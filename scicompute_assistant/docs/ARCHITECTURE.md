# SciCompute-Assistant 架构拆解

> 任务 1：目录结构与 `common/` 核心类接口规范。

## 1. 顶层目录布局

```
scicompute_assistant/
├── pyproject.toml              # 单一构建脚本，被服务版/桌面版共享
├── README.md
│
├── common/                     # 共享代码 ≥ 90 %（服务版与桌面版共用）
│   ├── ai/                     # AI 适配器层
│   │   ├── base.py             # BaseLLM 抽象类
│   │   ├── server_provider.py  # 老师账号 + 频率限制
│   │   ├── local_provider.py   # 学生本地 Key + 端点白名单
│   │   ├── orchestrator.py     # 高层调度中台
│   │   └── prompts.py          # System Prompt 模板库（见 AI_PROMPTS.md）
│   ├── compute/                # 科学计算执行引擎
│   │   ├── sandbox.py          # RestrictedPython + 信号超时
│   │   ├── kernel.py           # ComputeKernel 门面
│   │   └── tda.py              # giotto-tda + NumPy 兜底
│   ├── knowledge/              # 课程 RAG
│   │   └── service.py          # 内置 BoW，可换 ChromaDB
│   ├── protocols/              # Pydantic 通信协议（前后端 + IPC 共用）
│   │   ├── api_models.py
│   │   └── tda_payload.py
│   ├── security/               # 本地密钥存储
│   │   └── keyring_store.py    # Tauri / EncryptedFile / Null
│   └── utils/
│
├── server/                     # FastAPI 入口（云端版）
│   ├── main.py                 # app factory + uvicorn 启动器
│   ├── config.py               # pydantic-settings
│   ├── dependencies.py         # 单例 DI
│   ├── middleware/rate_limit.py
│   └── routers/{ai,compute,tda,knowledge}.py
│
├── desktop/                    # Tauri 入口（离线版）
│   └── src-tauri/              # Rust 端：keychain 桥 + Python sidecar
│
├── frontend/                   # 前端代码骨架（React/Reflex 任选）
│
├── assets/courseware/          # Markdown 课件，被 KnowledgeService 索引
│
└── tests/
```

### 复用比例的实现路径

* **路由器实现** 不写业务逻辑，只在 `common.*` 上做一层 Pydantic 收发——保证后端
  桌面版直接调用 `AIOrchestrator.audit_vectorize` 等方法即可复用 100 % 业务代码。
* **AI 适配器** 通过 `BaseLLM` 抽象屏蔽了云/本地差异；唯一的差异面在 `dependencies.py`
  的工厂函数里，根据 `SCICOMP_MODE` 选择装配方式。
* **安全模块** 同理使用策略模式：服务版装 `NullStore`，桌面版装 `TauriKeyringStore`
  （或 `EncryptedFileStore` 作为 fallback）。

## 2. `common/` 关键接口契约

### 2.1 `common.ai.base.BaseLLM`

```python
class BaseLLM(abc.ABC):
    name: str           # provider 唯一标识
    mode: ProviderMode  # SERVER | LOCAL

    def __init__(self, *, default_model: str) -> None: ...

    @abc.abstractmethod
    async def acomplete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,           # 子类可塞入 key_alias / endpoint 等
    ) -> LLMCallResult: ...

    def count_tokens(self, text: str) -> int: ...
    async def aclose(self) -> None: ...
```

**要点**：仅一个抽象方法（`acomplete`），其余为可选 hook；返回结构化的
`LLMCallResult`，避免子类把原始 dict 泄漏到上层。

### 2.2 `common.ai.AIOrchestrator`

```python
class AIOrchestrator:
    def __init__(self, *, server: BaseLLM | None, local: BaseLLM | None,
                 knowledge: KnowledgeService | None) -> None: ...

    async def chat(self, req: ChatRequest) -> ChatResponse: ...
    async def audit_vectorize(self, req: AuditRequest) -> AuditResponse: ...
    async def aclose(self) -> None: ...
```

**职责边界**：

* 选择 provider（`ProviderMode`）。
* 注入 `PromptLibrary` 模板。
* 尽力（best-effort）调用 `KnowledgeService.retrieve` 注入课件上下文；失败时静默退化。
* 解析 LLM 返回的 JSON，容忍 Markdown 围栏与前置闲聊。

### 2.3 `common.compute.ComputeKernel` / `Sandbox`

```python
@dataclass
class SandboxResult:
    ok: bool
    stdout: str
    stderr: str
    result: dict[str, Any]
    elapsed_ms: float
    error: str | None

class Sandbox:
    def __init__(self, *, timeout_sec: float, allow_restricted: bool) -> None: ...
    def run(self, code: str, *, inputs: dict[str, Any] | None) -> SandboxResult: ...

class ComputeKernel:
    def run_code(self, code: str, *, inputs=None, timeout_sec=None) -> SandboxResult: ...
```

**安全分层**：

1. AST 层 —— `RestrictedPython.compile_restricted` 阻断危险字面量与属性。
2. 运行时层 —— 受限 `builtins` + `_safe_import` 白名单。
3. 进程层 —— POSIX `SIGALRM` / Windows `Timer` 强行打断超时。
4. 部署层 —— **建议** 在服务版把 sandbox 进一步嵌入 gVisor / Firecracker。

### 2.4 `common.compute.TDAEngine`

```python
class TDAEngine:
    @property
    def is_available(self) -> bool: ...
    def compute(self, req: TDARequest) -> TDAResponse: ...
```

* 装了 giotto-tda 时调用 `VietorisRipsPersistence` / `WeakAlphaPersistence`。
* 未装时回退到 SciPy MST，仅生成 H0；上层通过 `warnings` 提示学生。
* 输出 100 % 是 `PersistenceDiagramPayload`，详见 `TDA_PROTOCOL.md`。

### 2.5 `common.knowledge.KnowledgeService`

```python
@dataclass
class KnowledgeHit:
    doc_id: str
    text: str
    score: float
    tags: list[str]

class KnowledgeService:
    def __init__(self, root: Path) -> None: ...
    def reindex(self) -> None: ...
    def retrieve(self, *, query: str, tags: Iterable[str] = (), k: int = 4
                 ) -> list[KnowledgeHit]: ...
```

* 默认内存 BoW，零依赖。
* 通过子类化 / `make_chroma_service` 工厂切换到 ChromaDB（学生离线环境只在
  *首次* 使用时构建嵌入索引）。

### 2.6 `common.security.SecurityStore`

```python
class SecurityStore(abc.ABC):
    def get_secret(self, name: str) -> str | None: ...
    def set_secret(self, name: str, value: str) -> None: ...
    def delete_secret(self, name: str) -> None: ...
    def list_aliases(self) -> Iterable[str]: ...
```

* `TauriKeyringStore`：桌面版首选，调用 Tauri IPC（→ macOS Keychain / Windows
  Credential Manager / libsecret）。
* `EncryptedFileStore`：Linux fallback，PBKDF2-HMAC-SHA256（600k 轮）+ Fernet
  对称加密；密钥派生自学生输入的 master passphrase。
* `NullStore`：服务版默认，所有写操作直接 `raise`，避免误路由。

## 3. 部署形态对照

| 项 | 服务版（FastAPI） | 离线版（Tauri） |
|---|---|---|
| 入口 | `uvicorn scicompute_assistant.server.main:app` | Tauri 加载内嵌 Python sidecar（PyOxidizer 或 pyinstaller）执行同样的 `create_app()`，仅本机绑定 |
| LLM provider | `ServerProvider`（教师 Key + 频率限制） | `LocalProvider`（OS keychain 取 Key） |
| 安全存储 | `NullStore` | `TauriKeyringStore`（fallback：`EncryptedFileStore`） |
| 沙箱 | RestrictedPython + （建议）gVisor | RestrictedPython + 用户机本地权限 |
| RAG 索引 | 服务端预构建，挂载只读 | 学生首次启动时本地构建，磁盘缓存 |

## 4. 进程拓扑（离线版）

```
┌──────────────────────────────────────────┐
│  Tauri WebView (React + Plotly)          │
│   - 代码编辑器 / 持久图 / 切换开关        │
└──────────────▲───────────────────────────┘
               │ IPC (invoke)
┌──────────────┴───────────────────────────┐
│  Rust Core (src-tauri)                   │
│   - keyring 桥 (tauri-plugin-keyring)    │
│   - spawn Python sidecar                  │
└──────────────▲───────────────────────────┘
               │ stdio / 127.0.0.1 only
┌──────────────┴───────────────────────────┐
│  Python sidecar (uvicorn, --host 127.0.0.1)│
│   - 与服务版完全一致的 FastAPI 应用       │
│   - LocalProvider 通过 IPC 反向调用 keyring│
└──────────────────────────────────────────┘
```

* 仅监听 127.0.0.1；端口由 Rust 在启动时随机分配并写入临时配置。
* Rust 侧 IPC 函数 `secret_get` / `secret_set` 经 Tauri allowlist 暴露给前端 *与*
  Python sidecar，保证 Key 始终在 OS keychain 内停留。
