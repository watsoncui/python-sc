# 首席架构师深度审查报告（v0.1 → v0.2）

> 范围：架构 + 性能 + 防御性编程；对原型代码进行问题定位、给出 Before/After
> 对比、阐释设计模式原理；所有改造都已落到代码并配套了单元测试。

---

## 一、架构审查

### A1. 双模态健壮性：API 路由独立性与状态竞争

**问题诊断**

v0.1 的 `AIOrchestrator._pick(mode)` 在 provider 缺失时仅抛 `RuntimeError`；
更严重的是 **同一个 `AIOrchestrator` 实例同时持有 `_server` 与 `_local`**——
这本身没问题，但 v0.1 没有任何隔离机制：

* 上层路由可以在一次请求里同时（错误地）走 SERVER 与 LOCAL，导致日志、
  token 计数错配；
* `bind_request_context` 在多个并发请求里共享一个 `ContextVar`，但 v0.1 根
  本没有 binding/unbinding 配对，导致跨请求字段串流；
* 路由层任何未捕获异常都会原样冒泡为 HTTP 500，**student key 失效与
  teacher key 失效完全无法区分**。

**Before / After**

```python
# Before — v0.1 (orchestrator.py)
def _pick(self, mode: ProviderMode) -> BaseLLM:
    if mode is ProviderMode.SERVER:
        if self._server is None:
            raise RuntimeError("Server provider is not configured on this build.")
        return self._server
    if mode is ProviderMode.LOCAL:
        if self._local is None:
            raise RuntimeError("Local provider is not configured on this build.")
        return self._local
    raise ValueError(f"Unknown provider mode: {mode}")

async def audit_vectorize(self, req: AuditRequest) -> AuditResponse:
    provider = self._pick(req.provider)
    tags = [f"week:{req.course_week}"] if req.course_week else []
    context, _hits = self._retrieve_context(tags=tags, query=req.code[:512])
    prompt = PromptLibrary.vectorize_audit(...)
    result = await provider.acomplete(prompt, ...)        # ← 任何异常裸抛
    return self._parse_audit_response(result.message.content, usage=result.usage)
```

```python
# After — v0.2 (orchestrator.py)
def _pick(self, mode: ProviderMode) -> BaseLLM:
    if mode is ProviderMode.SERVER:
        if self._server is None:
            raise LLMConfigurationError(
                "Server provider is not configured on this build. "
                "Set SCICOMP_SERVER_API_KEY or call with provider='local'.")
        return self._server
    if mode is ProviderMode.LOCAL:
        if self._local is None:
            raise LLMConfigurationError(
                "Local provider is not configured on this build. "
                "Switch the app to desktop mode or use provider='server'.")
        return self._local
    raise LLMConfigurationError(f"Unknown provider mode: {mode!r}")

async def audit_vectorize(self, req: AuditRequest) -> AuditResponse:
    async with self._scope(provider=req.provider.value, op="audit_vectorize") as ctx:
        provider = self._pick(req.provider)               # 提前路由，避免泄漏
        ...
        result = await self._call_with_alerts(             # 统一兜底
            provider.acomplete(prompt, ...)
        )
        ctx["usage"] = result.usage.model_dump()
        return self._parse_audit_response(result.message.content, usage=result.usage)
```

* `LLMConfigurationError` 是 **类型化异常层次** 的成员，路由层经
  `install_exception_handlers` 统一映射为 HTTP 400 并附带学生可读的提示；
* `_scope(...)` 是一个 `async with` 上下文（**Scoped Context 模式**）：
  入口注入 `request_id` 等到 `ContextVar`，退出时显式 `unbind`，杜绝跨请求字段串流；
* `_call_with_alerts` 把所有 provider 调用包在一个保险丝里：未知异常被
  归一化为 `LLMResponseError`，可重试的 5xx 自动触发 `AlertSink.emit`。

**关键证据**：`test_orchestrator_routes_to_correct_provider` 用一对 scripted
provider 验证「SERVER 模式下 LOCAL provider 的 `.calls` 列表必须为空」——
确保 student key 永不在 server-mode 请求里被错误地拉出来。

```python
# tests/test_errors_and_retries.py
async def test_orchestrator_routes_to_correct_provider():
    server = _ScriptedProvider([_ok_result('{"summary":"ok","suggestions":[]}')])
    local = _ScriptedProvider([_ok_result('{"summary":"BAD","suggestions":[]}')])
    orch = AIOrchestrator(server=server, local=local)
    await orch.audit_vectorize(AuditRequest(code="...", provider=ProviderMode.SERVER))
    assert len(server.calls) == 1
    assert local.calls == []        # critical
```

**设计模式**：Strategy（provider 抽象）+ Scoped Context（请求隔离）+
Typed Exception Hierarchy（错误路由）。

---

### A2. 解耦程度：前后端协议的 Open/Closed 违例

**问题诊断**

v0.1 的 `TDARequest.pipeline: Literal["vietoris_rips","alpha","cubical","mapper"]`
是个 *封闭枚举*：每加一个 TDA 算子需要同时修改 Pydantic Literal、
`TDAEngine.compute` 的 if/elif 级联、FastAPI 路由文档、以及前端下拉项。
这是 **开闭原则（Open/Closed Principle）的典型违例**。

**Before / After**

```python
# Before — common/compute/tda.py (v0.1)
if self.is_available and req.pipeline in ("vietoris_rips", "alpha"):
    diagrams = self._giotto_persistence(X, req)
else:
    if not self.is_available:
        warnings.append("giotto-tda not installed; using NumPy fallback (approximate, H0 only).")
    diagrams = self._numpy_fallback(X, req)
```

```python
# After — common/compute/operators.py (v0.2)
class Operator(abc.ABC):
    operator_id: ClassVar[str]
    @abc.abstractmethod
    def descriptor(self) -> OperatorDescriptor: ...
    @abc.abstractmethod
    def run(self, points, params: dict[str, Any]): ...

# Registration is one line per operator:
register_operator(_GiottoVietorisRips())
register_operator(_GiottoAlpha())
register_operator(_NumpyMST())

# Engine looks up by string id; no if/else cascade:
op = get_operator(req.operator or req.pipeline)
result = op.run(X, params)
```

* 协议层新增 `operator: str | None` + `params: dict[str, Any]`（仍保留旧
  `pipeline` 字段做向后兼容）；
* 新增 `GET /tda/operators` 端点：返回每个 operator 的
  `OperatorDescriptor`（id + title + 参数 JSON Schema + 输出 homology 维度），
  **前端据此动态渲染参数表单**，再也无需硬编码 dropdown；
* 测试 `test_registry_pickup_new_operator` 通过定义一个最小 `_FakeOp` 并
  `register_operator(...)` 后立刻调用 `/tda/pipeline` 验证：完整链路不
  需要修改任何注册表/路由/Pydantic 代码。

**设计模式**：Strategy + Registry（Plugin Pattern）。每个 operator 是一
个独立可替换的策略，注册表是它们的全局映射；前端通过 self-describing
schema 反射地拼装 UI——是大多数现代低代码 / 插件化系统采用的标准做法。

---

### A3. 并发安全：NumPy / Giotto-tda 阻塞事件循环

**问题诊断**

`TDAEngine.compute` 与 `Sandbox.run` 都是 **同步 CPU-bound** 函数，但
v0.1 在 `async def pipeline(...)` 与 `async def run(...)` 里直接同步调
用：FastAPI 的事件循环线程会被阻塞数百毫秒到数秒不等，期间所有其它
请求（包括 `/healthz`）排队等待。在 8 核机器上 1 个学生跑 `pipeline`
直接拖垮全班的 UI 心跳。

**Before / After**

```python
# Before — server/routers/tda.py (v0.1)
@router.post("/pipeline", response_model=TDAResponse)
async def pipeline(req, engine = Depends(tda_dep)):
    return engine.compute(req)       # ← 直接在事件循环里跑 NumPy + giotto-tda
```

```python
# After — server/routers/tda.py (v0.2)
@router.post("/pipeline", response_model=TDAResponse)
async def pipeline(req, engine = Depends(tda_dep)):
    return await asyncio.to_thread(engine.compute, req)  # 卸载到 worker 线程
```

同样的改造应用于 `server/routers/compute.py:run`。

**为什么用 `asyncio.to_thread` 而不是 `ProcessPoolExecutor`？**

| 维度 | 线程池 | 进程池 |
|---|---|---|
| 适用 GIL-释放 / native code | ✅ NumPy/SciPy 大部分耗时在 BLAS / C 扩展里释放 GIL | ✅ |
| 序列化开销 | 0 | 大（点云 ndarray 需要 pickle） |
| 启动延迟 | 微秒 | 数十毫秒到几百毫秒 |
| 故障隔离 | 一个线程崩溃可能影响主进程 | 子进程崩溃可被 supervisor 回收 |

教学场景中点云规模通常 ≤ 1e4 点，NumPy/scipy/giotto 在内部已经释放
GIL，**线程池是当前最优解**；若未来要支撑 1e6 点 + 多 GPU，再切到
`concurrent.futures.ProcessPoolExecutor` 并把 ndarray 通过 `shared_memory`
传递。该切换是单点修改（`asyncio.to_thread` → 一个 helper 函数），架构
不变。

**进一步硬化（已落地）**：Sandbox 超时机制现在感知线程身份——

```python
# common/compute/sandbox.py
in_main = threading.current_thread() is threading.main_thread()
use_signal = hasattr(signal, "SIGALRM") and in_main
if use_signal:
    signal.signal(signal.SIGALRM, _alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, self.timeout_sec)
else:
    # FastAPI worker threads / Windows: deliver async exception via the
    # CPython C API. Cleared in finally{} to avoid spurious propagation.
    timer = threading.Timer(
        self.timeout_sec,
        lambda: ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(threading.get_ident()),
            ctypes.py_object(_Timeout),
        ),
    )
```

—— v0.1 在工作线程里直接 `signal.signal` 报错 `ValueError: signal only works in
main thread`，新版本通过 `PyThreadState_SetAsyncExc` 实现线程级超时，
和 IPython 的 `interruptiblesleep` 同款做法。

---

## 二、性能审计

### B1. 残留的 Python 循环（向量化收益）

**问题诊断**

v0.1 的 `_betti_curves` 内层是 Python `for p in pts: counts += ...`，
即 `O(n_dim × n_pts × n_bins)` 个 Python-level 迭代；
`_numpy_fallback` 用 `rows: list[list[float]]` 逐行 append 后再 `np.asarray`。

**Before / After**

```python
# Before — common/compute/tda.py (v0.1) — Python loop per persistence point
for dim, pts in sorted(by_dim.items()):
    counts = np.zeros_like(grid, dtype=int)
    for p in pts:
        counts += ((grid >= p.birth) & (grid < p.death)).astype(int)
    out.append(BettiCurve(dimension=dim, filtration=grid.tolist(), values=counts.tolist()))
```

```python
# After — common/compute/tda.py (v0.2) — one broadcast per dimension
for d in np.unique(dims):
    sel = dims == d
    b = births[sel][None, :]                 # (1, k)
    e = deaths[sel][None, :]
    g = grid[:, None]                        # (n_bins, 1)
    counts = ((g >= b) & (g < e)).sum(axis=1).astype(np.int64)
    out.append(BettiCurve(
        dimension=int(d),
        filtration=grid.tolist(),
        values=counts.tolist(),
    ))
```

* **复杂度**：从 `O(n_dim × n_pts × n_bins)` 个 Python 解释器迭代降至
  `O(1)` 个 ndarray 调用（C 层一次性完成 `n_bins × k` 比较）；
* **正确性回归**：`test_vectorised_betti_matches_loop_implementation` 把
  随机生成的 40 个特征点喂给「向量化」和「reference loop」两版本，断言
  逐维度的 counts list **逐元素相等**。

同理 `_mst_h0` 把 `rows: list[list[float]]` 的 Python list 累积换成单次
`np.column_stack` + `np.vstack`，避免 O(n) 次 list append。

**设计模式**：Vectorization Refactor 的本质是把 *Iteration Strategy* 从
解释器层下推到 BLAS / NumPy C 层；同时通过 broadcasting 把高维循环折成单
次张量运算。

---

### B2. 内存拷贝

**问题诊断 + 改进**

1. `np.asarray(req.data, dtype=np.float64)`：从 Python `list[list[float]]`
   构造 ndarray **必然要发生一次拷贝**（无法零拷贝），不可避免。
2. v0.1 后续 `X.astype(float).tolist()` 在 preview 路径里再次复制一份
   `float64 → Python float`，浪费两倍内存。
3. `np.where(np.isfinite(diagrams[:, 1]), diagrams[:, 1], 0.0)` 创建中
   间数组——v0.2 改为单次布尔索引：

```python
# After
finite_mask = np.isfinite(births) & np.isfinite(deaths)
births, deaths, dims = births[finite_mask], deaths[finite_mask], dims[finite_mask]
```

4. `_suggest_max_edge` 在估算 max_edge_length 时把 `pdist` 输入限制在
   1024 个采样点，避免 O(n²) 的距离矩阵在大点云下爆内存。

5. `_sanitize_point_cloud` 末尾使用 `np.ascontiguousarray` 让后续 BLAS
   不需要再做 stride 重排（如果输入是 column-major slice）。

进一步可走的路（**未落地**，留作后续）：将 `tolist()` 换为 `orjson` 直接
序列化 ndarray；或者大点云走 Apache Arrow over HTTP（前端用
`apache-arrow-js` 反序列化）。

---

### B3. 噪声 TDA 的数值稳定性

**问题诊断**

v0.1 的请求协议没有 `min_persistence`、没有标准化选项，`max_edge_length`
是静态默认 1.0——遇到学生上传的高斯噪声或者尺度差几个数量级的真实
数据时，要么持久图被淹没在短噪声点里，要么 H1/H2 特征根本进不了
filtration。

**Before / After**

```python
# Before — protocols/tda_payload.py (v0.1)
class TDARequest(BaseModel):
    pipeline: Literal["vietoris_rips","alpha","cubical","mapper"] = "vietoris_rips"
    max_edge_length: float = Field(1.0, gt=0.0)
    # ...无 min_persistence / standardize / auto_max_edge_length
```

```python
# After — protocols/tda_payload.py (v0.2)
class TDARequest(BaseModel):
    operator: str | None = None                     # plugin id
    params: dict[str, Any] = Field(default_factory=dict)
    max_edge_length: float = Field(1.0, ge=0.0)
    auto_max_edge_length: bool = False              # 数据驱动估计 cloud 直径
    standardize: bool = False                       # z-score 归一化
    min_persistence: float | None = None            # 噪声特征过滤阈值
```

实现侧 `_sanitize_point_cloud` + `_suggest_max_edge` 联动：

* 读取数据后第一步用 `np.isfinite(X).all(axis=1)` 把 NaN/Inf 整行丢弃并附 warning；
* 标准化使用 `sigma = np.where(sigma < 1e-12, 1.0, sigma)` 防止常量列除零；
* `_suggest_max_edge` 采样后取 **第 90 百分位** pairwise 距离（中位数 +
  长尾），同时下界保护 `max(., 1e-6)` 避免 0；
* `min_persistence > 0` 时在持久图层面做向量化布尔过滤，并把丢弃数
  写入 warnings——既诚实又可解释。

**测试用例**：

* `test_tda_drops_nonfinite_input_rows` 喂入含 `nan`/`inf` 的 4 点云，
  断言出现 “Dropped X non-finite rows” 警告；
* `test_tda_min_persistence_filters_noise` 对比无过滤与 `min_persistence=2.0`
  的特征数；
* `test_tda_auto_max_edge_length_kicks_in` 喂入跨度 1000 的点云，断言
  `auto_max_edge_length=True` 时持久图中能看到 MST 边。

**设计原则**：「Honest Numerics」——对所有降级 / 过滤 / 兜底都在
`warnings` 里给出可观察的信号，UI 据此做黄条提示，让学生明白「为什么
看不到 H1」而不是误以为算法错了。

---

## 三、防御性编程补强

### C1. 异常捕获链路（超时 / Rate Limit / NaN）

**问题诊断**

v0.1 的 provider 只 `resp.raise_for_status()` 后让 httpx 异常裸抛——
路由层 `except (PermissionError, RuntimeError)` 是个语义模糊的捕获，
覆盖率不全（不接 `httpx.TimeoutException`、`httpx.HTTPStatusError`），
且无法区分 401 vs 429 vs 5xx。

**Before / After**

```python
# Before — common/ai/server_provider.py (v0.1)
resp = await self._client.post(..., headers=headers)
resp.raise_for_status()        # 任何 4xx/5xx 都是 httpx.HTTPStatusError
data = resp.json()
choice = data["choices"][0]["message"]   # KeyError / IndexError 裸抛
```

```python
# After — common/ai/server_provider.py (v0.2)
try:
    resp = await self._client.post(..., headers=headers)
except httpx.TimeoutException as exc:
    raise LLMTimeoutError(...) from exc
except httpx.HTTPError as exc:
    raise LLMNetworkError(...) from exc

if resp.status_code in (401, 403):  raise LLMAuthError(...)
if resp.status_code == 429:         raise LLMRateLimitError(
                                        retry_after=_parse_retry_after(...))
if resp.status_code >= 500:         raise LLMUpstreamError(...)
if resp.status_code >= 400:         raise LLMResponseError(...)

try:
    data = resp.json()
    choice = data["choices"][0]["message"]
    content, role = choice["content"], choice.get("role", "assistant")
except (KeyError, IndexError, ValueError) as exc:
    raise LLMResponseError("Malformed completion payload.") from exc
```

外层 `_with_retries` 用 **指数退避 + jitter** 处理可重试错误，并按
`Retry-After` 报头精确等待：

```python
# common/ai/server_provider.py (v0.2)
async def _with_retries(self, payload, *, model_name):
    delay = 0.5
    for attempt in range(1, self._max_retries + 1):
        try:
            return await self._call_once(payload, model_name=model_name)
        except LLMRateLimitError as exc:
            wait = exc.retry_after if exc.retry_after is not None else delay
            await asyncio.sleep(max(0.0, wait) + random.uniform(0, 0.25))
        except (LLMTimeoutError, LLMNetworkError, LLMUpstreamError):
            if attempt == self._max_retries: raise
            await asyncio.sleep(delay + random.uniform(0, 0.25))
            delay = min(delay * 2, 8.0)
```

**Auth 错误绝不重试**：`test_server_provider_does_not_retry_auth_errors`
断言一次失败即可终止——错误密钥 retry 100 次也不会变好。

**路由层映射**（centralised, `server/error_handlers.py`）：

```python
@app.exception_handler(LLMError)
async def _llm_error(request, exc: LLMError):
    body = {"detail": str(exc), "error_type": type(exc).__name__,
            "retryable": exc.retryable}
    headers = {}
    if isinstance(exc, LLMRateLimitError) and exc.retry_after is not None:
        body["retry_after"] = exc.retry_after
        headers["Retry-After"] = str(int(exc.retry_after))
    return JSONResponse(status_code=exc.http_status, content=body, headers=headers)
```

`LLMError.http_status` 由子类静态声明（429/401/504/502/400），HTTP 状态
码不再散落在路由层。**设计模式**：Typed Exception Hierarchy 的标准应用。

**NaN/Inf 在 sandbox 出口处统一拦截**：

```python
# common/compute/sandbox.py (v0.2)
def _scrub_nonfinite(payload, *, prefix=""):
    """Walk a nested dict/list, replacing NaN/Inf with None.
    Returns (scrubbed, [dotted-keys-that-were-replaced])."""
```

之后 `SandboxResult.nonfinite_keys` 透传到 `ComputeResponse.nonfinite_keys`，
UI 据此给学生贴黄条「`mean` 被替换为 null（NaN）」。

测试：`test_sandbox_replaces_nan_with_none` 验证 NaN/Inf 标量与嵌套列表
都被替换并被报告。

---

### C2. 日志审计 + Slack 告警预留

**v0.1 状态**：`logging.getLogger(__name__)` 散落各处，无结构化字段；告警接口完全没有。

**v0.2 新增 `common/observability/`**：

```text
common/observability/
├── logging.py    # configure_logging / get_logger / bind_request_context
└── alerts.py     # AlertSink (Strategy) + NullAlertSink + SlackWebhookAlertSink
```

* **结构化日志**：`bind_request_context(request_id=..., provider=..., op=...)`
  把字段写入 `contextvars.ContextVar`，`_ContextFilter` 在每条 LogRecord 上
  注入这些字段；`json_lines=True` 时改用单行 JSON 格式，可直接被
  Loki/Datadog 摄取。
* **请求 ID 中间件**：`RequestContextMiddleware` 把 `X-Request-Id`
  header（缺失则生成）贯穿日志、响应头、orchestrator scope，便于跨服务
  追踪。
* **Slack 告警预留**：`SlackWebhookAlertSink` 通过 `asyncio.to_thread` +
  `urllib.request` 异步投递（**永不阻塞请求**），且 `try/except` 吞掉所有
  失败——告警绝对不能反过来打挂业务。沟通失败时 `logging.WARNING`。
* **接入点**：`AIOrchestrator._Scope.__aexit__` 在 LLM 调用失败时按错误
  类型决定 `severity=error|warning` 后发 alert。

```python
# common/ai/orchestrator.py (v0.2)
async def __aexit__(self, exc_type, exc, tb) -> bool:
    if exc is not None and isinstance(exc, LLMError):
        severity = "error" if isinstance(exc, LLMUpstreamError) else "warning"
        await get_alert_sink().emit(
            AlertEvent(severity=severity,
                       title=f"LLM call failed: {type(exc).__name__}",
                       body=str(exc),
                       fields={..., "retryable": exc.retryable}))
    return False
```

**测试**：

* `test_slack_sink_skips_when_unconfigured` —— 没设 webhook 时静默；
* `test_slack_sink_swallows_delivery_errors` —— `_post` 主动抛错时
  `emit` 不会冒泡；
* `test_request_context_attaches_fields_to_log_records` —— `caplog`
  能拿到 `record.request_id == "rid-1"`。

**设计模式**：Strategy（`AlertSink` 一接口三实现）+ Bound Context（
`ContextVar` 是 Python 异步世界的「请求局部存储」标准做法，与 Java MDC
对应）。

---

### C3. 测试覆盖：边缘案例矩阵

| 模块 | 边缘案例 | 测试 |
|---|---|---|
| Orchestrator | LOCAL 未配置时被请求 → LLMConfigurationError | `test_orchestrator_refuses_local_when_not_configured` |
| Orchestrator | SERVER 未配置时被请求 | `test_orchestrator_refuses_server_when_not_configured` |
| Orchestrator | SERVER 模式下 LOCAL provider 必须零调用 | `test_orchestrator_routes_to_correct_provider` |
| ServerProvider | 上游 429 → 重试后成功 | `test_server_provider_retries_rate_limit_then_succeeds` |
| ServerProvider | 持续 5xx → 达 max_retries 后抛 | `test_server_provider_gives_up_after_max_retries` |
| ServerProvider | 401/403 不重试 | `test_server_provider_does_not_retry_auth_errors` |
| ServerProvider | httpx.TimeoutException → LLMTimeoutError | `test_server_provider_maps_httpx_timeout` |
| ServerProvider | httpx.ConnectError → LLMNetworkError | `test_server_provider_maps_httpx_network_error` |
| Audit parser | 单行 suggestion 坏掉，整体不挂 | `test_audit_parser_drops_malformed_suggestion_rows` |
| Audit parser | 空字符串输入 | `test_audit_parser_handles_empty_content` |
| Audit parser | 围栏 ```json | `test_audit_parser_strips_code_fences` |
| TDA | 注册新算子立即可用 | `test_registry_pickup_new_operator` |
| TDA | 未知 operator_id → ValueError | `test_registry_unknown_operator_raises` |
| TDA | 向量化 Betti 与 loop reference 对齐 | `test_vectorised_betti_matches_loop_implementation` |
| TDA | 输入含 NaN/Inf 行 | `test_tda_drops_nonfinite_input_rows` |
| TDA | min_persistence 过滤噪声 | `test_tda_min_persistence_filters_noise` |
| TDA | 标准化产生 warning | `test_tda_standardize_emits_warning` |
| TDA | auto_max_edge_length 工作 | `test_tda_auto_max_edge_length_kicks_in` |
| TDA | 空输入 / 单点 | `test_tda_handles_empty_input_gracefully` / `test_tda_single_point_does_not_crash` |
| Sandbox | NaN/Inf 标量与嵌套列表均替换为 null | `test_sandbox_replaces_nan_with_none` |
| Alerts | NullSink、Slack 未配置、Slack 投递失败 | `test_null_sink_emits_silently` / `test_slack_sink_skips_when_unconfigured` / `test_slack_sink_swallows_delivery_errors` |
| Logging | 请求字段注入 LogRecord | `test_request_context_attaches_fields_to_log_records` |

共 **41 个** pytest 用例，新增覆盖面集中在「v0.1 的硬编码假设」与
「真实网络异常」上。

---

## 四、改造收口

| 维度 | v0.1 | v0.2 |
|---|---|---|
| Provider 错误信号 | `RuntimeError` / 裸 httpx | 7 类 `LLMError` 子类 → HTTP 自动映射 |
| 重试策略 | 无 | 指数退避 + jitter + `Retry-After` |
| TDA 扩展性 | Literal 枚举 + if/else | Operator Registry + `params: dict` |
| 事件循环 | CPU 任务同步阻塞 | `asyncio.to_thread` 卸载 |
| Sandbox 超时 | 主线程外报错 | 主线程 SIGALRM + worker 线程 ctypes 异步异常 |
| Betti 曲线 | 双层 Python 循环 | 单次 broadcasting |
| 噪声鲁棒 | 无 | NaN/Inf 过滤、z-score、auto max-edge、`min_persistence` |
| 日志 | 散落、平铺 | `ContextVar` 注入 + 单行 JSON 可选 |
| 告警 | 无 | `AlertSink`（Slack/Null/可扩展） |
| 测试数量 | 17 | 41（+24） |

> 改造贯穿三层设计模式：**Strategy**（Provider/Operator/AlertSink）、
> **Registry**（Operator）、**Typed Exception Hierarchy**（LLMError 树）、
> **Scoped Context**（`_Scope` + `ContextVar`）。它们共同把「业务路径」
> 与「横切关注点」彻底解耦，让后续添加（新算子 / 新告警通道 / 新错误类型 /
> 新 provider）都变成「单点修改 + 注册」，符合 Open/Closed 与
> Single-Responsibility 原则。
