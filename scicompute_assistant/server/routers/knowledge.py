"""RAG / knowledge search routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...common.knowledge import KnowledgeService
from ..dependencies import knowledge_dep

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    tag: list[str] = Query(default_factory=list),
    k: int = Query(4, ge=1, le=20),
    svc: KnowledgeService = Depends(knowledge_dep),
):
    hits = svc.retrieve(query=q, tags=tag, k=k)
    return [
        {"doc_id": h.doc_id, "score": h.score, "tags": h.tags, "preview": h.text}
        for h in hits
    ]


@router.post("/reindex")
async def reindex(svc: KnowledgeService = Depends(knowledge_dep)) -> dict[str, str]:
    svc.reindex()
    return {"status": "ok"}
