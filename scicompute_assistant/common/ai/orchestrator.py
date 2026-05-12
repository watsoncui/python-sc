"""High-level dispatcher used by FastAPI routers / Tauri IPC handlers.

Hardenings vs. the v0.1 prototype
---------------------------------
* **Strict provider routing**: ``audit_vectorize`` / ``chat`` never silently
  fall back from LOCAL → SERVER (or vice-versa). If the requested mode is
  not configured, we raise a typed error – this prevents a desktop build
  accidentally talking to the teacher key, and a server build accidentally
  reading a missing student key.
* **Per-call isolation**: every ``acomplete`` call is wrapped in a fresh
  ``bind_request_context`` so concurrent students don't share log fields
  (state-race fix).
* **Typed error mapping**: provider exceptions propagate as `LLMError`
  subclasses; the FastAPI route layer maps each to the right HTTP status.
* **Alert sink**: 5xx-class upstream failures emit a Slack alert.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

from ..observability import bind_request_context, get_alert_sink, get_logger
from ..observability.alerts import AlertEvent
from ..observability.logging import new_request_id, unbind_request_context
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
from .errors import (
    LLMConfigurationError,
    LLMError,
    LLMResponseError,
    LLMUpstreamError,
)
from .prompts import PromptLibrary

log = get_logger(__name__)

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


class AIOrchestrator:
    def __init__(
        self,
        *,
        server: BaseLLM | None = None,
        local: BaseLLM | None = None,
        knowledge: Any | None = None,
    ) -> None:
        self._server = server
        self._local = local
        self._knowledge = knowledge

    # ------------------------------------------------------------------ #
    # Provider selection (strict, no silent fallback)
    # ------------------------------------------------------------------ #
    def _pick(self, mode: ProviderMode) -> BaseLLM:
        if mode is ProviderMode.SERVER:
            if self._server is None:
                raise LLMConfigurationError(
                    "Server provider is not configured on this build. "
                    "Set SCICOMP_SERVER_API_KEY or call with provider='local'."
                )
            return self._server
        if mode is ProviderMode.LOCAL:
            if self._local is None:
                raise LLMConfigurationError(
                    "Local provider is not configured on this build. "
                    "Switch the app to desktop mode or use provider='server'."
                )
            return self._local
        raise LLMConfigurationError(f"Unknown provider mode: {mode!r}")

    async def aclose(self) -> None:
        for p in (self._server, self._local):
            if p is not None:
                await p.aclose()

    # ------------------------------------------------------------------ #
    # RAG (best-effort; never breaks the LLM call)
    # ------------------------------------------------------------------ #
    def _retrieve_context(self, *, tags: list[str] | None, query: str) -> tuple[str, list[str]]:
        if self._knowledge is None:
            return "", []
        try:
            hits = self._knowledge.retrieve(query=query, tags=tags or [], k=4)
        except Exception:  # noqa: BLE001
            log.warning("Knowledge retrieval failed; falling back to no-context.", exc_info=True)
            return "", []
        merged = "\n---\n".join(h.text for h in hits)
        return merged, [h.doc_id for h in hits]

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    async def chat(self, req: ChatRequest) -> ChatResponse:
        async with self._scope(provider=req.provider.value, op="chat") as ctx:
            provider = self._pick(req.provider)
            query = req.messages[-1].content if req.messages else ""
            context, hits = self._retrieve_context(tags=req.context_tags, query=query)
            prompt = PromptLibrary.teaching_chat(history=req.messages, course_context=context)
            log.info("ai.chat start", extra={"messages": len(prompt), "rag_hits": len(hits)})
            start = time.perf_counter()
            result = await self._call_with_alerts(
                provider.acomplete(
                    prompt,
                    model=req.model,
                    temperature=req.temperature,
                    max_tokens=req.max_tokens,
                    key_alias=req.local_key_alias,
                )
            )
            log.info("ai.chat ok", extra={"elapsed_ms": (time.perf_counter() - start) * 1000,
                                          "usage": result.usage.model_dump()})
            ctx["usage"] = result.usage.model_dump()
            return ChatResponse(reply=result.message, usage=result.usage, knowledge_hits=hits)

    async def audit_vectorize(self, req: AuditRequest) -> AuditResponse:
        async with self._scope(provider=req.provider.value, op="audit_vectorize") as ctx:
            provider = self._pick(req.provider)
            tags = [f"week:{req.course_week}"] if req.course_week else []
            context, _ = self._retrieve_context(tags=tags, query=req.code[:512])
            prompt = PromptLibrary.vectorize_audit(
                code=req.code,
                course_week=req.course_week,
                target=req.target,
                course_context=context,
            )
            start = time.perf_counter()
            result = await self._call_with_alerts(
                provider.acomplete(
                    prompt,
                    model=None,
                    temperature=0.1,
                    max_tokens=2048,
                    key_alias=req.local_key_alias,
                )
            )
            log.info("ai.audit ok",
                     extra={"elapsed_ms": (time.perf_counter() - start) * 1000,
                            "code_lines": req.code.count("\n") + 1})
            ctx["usage"] = result.usage.model_dump()
            return self._parse_audit_response(result.message.content, usage=result.usage)

    # ------------------------------------------------------------------ #
    # Cross-cutting helpers
    # ------------------------------------------------------------------ #
    class _Scope:
        """Async context manager: binds request_id + reports failures to Slack."""

        def __init__(self, fields: dict[str, Any]) -> None:
            self.fields = fields
            self._token = None
            self.ctx: dict[str, Any] = {}

        async def __aenter__(self) -> dict[str, Any]:
            fields = {**self.fields, "request_id": new_request_id()}
            self._token = bind_request_context(**fields)
            return self.ctx

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            try:
                if exc is not None and isinstance(exc, LLMError):
                    sink = get_alert_sink()
                    severity = "error" if isinstance(exc, LLMUpstreamError) else "warning"
                    await sink.emit(
                        AlertEvent(
                            severity=severity,
                            title=f"LLM call failed: {type(exc).__name__}",
                            body=str(exc),
                            fields={**self.fields, **self.ctx, "retryable": exc.retryable},
                        )
                    )
                    log.warning("ai.failed",
                                extra={"error_type": type(exc).__name__,
                                       "error_msg": str(exc)})
            finally:
                if self._token is not None:
                    unbind_request_context(self._token)
            return False

    def _scope(self, **fields: Any) -> "AIOrchestrator._Scope":
        return AIOrchestrator._Scope(fields)

    @staticmethod
    async def _call_with_alerts(coro):
        try:
            return await coro
        except asyncio.CancelledError:
            raise
        except LLMError:
            raise
        except Exception as exc:  # noqa: BLE001 - wrap unknown to typed
            raise LLMResponseError(f"Unexpected provider failure: {exc!r}") from exc

    # ------------------------------------------------------------------ #
    # LLM-tolerant JSON parser
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_audit_response(text: str, *, usage: LLMUsage) -> AuditResponse:
        cleaned = (text or "").strip()
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

        suggestions: list[AuditSuggestion] = []
        for s in data.get("suggestions", []) or []:
            if not isinstance(s, dict):
                continue
            try:
                suggestions.append(AuditSuggestion(**s))
            except Exception:  # noqa: BLE001 - one bad row should not kill the response
                log.debug("Dropping malformed suggestion row.", exc_info=True)

        return AuditResponse(
            summary=str(data.get("summary", "")),
            suggestions=suggestions,
            refactored_code=data.get("refactored_code"),
            usage=usage,
        )
