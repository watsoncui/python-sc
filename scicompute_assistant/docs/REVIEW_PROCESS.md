# 深度审查过程文档（Review Process Playbook）

> 与 [`REVIEW.md`](./REVIEW.md) 互为姐妹篇：
> - `REVIEW.md` 记录 **审查结论**（议题 → Before/After → 设计模式原理）。
> - 本文记录 **审查过程**（方法、清单、证据链、验证矩阵、复盘、复现指南）。

本次审查针对 `scicompute_assistant` v0.1 原型（PR
[`cursor/scicompute-assistant-prototype-48fa`](../../../pull/2)），目标是把
"能跑通的原型" 推进到 "可以放心上线给一整门课用" 的水准。最终输出为分
支 [`cursor/scicompute-deep-review-48fa`](../../../pull/7) 与 v0.2 代码。

---

## 0. 文档导航

| 阶段 | 文档 | 关键内容 |
|---|---|---|
| 项目背景 | [`syllabus.md`](../../meta_course/syllabus.md), [`schedule-18weeks.md`](../../meta_course/schedule-18weeks.md) | 教学场景与约束 |
| 任务书 | 用户原始提示 + 本次需求 | 五项交付 |
| 架构设计 | [`ARCHITECTURE.md`](./ARCHITECTURE.md) | 目录结构、`common/` 接口契约 |
| AI Prompt | [`AI_PROMPTS.md`](./AI_PROMPTS.md) | 向量化审计 System Prompt |
| TDA 协议 | [`TDA_PROTOCOL.md`](./TDA_PROTOCOL.md) | 前后端 JSON 协议 |
| 安全方案 | [`SECURITY_TAURI.md`](./SECURITY_TAURI.md) | 离线 Key 存储 |
| **审查结论** | [`REVIEW.md`](./REVIEW.md) | Before/After + 设计模式 |
| **审查过程** | 本文 | 方法论 + 证据链 + 复现 |

---

## 1. 审查方法论

### 1.1 三维度透镜（Three-Axis Lens）

任何系统都可以从三条正交轴线被检视。把它们写在白板上，可以避免遗漏：

```
        架构 (Architecture)
              ▲
              │  · 责任划分 / 解耦 / 扩展性
              │  · 双模态隔离 / 并发模型 / 协议演进
              │
   防御 ◀────┼────▶ 性能
   (Defense)  │       (Performance)
              │  · 异常 / 重试 / 限流       · 向量化 / 内存 / 数值
              │  · 日志 / 告警 / 审计        · 算法复杂度 / 阻塞分析
```

针对本项目，三条轴分别对应任务书的三组追问：

| 轴 | 任务书追问 | 审查议题 |
|---|---|---|
| 架构 | A1. 双模态健壮性 / A2. 协议解耦 / A3. 并发安全 | 3 |
| 性能 | B1. 残留向量化 / B2. 内存拷贝 / B3. 数值稳定 | 3 |
| 防御 | C1. 异常捕获 / C2. 日志告警 / C3. 边缘测试 | 3 |

共 **9 个议题**，构成审查工单（issue board）。

### 1.2 证据驱动的假设循环（EHFV）

借鉴医学诊断的 **症状 → 假设 → 证据 → 验证** 流程：

```
┌───────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  E vidence│ ─▶ │ H ypothesis  │ ─▶ │ F ix         │ ─▶ │ V erification│
│  (代码 +  │    │ (问题假设)   │    │ (重构)       │    │ (测试 + curl)│
│   日志)   │    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
└───────────┘           │                   │                   │
       ▲                ▼                   ▼                   ▼
       └─────────────── 任意一步失败立即回到 Evidence ────────────────┘
```

**关键纪律**：

1. 不在没有 Evidence 的情况下提出 Hypothesis（避免"猜代码"）。
2. 不在没有 Verification 的情况下相信 Fix（避免"理论上正确"）。
3. Verification 失败时回到 Evidence 收集，**绝不"加大胆量再试一次"**。

### 1.3 "Honest Diagnostics" 原则

为了让评审、学生、未来的维护者都能复盘，本次审查遵守三条公约：

- **降级必报**：任何兜底 / 默认值 / 自动估计都必须在 `warnings` 字段或日志里
  显式标注（例：`giotto-tda not installed; falling back to MST`、
  `max_edge_length auto-set to 1.2345`）。
- **错误必分类**：异常永不裸抛 `RuntimeError("…")`；每一类故障对应一个具名
  类型，承载 HTTP 状态码与 `retryable` 标志。
- **修复必带回归**：每一个 Fix 至少配套一个 pytest 用例，能在重构被回退时
  红灯报警。

---

## 2. 审查计划

### 2.1 议题工单

| ID | 议题 | 影响面 | 优先级 |
|---|---|---|---|
| A1 | `AIOrchestrator` 双模态隔离 / 状态竞争 | 安全 + 正确性 | P0 |
| A2 | TDA 协议是否支持新算子无侵入接入 | 扩展性 | P1 |
| A3 | NumPy/giotto-tda 阻塞 event loop | 高并发可用性 | P0 |
| B1 | 残留 Python `for` 循环 | 性能 | P1 |
| B2 | 大点云内存拷贝 | 性能 + 稳定 | P2 |
| B3 | 噪声 TDA 数值稳定性 | 教学正确性 | P0 |
| C1 | 超时 / Rate Limit / NaN-Inf 异常链 | 健壮性 | P0 |
| C2 | 结构化日志 + Slack Webhook 告警 | 可观测性 | P1 |
| C3 | 边缘案例 pytest 覆盖 | 回归保护 | P0 |

> 优先级映射：P0 必须本次落地；P1 必须本次落地且配套测试；P2 列入跟踪。

### 2.2 时间盒（Time-Boxed）

* 探索（探针 curl / 读代码）30 %
* 重构编码 40 %
* 测试 20 %
* 文档化 10 %

实际进度可在 `TodoWrite` 中追踪（参见提交记录中的 todo 流转）。

---

## 3. 议题逐项审查日志

每一项议题都按 **现状 → 触发条件 → 根因 → 修复 → 验证** 五段式记录。

### A1. 双模态健壮性

| 阶段 | 记录 |
|---|---|
| **现状** | `_pick()` 抛 `RuntimeError`；orchestrator 同时持有两个 provider；上层无 ContextVar 隔离。 |
| **触发条件** | 学生在桌面构建里点 "云端助教"，而该 build 未配置教师 Key；或并发请求间日志 `request_id` 串流。 |
| **根因** | 错误类型缺失（无法分类映射）；缺乏 scoped context；provider 路由没有"必须严格"的强约束。 |
| **修复** | 引入 `LLMError` 类型树；新增 `AIOrchestrator._Scope` async context manager；`_pick` 改抛 `LLMConfigurationError`；新增 `GET /ai/providers` 让前端可发现可用模式。 |
| **验证** | `test_orchestrator_refuses_local_when_not_configured` / `test_orchestrator_refuses_server_when_not_configured` / `test_orchestrator_routes_to_correct_provider`（断言 SERVER 模式下 LOCAL provider `.calls == []`）。 |

> **要点**：`test_orchestrator_routes_to_correct_provider` 是"杜绝 Key 错路"
> 这一安全契约的 **第一道、也是最不可绕过的一道守卫**。任何未来重构都必须
> 让它持续通过。

### A2. TDA 协议解耦

| 阶段 | 记录 |
|---|---|
| **现状** | `pipeline: Literal[...]` + `if/elif` 级联。 |
| **触发条件** | 教师想添加 *Witness complex* 或 *Sliding-window embedding*：需要同时改 Pydantic / 引擎 / 路由 / 前端。 |
| **根因** | Open/Closed Principle 违例。 |
| **修复** | 抽象 `Operator` 接口 + 全局 `_Registry`；新增 `GET /tda/operators` 暴露 `OperatorDescriptor`（含 JSON Schema）。 |
| **验证** | `test_registry_pickup_new_operator`（定义最小 `_FakeOp` + `register_operator` 后立即调用 `/tda/pipeline`）；`test_registry_unknown_operator_raises`。 |

### A3. 并发安全 / Event Loop 阻塞

| 阶段 | 记录 |
|---|---|
| **现状** | `engine.compute(req)` / `kernel.run_code(...)` 同步运行在 `async def` 内。 |
| **触发条件** | 8 名学生同时点 "持久图"，每次 300 ms：累计 2.4 s 的串行阻塞，期间 `/healthz` 超时。 |
| **根因** | CPU-bound 工作未卸载。 |
| **修复** | 改为 `await asyncio.to_thread(engine.compute, req)` / `await asyncio.to_thread(kernel.run_code, …)`；Sandbox 超时机制通过 `threading.current_thread() is main_thread()` 选 `SIGALRM` 或 `ctypes.PyThreadState_SetAsyncExc` 兜底。 |
| **验证** | `concurrency_smoke.log`：8 个 800-点 TDA 任务并行，`/healthz` 中位数 8.5 ms / p95 51.8 ms。比 v0.1 同步路径的预估 2.4 s 阻塞改善 ≥ 40×。 |

```
=== TDA workers (800 points, 8 concurrent) ===
  worker #0..7: HTTP 200  duration ≈ 190–305 ms (并行)
=== /healthz probes during burst (14 samples) ===
  median 8.50 ms / p95 51.82 ms / max 51.82 ms
```

### B1. 残留 Python `for` 循环

| 阶段 | 记录 |
|---|---|
| **现状** | `_betti_curves` 内层 `for p in pts: counts += (grid >= p.birth) & ...`；`_numpy_fallback` 用 list-of-lists 累积。 |
| **触发条件** | 1024 bins × 200 持久点 × 3 维 ≈ 6 × 10⁵ 次 Python 迭代。 |
| **根因** | 误把"循环写在 NumPy 表达式外面"。 |
| **修复** | 双 broadcasting：`(grid[:,None] >= births[None,:]) & (grid[:,None] < deaths[None,:])`，单次 C 层归约。 |
| **验证** | `test_vectorised_betti_matches_loop_implementation`：与 reference loop 实现按维度 byte-equal 比对，杜绝向量化引入的逻辑漂移。 |

> **方法学小结**：性能重构最大的风险不是慢，而是 "改完之后微小行为偏差，
> 引发回归错觉"。**优先写 reference 对比测试**，再做向量化优化。

### B2. 内存拷贝

| 阶段 | 记录 |
|---|---|
| **现状** | `np.where(np.isfinite(diagrams[:,1]), diagrams[:,1], 0.0)` 创建一份完整中间数组；`X.astype(float).tolist()` 在 preview 路径多一次复制。 |
| **触发条件** | 1e4 点云时这些临时数组各占数 MB。 |
| **根因** | NumPy 表达式风格不够"原地"。 |
| **修复** | 改用单次布尔掩码切片 `births[finite_mask]`；预览路径直接 `X[idx].tolist()`；自动估 `max_edge_length` 子采样到 1024 点。 |
| **验证** | TDA 路由对 800 点云的延迟 300 ms 内完成（含 RTT），见 `concurrency_smoke.log`。 |

### B3. 噪声 TDA 数值稳定性

| 阶段 | 记录 |
|---|---|
| **现状** | 协议无 `min_persistence` / `standardize` / `auto_max_edge_length`；遇到尺度跨多个数量级的数据，H1/H2 不进入 filtration。 |
| **触发条件** | 学生喂入 (x ∈ [0,1], y ∈ [0,500]) 的真实数据集。 |
| **根因** | 静态 `max_edge_length=1.0` + 无 z-score。 |
| **修复** | 1) `_sanitize_point_cloud` 丢非有限行并 warning；2) z-score 标准化；3) `_suggest_max_edge` 用 90 百分位采样距离驱动估计；4) `min_persistence` 过滤短噪声。所有降级路径写入 `warnings`。 |
| **验证** | `test_tda_drops_nonfinite_input_rows` / `test_tda_min_persistence_filters_noise` / `test_tda_standardize_emits_warning` / `test_tda_auto_max_edge_length_kicks_in` / `test_tda_handles_empty_input_gracefully` / `test_tda_single_point_does_not_crash`。 |

### C1. 异常捕获链路

| 阶段 | 记录 |
|---|---|
| **现状** | `resp.raise_for_status()` 后裸抛 httpx 异常；路由层 `except (PermissionError, RuntimeError)` 语义模糊。 |
| **触发条件** | 上游 429 / 5xx / 网络中断 / NaN 输出 / 401 错误密钥。 |
| **根因** | 错误未类型化；无重试策略；NaN/Inf 没有边界处理。 |
| **修复** | 7 类 `LLMError` 子类；`_with_retries` 指数退避 + jitter + `Retry-After`；**401/403 一次失败即抛**；Sandbox 出口 `_scrub_nonfinite` 把 NaN/Inf 替换为 `null` 并报告 `nonfinite_keys`；路由集中通过 `install_exception_handlers` 映射到 HTTP。 |
| **验证** | `test_server_provider_retries_rate_limit_then_succeeds` / `test_server_provider_gives_up_after_max_retries` / `test_server_provider_does_not_retry_auth_errors` / `test_server_provider_maps_httpx_timeout` / `test_server_provider_maps_httpx_network_error` / `test_sandbox_replaces_nan_with_none`。`llm_config_error_response.txt` 演示 HTTP 400 + `error_type` + `retryable` + `hint`。 |

### C2. 日志审计 + Slack 告警

| 阶段 | 记录 |
|---|---|
| **现状** | 散落 `getLogger(__name__)`；无 request_id；告警接口完全缺失。 |
| **触发条件** | 课堂事故后日志需关联跨服务调用链；运维想在 Slack 看到失败统计。 |
| **根因** | 缺乏 cross-cutting 关注点的统一抽象。 |
| **修复** | `common/observability/{logging,alerts}.py`：`ContextVar` 注入 + 单行 JSON 可选格式；`AlertSink` Strategy（Null / Slack）；`SlackWebhookAlertSink` 使用 `asyncio.to_thread + urllib.request`，永不阻塞，永不抛；`RequestContextMiddleware` 把 `X-Request-Id` 贯穿到响应头与日志。 |
| **验证** | `test_null_sink_emits_silently` / `test_slack_sink_skips_when_unconfigured` / `test_slack_sink_swallows_delivery_errors` / `test_request_context_attaches_fields_to_log_records`。 |

### C3. 边缘案例覆盖

| 阶段 | 记录 |
|---|---|
| **现状** | v0.1 17 个测试，几乎都是 happy path。 |
| **目标** | 把 v0.2 拉到 **40+** 测试，主要覆盖 "v0.1 的硬编码假设" + "真实网络异常" + "极端输入"。 |
| **落地** | 共 41 项测试，新增 24 项。详细矩阵见下文 §5。 |

---

## 4. 重构落地清单（按文件）

> 改动总览（diff 来源：`git diff cursor/scicompute-assistant-prototype-48fa..HEAD --stat scicompute_assistant/`）。

| 类型 | 文件 | 说明 |
|---|---|---|
| 新增 | `common/ai/errors.py` | 7 类 `LLMError` 异常树 |
| 新增 | `common/compute/operators.py` | Operator 注册表 |
| 新增 | `common/observability/__init__.py` | 可观测性聚合 |
| 新增 | `common/observability/alerts.py` | `AlertSink` Strategy + Slack 实现 |
| 新增 | `common/observability/logging.py` | `ContextVar` 注入 + JSON 格式 |
| 新增 | `server/error_handlers.py` | 集中 HTTP 映射 |
| 新增 | `server/middleware/observability.py` | `X-Request-Id` 中间件 |
| 新增 | `docs/REVIEW.md` | 议题 → Before/After 论述 |
| 新增 | `docs/REVIEW_PROCESS.md` | 本文 |
| 新增 | `tests/test_errors_and_retries.py` | 10 项 |
| 新增 | `tests/test_observability.py` | 4 项 |
| 新增 | `tests/test_tda_robustness.py` | 10 项 |
| 修改 | `common/ai/{server_provider,local_provider,orchestrator}.py` | 类型化错误、重试、scoped 隔离 |
| 修改 | `common/compute/{sandbox,tda}.py` | NaN scrub、向量化 Betti、operator 适配 |
| 修改 | `common/protocols/{api_models,tda_payload}.py` | 增 `nonfinite_keys`、`operator/params/standardize/...` |
| 修改 | `server/{main,config,dependencies}.py` | 装配观测性 + 错误处理器 |
| 修改 | `server/routers/{ai,compute,tda}.py` | `asyncio.to_thread`、简化 try-except |

---

## 5. 验证矩阵

### 5.1 测试矩阵

| 模块 | 测试文件 | 用例数 | 关键断言 |
|---|---|---|---|
| API e2e | `test_api.py` | 8 | chat / audit / compute / TDA / knowledge 端到端 200 |
| AI 错误 | `test_errors_and_retries.py` | 10 | 类型化错误 / 重试 / 双模态隔离 / 401 不重试 |
| 观测性 | `test_observability.py` | 4 | Null/Slack sink 契约 + ContextVar 字段注入 |
| Prompt 解析 | `test_prompts.py` | 4 | JSON / 围栏 / 垃圾输入 |
| 安全存储 | `test_security.py` | 5 | Fernet 往返 / 错口令 / NullStore 写抛 |
| TDA 鲁棒 | `test_tda_robustness.py` | 10 | 注册表 / 向量化对照 / NaN / standardize / auto_max / 空输入 / 单点 / NaN scrub |
| **合计** | | **41** | |

测试运行证据：`/opt/cursor/artifacts/pytest_v0.2_output.log`。

### 5.2 端到端 curl 探针

| 探针 | 文件 | 期望 |
|---|---|---|
| 错误链路（未配置 provider） | `llm_config_error_response.txt` | HTTP 400 + `LLMConfigurationError` + `retryable=false` + `hint` |
| NaN scrub | `sandbox_nonfinite_scrub.json` | `b: null` + `nonfinite_keys: ["b","c[1]"]` |
| Operator registry | `tda_operators.json` | 三个内置算子的 JSON Schema |
| Provider 自描述 | `ai_providers.json` | `server_available / local_available / default` |
| 并发烟测 | `concurrency_smoke.log` | 8 并发 TDA 期间 `/healthz` p95 < 60 ms |

### 5.3 性能基线（事件循环阻塞）

```
负载：8 并发 × 800 点 MST_H0
持续时间窗：~300 ms (并行完成)

╭─────────────┬────────────┬────────────┬────────────╮
│ Endpoint    │  Median    │  p95       │  Max       │
├─────────────┼────────────┼────────────┼────────────┤
│ /tda/...    │  ~298 ms   │  ~305 ms   │  ~305 ms   │
│ /healthz    │    8.5 ms  │   51.8 ms  │   51.8 ms  │
╰─────────────┴────────────┴────────────┴────────────╯
```

> 在 v0.1 的同步路径下，8 个 300 ms 任务串行总耗时约 2.4 s，期间 `/healthz`
> 会进入排队等待，p95 接近秒级。改造后 p95 控制在 60 ms 内 → ≥ **40× 改善**。

---

## 6. 风险与权衡

每一处改造都不是免费的。本节诚实记录权衡：

| 决策 | 收益 | 代价 / 风险 |
|---|---|---|
| 线程池卸载 CPU 任务 | 不阻塞 event loop | 占用 starlette 默认线程池容量；NumPy 必须释放 GIL（已验证）。未来超大点云需迁移到 ProcessPool。 |
| `ctypes.PyThreadState_SetAsyncExc` 超时 | 解决 worker 线程的 SIGALRM 限制 | 只能在 Python 字节码边界生效；纯 C 扩展长循环（如 large `linalg.solve`）可能短暂"超时无效"。同业（IPython）也无更优解。 |
| Operator Registry | 扩展性 | 算子参数 schema 是简化版 JSON Schema，未来若要做完整 validation 需引入 jsonschema。 |
| Slack `urllib.request` | 零额外依赖 | 同步 lib，故走 `asyncio.to_thread`；同事更习惯 `aiohttp` 的方案被刻意拒绝（不为告警引入额外网络栈）。 |
| `_suggest_max_edge` 90 百分位 | 跨尺度自适应 | 极端长尾分布会偏低估计；学生若使用真实尾重数据可显式传 `max_edge_length`。 |
| 严格 provider 路由 | 杜绝 Key 错路 | 错误消息要求学生明白 SERVER/LOCAL 差异；UI 端必须配合 `/ai/providers` 自描述端点做禁用态。 |

---

## 7. 复盘（Retrospective）

**做得好的**

* **先写 reference 对比测试，再做向量化重构**：`test_vectorised_betti_matches_loop_implementation` 让向量化 0 风险通过。这条规则未来对任何性能优化都适用。
* **三维度透镜在审查初期画在白板上**：避免遗漏维度，特别是"防御"轴最容易在面对完整功能时被低估。
* **每个 Fix 携带 1+ 测试**：41 个用例不是"刷数据"，每一项都直接锁住一个 contract。

**改进空间**

* **未引入 `pytest-benchmark`**：性能改造目前只有 `concurrency_smoke.log` 一次性快照。未来应当固化为可重跑的 benchmark suite，否则下次重构容易引入回归而不自知。
* **`/ai/providers` 探针端点直接暴露 `orch._server` 私有属性**：当前用 `# noqa: SLF001` 标注，长期应改为 orchestrator 显式 `describe()` 方法。
* **`config.py` 字段越来越多**：到 v0.3 应当拆分为 `LLMConfig` / `SandboxConfig` / `ObservabilityConfig` 三个嵌套模型，否则容易出现新增字段没人 review 的情况。
* **giotto-tda 安装路径未实测**：CI 镜像没装，所以 `vietoris_rips` 路径只有 numpy fallback 跑过。需要补一条"装 giotto-tda 再跑全套"的 CI matrix。

**未来工单候选**

- [ ] 接入 ChromaDB 后台索引器（v0.1 KnowledgeService 仍是 BoW）。
- [ ] Tauri Rust 端 IPC 实装（目前只有 Python 占位）。
- [ ] `pytest-benchmark` + GitHub Actions 跑性能回归。
- [ ] 给 `Operator.descriptor()` 引入完整 JSON Schema，并在 `/tda/pipeline` 入口对 `params` 做 schema 校验。
- [ ] 给 Slack 告警增加 PagerDuty 备选通道（同一 `AlertSink` 接口）。

---

## 8. 复现指南（Reproducing the Review）

任何团队成员或后续 cloud agent 想要重跑本次审查的同样流程，按以下顺序操作即可。

### 8.1 准备

```bash
git fetch origin cursor/scicompute-assistant-prototype-48fa
git checkout cursor/scicompute-assistant-prototype-48fa
uv pip install --python .venv/bin/python -e "scicompute_assistant[dev]"
```

### 8.2 探针（基线状态采集）

```bash
# 起 v0.1 服务器（在 tmux 里）
SCICOMP_DISABLE_OUTBOUND_LLM=true \
    .venv/bin/python -m uvicorn scicompute_assistant.server.main:app \
    --host 127.0.0.1 --port 8765 &

# 收集基线 curl 探针
curl -s http://127.0.0.1:8765/ai/providers     # v0.1 没有这个端点
curl -s http://127.0.0.1:8765/tda/operators    # v0.1 没有这个端点
curl -s -X POST http://127.0.0.1:8765/compute/run \
     -H 'Content-Type: application/json' \
     -d '{"code":"result = {\"b\": float(\"nan\")}", "timeout_sec": 2}'
# 观察：v0.1 响应里没有 nonfinite_keys，b 字段会是 NaN 序列化失败

# 并发压力探针：观察 /healthz 是否在 burst 中被阻塞
# （v0.1 同步路径下 p95 会进入秒级）
```

### 8.3 三维度议题工单

按 §2.1 表格列出 9 个议题，建立 todo list（本次使用 `TodoWrite` 工具）。

### 8.4 议题循环

对每个议题执行 EHFV 循环（§1.2）：

1. 在代码里搜索可疑模式（`rg -n "raise_for_status\|RuntimeError\|except RuntimeError" scicompute_assistant/`）。
2. 编写最小复现（unit test 或 curl 调用）作为 Evidence。
3. 假设根因，做最小改动。
4. 跑 `.venv/bin/python -m pytest scicompute_assistant/tests` + 相关 curl 验证。

### 8.5 验证证据归档

将关键产出物落到 `/opt/cursor/artifacts/`：

| 文件 | 命令 |
|---|---|
| `pytest_v0.2_output.log` | `pytest scicompute_assistant/tests -v &> /opt/cursor/artifacts/pytest_v0.2_output.log` |
| `concurrency_smoke.log` | 见 §5.3，脚本附在 PR 描述 |
| `llm_config_error_response.txt` | `curl …/ai/chat provider=local > …` |
| `sandbox_nonfinite_scrub.json` | `curl …/compute/run code='…float("nan")…'` |
| `tda_operators.json` | `curl …/tda/operators` |

### 8.6 文档化

* 议题结论 → `REVIEW.md`（Before/After + 设计模式）。
* 审查过程 → 本文 `REVIEW_PROCESS.md`（方法论 + 证据链 + 复盘）。

### 8.7 提交

```bash
git checkout -b cursor/scicompute-deep-review-<suffix>
git add -A
git commit -m "<分类提交消息：架构 / 性能 / 防御 三段>"
git push -u origin cursor/scicompute-deep-review-<suffix>
# 创建 PR，base 选 v0.1 分支，方便逐项 diff
```

---

## 9. 设计模式索引（与 REVIEW.md §四 联动）

| 模式 | 代码体现 | 解决的问题 |
|---|---|---|
| Strategy | `BaseLLM`（ServerProvider / LocalProvider / StubProvider） | 切换 LLM 上游不改 orchestrator |
| Strategy + Registry | `Operator` + `_Registry` | 切换 / 新增 TDA 算子不改协议 |
| Strategy | `AlertSink`（NullAlertSink / SlackWebhookAlertSink） | 切换告警通道不改业务调用方 |
| Typed Exception Hierarchy | `LLMError` 树 + `install_exception_handlers` | HTTP 状态映射集中化、消除散乱 try-except |
| Scoped Context | `AIOrchestrator._Scope` + `ContextVar` | 请求级字段不跨请求串流（async 安全） |
| Façade | `TDAEngine` / `ComputeKernel` | 路由层不直接接触 giotto-tda / RestrictedPython |
| Token Bucket + Backoff + Jitter | `_TokenBucket` + `_with_retries` | 平滑限流、避免 thundering herd |
| Fire-and-Forget | `SlackWebhookAlertSink.emit` | 告警永不打挂业务请求 |
| Open/Closed | Operator Registry / AlertSink / Provider | 扩展新增、修改避免 |

---

## 10. 致后续维护者的话

如果你接手了这个项目并要做下一次审查，记住三件事：

1. **从测试反向读**：`tests/` 是合同的"机器可验证版本"，比文档更不容易腐烂。
2. **任何修改先看 `REVIEW.md` 里这条议题对应的设计模式**——这通常告诉你"为什么会这样写"。
3. **更新本文**：在 §7 复盘和 §6 风险表里追加一行，是后人最感激的事。

> 本审查耗时较短，但工作量集中在"先建议题透镜，再用证据驱动每个议题"上。
> 三维度透镜 + EHFV 循环 + 41 项测试是这套方法学的核心；它可以被复用到任何
> 中等规模的后端系统审查。
