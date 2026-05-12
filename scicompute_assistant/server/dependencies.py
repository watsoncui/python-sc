"""Application-wide singletons (DI for FastAPI routes)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import Request

from ..common.ai import (
    AIOrchestrator,
    BaseLLM,
    LocalProvider,
    ServerProvider,
)
from ..common.ai.base import LLMCallResult
from ..common.compute import ComputeKernel, TDAEngine
from ..common.knowledge import KnowledgeService
from ..common.protocols.api_models import ChatMessage, LLMUsage, ProviderMode
from ..common.security import build_default_store
from .config import ServerSettings, load_settings


class _StubProvider(BaseLLM):
    """No-network provider used in CI / smoke tests.

    Returns a deterministic shaped response so the route layer is exercised
    end-to-end without hitting an upstream LLM. Audit responses are valid
    JSON that conforms to the system prompt's contract.
    """

    name = "stub"
    mode = ProviderMode.SERVER

    def __init__(self, *, default_model: str = "stub-model") -> None:
        super().__init__(default_model=default_model)

    async def acomplete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMCallResult:
        last_user = next((m for m in reversed(messages) if m.role == "user"), None)
        is_audit = any(
            "向量化审计助教" in m.content for m in messages if m.role == "system"
        )
        if is_audit:
            content = (
                '{"summary":"stub: 检测到 for 循环可向量化",'
                '"suggestions":[{"category":"vectorization","severity":"info",'
                '"line_range":[1,3],'
                '"rationale":"使用 np.sum(arr**2) 替代显式累加；广播免去 Python 解释器开销。",'
                '"rewritten_snippet":"return np.sum(arr ** 2)"}],'
                '"refactored_code":"import numpy as np\\n\\n'
                'def sum_squares(arr):\\n    arr = np.asarray(arr, dtype=np.float64)\\n'
                '    return float(np.sum(arr ** 2))"}'
            )
        else:
            content = "stub-reply: " + (last_user.content[:120] if last_user else "(empty)")
        return LLMCallResult(
            message=ChatMessage(role="assistant", content=content),
            usage=LLMUsage(
                prompt_tokens=self.count_tokens(" ".join(m.content for m in messages)),
                completion_tokens=self.count_tokens(content),
                total_tokens=0,
                model=model or self.default_model,
                provider=self.mode,
            ),
        )


@lru_cache
def get_settings() -> ServerSettings:
    return load_settings()


@lru_cache
def get_knowledge_service() -> KnowledgeService:
    settings = get_settings()
    return KnowledgeService(root=settings.courseware_root)


@lru_cache
def get_compute_kernel() -> ComputeKernel:
    settings = get_settings()
    return ComputeKernel(
        timeout_sec=settings.sandbox_timeout_sec,
        restricted=settings.sandbox_restricted,
    )


@lru_cache
def get_tda_engine() -> TDAEngine:
    return TDAEngine()


@lru_cache
def get_orchestrator() -> AIOrchestrator:
    settings = get_settings()

    server: BaseLLM | None = None
    local: BaseLLM | None = None

    if settings.disable_outbound_llm or not settings.server_api_key:
        server = _StubProvider()
    else:
        server = ServerProvider(
            api_key=settings.server_api_key,
            base_url=settings.server_base_url,
            default_model=settings.server_default_model,
            rpm_limit=settings.server_rpm_limit,
            burst=settings.server_burst,
        )

    if settings.mode == "desktop":
        store = build_default_store(
            mode="desktop",
            fallback_path=settings.fallback_store_path,
            fallback_passphrase=settings.fallback_passphrase or "scicompute-dev",
        )
        local = LocalProvider(
            store=store,
            default_endpoint=settings.local_default_endpoint,
            default_model=settings.local_default_model,
        )

    return AIOrchestrator(server=server, local=local, knowledge=get_knowledge_service())


# ------------------------------------------------------------------ #
# FastAPI deps
# ------------------------------------------------------------------ #
def orchestrator_dep(request: Request) -> AIOrchestrator:  # noqa: ARG001
    return get_orchestrator()


def kernel_dep(request: Request) -> ComputeKernel:  # noqa: ARG001
    return get_compute_kernel()


def tda_dep(request: Request) -> TDAEngine:  # noqa: ARG001
    return get_tda_engine()


def knowledge_dep(request: Request) -> KnowledgeService:  # noqa: ARG001
    return get_knowledge_service()
