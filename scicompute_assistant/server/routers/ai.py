"""AI routes: chat + vectorization audit.

Errors are mapped centrally by :func:`scicompute_assistant.server.error_handlers.install_exception_handlers`,
so route handlers can stay focused on intent.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...common.ai import AIOrchestrator
from ...common.protocols.api_models import (
    AuditRequest,
    AuditResponse,
    ChatRequest,
    ChatResponse,
)
from ..dependencies import orchestrator_dep

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, orch: AIOrchestrator = Depends(orchestrator_dep)) -> ChatResponse:
    return await orch.chat(req)


@router.post("/audit/vectorize", response_model=AuditResponse)
async def audit_vectorize(
    req: AuditRequest,
    orch: AIOrchestrator = Depends(orchestrator_dep),
) -> AuditResponse:
    return await orch.audit_vectorize(req)


@router.get("/providers")
async def providers(orch: AIOrchestrator = Depends(orchestrator_dep)) -> dict[str, object]:
    """Expose which providers are wired in the current build.

    Front-ends use this to grey out the matching toggle so students
    cannot pick a mode that will never work in this build.
    """
    return orch.describe()
