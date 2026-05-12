"""Top-level request/response models shared by FastAPI routes and the desktop IPC layer.

These models are intentionally framework-agnostic so they can be reused by:
  * FastAPI route handlers (server build).
  * The Tauri `invoke` IPC bridge (desktop build, where the same Python core runs
    inside an embedded process or sidecar).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProviderMode(str, Enum):
    """Which LLM backend the orchestrator should route to."""

    SERVER = "server"  # Teacher-managed shared key (rate limited).
    LOCAL = "local"    # Student-provided personal key (stored encrypted locally).


# --------------------------------------------------------------------------- #
# Chat
# --------------------------------------------------------------------------- #
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    provider: ProviderMode = ProviderMode.SERVER


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    provider: ProviderMode = ProviderMode.SERVER
    temperature: float = Field(0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, ge=1, le=8192)
    model: str | None = None
    # Optional: pass the encrypted local key handle so LocalProvider can decrypt it.
    local_key_alias: str | None = None
    # Free-form metadata (e.g. course week, knowledge-point id) – used for RAG.
    context_tags: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: ChatMessage
    usage: LLMUsage
    knowledge_hits: list[str] = Field(
        default_factory=list,
        description="IDs of courseware snippets injected by the RAG layer.",
    )


# --------------------------------------------------------------------------- #
# Code audit  (核心功能：将循环代码转化为向量化代码)
# --------------------------------------------------------------------------- #
class AuditRequest(BaseModel):
    code: str = Field(..., description="Student-submitted Python source.")
    provider: ProviderMode = ProviderMode.SERVER
    local_key_alias: str | None = None
    course_week: int | None = Field(
        default=None,
        ge=1,
        le=19,
        description="Week index of the course; used for RAG and style guidance.",
    )
    target: Literal["vectorize", "explain", "debug"] = "vectorize"


class AuditSuggestion(BaseModel):
    category: Literal[
        "vectorization",
        "memory_layout",
        "numerical_stability",
        "api_correctness",
        "style",
    ]
    severity: Literal["info", "warn", "error"] = "info"
    line_range: tuple[int, int] | None = None
    rationale: str
    rewritten_snippet: str | None = None


class AuditResponse(BaseModel):
    summary: str
    suggestions: list[AuditSuggestion]
    refactored_code: str | None = Field(
        default=None,
        description="A full vectorized rewrite produced by the LLM, if available.",
    )
    usage: LLMUsage


# --------------------------------------------------------------------------- #
# Sandboxed code execution
# --------------------------------------------------------------------------- #
class ComputeRequest(BaseModel):
    code: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    timeout_sec: float = Field(5.0, gt=0.0, le=60.0)
    capture_stdout: bool = True


class ComputeResponse(BaseModel):
    ok: bool
    stdout: str = ""
    stderr: str = ""
    result: dict[str, Any] = Field(default_factory=dict)
    elapsed_ms: float = 0.0
    error: str | None = None
