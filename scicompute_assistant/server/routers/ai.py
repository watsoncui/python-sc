"""AI routes: chat + vectorization audit."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from ...common.ai import AIOrchestrator
from ...common.protocols.api_models import (
    AuditRequest,
    AuditResponse,
    ChatRequest,
    ChatResponse,
)
from ..dependencies import orchestrator_dep

log = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, orch: AIOrchestrator = Depends(orchestrator_dep)) -> ChatResponse:
    try:
        return await orch.chat(req)
    except (PermissionError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/audit/vectorize", response_model=AuditResponse)
async def audit_vectorize(
    req: AuditRequest,
    orch: AIOrchestrator = Depends(orchestrator_dep),
) -> AuditResponse:
    try:
        return await orch.audit_vectorize(req)
    except (PermissionError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
