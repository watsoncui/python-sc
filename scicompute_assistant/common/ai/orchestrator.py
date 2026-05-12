"""High-level dispatcher used by FastAPI routers / Tauri IPC handlers.

Responsibilities
---------------
* Pick the right provider (server vs local) based on ``ProviderMode``.
* Inject prompts from :class:`PromptLibrary`.
* Pull relevant snippets from the knowledge service (RAG) when available.
* Parse audit responses defensively (LLMs occasionally return wrapped JSON).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ..protocols.api_models import (
    AuditRequest,
    AuditResponse,
    AuditSuggestion,
    ChatRequest,
    ChatResponse,
    LLMUsage,
    ProviderMode,
)
from .base import BaseLLM
from .prompts import PromptLibrary

log = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


class AIOrchestrator:
    """Routes high-level intents to the appropriate provider + prompt."""

    def __init__(
        self,
        *,
        server: BaseLLM | None = None,
        local: BaseLLM | None = None,
        knowledge: Any | None = None,  # ``KnowledgeService`` – kept loose to avoid cycles.
    ) -> None:
        self._server = server
        self._local = local
        self._knowledge = knowledge

    # ------------------------------------------------------------------ #
    # Provider selection
    # ------------------------------------------------------------------ #
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

    async def aclose(self) -> None:
        for p in (self._server, self._local):
            if p is not None:
                await p.aclose()

    # ------------------------------------------------------------------ #
    # RAG helper (best-effort, never blocks the request on RAG failure)
    # ------------------------------------------------------------------ #
    def _retrieve_context(self, *, tags: list[str] | None, query: str) -> tuple[str, list[str]]:
        if self._knowledge is None:
            return "", []
        try:
            hits = self._knowledge.retrieve(query=query, tags=tags or [], k=4)
        except Exception:  # noqa: BLE001 - RAG must never break LLM call
            log.warning("Knowledge retrieval failed; falling back to no-context.", exc_info=True)
            return "", []
        merged = "\n---\n".join(h.text for h in hits)
        return merged, [h.doc_id for h in hits]

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    async def chat(self, req: ChatRequest) -> ChatResponse:
        provider = self._pick(req.provider)
        query = req.messages[-1].content if req.messages else ""
        context, hits = self._retrieve_context(tags=req.context_tags, query=query)

        prompt = PromptLibrary.teaching_chat(history=req.messages, course_context=context)
        result = await provider.acomplete(
            prompt,
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            key_alias=req.local_key_alias,
        )
        return ChatResponse(reply=result.message, usage=result.usage, knowledge_hits=hits)

    async def audit_vectorize(self, req: AuditRequest) -> AuditResponse:
        provider = self._pick(req.provider)
        tags = [f"week:{req.course_week}"] if req.course_week else []
        context, _hits = self._retrieve_context(tags=tags, query=req.code[:512])

        prompt = PromptLibrary.vectorize_audit(
            code=req.code,
            course_week=req.course_week,
            target=req.target,
            course_context=context,
        )
        result = await provider.acomplete(
            prompt,
            model=None,
            temperature=0.1,  # vectorization audit wants determinism
            max_tokens=2048,
            key_alias=req.local_key_alias,
        )
        return self._parse_audit_response(result.message.content, usage=result.usage)

    # ------------------------------------------------------------------ #
    # Parsing helpers (LLM-tolerant)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_audit_response(text: str, *, usage: LLMUsage) -> AuditResponse:
        """Tolerant JSON parser: strips Markdown fences then falls back to regex.

        The system prompt forbids Markdown fences, but real-world LLMs leak.
        """
        cleaned = text.strip()
        # Strip ```json ... ``` fences if present.
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)

        data: dict | None = None
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            m = _JSON_BLOCK_RE.search(cleaned)
            if m:
                try:
                    data = json.loads(m.group(0))
                except json.JSONDecodeError:
                    data = None

        if not isinstance(data, dict):
            return AuditResponse(
                summary="LLM 输出无法解析为 JSON，请重试或切换模型。",
                suggestions=[],
                refactored_code=None,
                usage=usage,
            )

        suggestions = [
            AuditSuggestion(**s) for s in data.get("suggestions", []) if isinstance(s, dict)
        ]
        return AuditResponse(
            summary=str(data.get("summary", "")),
            suggestions=suggestions,
            refactored_code=data.get("refactored_code"),
            usage=usage,
        )
