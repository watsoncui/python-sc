# SciCompute-Assistant 原型

双模态（服务版 / 离线版）的 Python 科学计算教学辅助系统：

* AI 调度中台（`ServerProvider` / `LocalProvider` / `AIOrchestrator`）
* 沙箱化的科学计算执行引擎（NumPy / SciPy / giotto-tda）
* 课程 Markdown 课件 RAG（默认内置 BoW，可切换 ChromaDB）
* Tauri 离线密钥安全方案（Stronghold + 加密文件 fallback）

## 文档

| 文档 | 主题 |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 架构拆解 + `common/` 接口规范 |
| [`docs/AI_PROMPTS.md`](docs/AI_PROMPTS.md)     | 向量化审计 System Prompt |
| [`docs/TDA_PROTOCOL.md`](docs/TDA_PROTOCOL.md) | TDA 后端 → Plotly 前端协议 |
| [`docs/SECURITY_TAURI.md`](docs/SECURITY_TAURI.md) | 离线版 API Key 安全方案 |
| [`docs/REVIEW.md`](docs/REVIEW.md) | v0.1 → v0.2 深度审查的 Before/After + 设计模式 |
| [`docs/REVIEW_PROCESS.md`](docs/REVIEW_PROCESS.md) | 审查方法论 / 议题工单 / EHFV 循环 / 复现指南 |

## 快速启动（服务版原型）

```bash
# 1. 安装核心依赖
pip install -e ".[dev]"

# 2. 启动 FastAPI 服务（默认使用桩 LLM，不会真正请求外部模型）
SCICOMP_DISABLE_OUTBOUND_LLM=true scicompute-server
# 或：
uvicorn scicompute_assistant.server.main:app --host 0.0.0.0 --port 8000

# 3. 接通真实模型时，配置环境变量
export SCICOMP_SERVER_API_KEY=sk-...
export SCICOMP_SERVER_DEFAULT_MODEL=gpt-4o-mini
unset SCICOMP_DISABLE_OUTBOUND_LLM
```

## 端点速览

| Method | Path | 说明 |
|---|---|---|
| `GET`  | `/`                       | 元信息（名称/模式/版本） |
| `GET`  | `/healthz`                | 心跳 |
| `POST` | `/ai/chat`                | 教学聊天（自动注入 RAG 上下文） |
| `POST` | `/ai/audit/vectorize`     | 向量化审计（结构化 JSON） |
| `POST` | `/compute/run`            | RestrictedPython 沙箱 |
| `POST` | `/tda/pipeline`           | 持久同调 → Plotly payload |
| `GET`  | `/tda/health`             | giotto-tda 是否可用 |
| `GET`  | `/knowledge/search`       | 课件检索 |
| `POST` | `/knowledge/reindex`      | 重建课件索引 |

## 测试

```bash
pytest scicompute_assistant/tests -v
```

桩 LLM 让所有 AI 路径无网即可冒烟。
