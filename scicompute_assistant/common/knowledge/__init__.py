"""Course-aware RAG layer used by both server and desktop builds."""

from .service import (
    BowBackend,
    ChromaBackend,
    KnowledgeHit,
    KnowledgeService,
    build_knowledge_service,
)

__all__ = [
    "BowBackend",
    "ChromaBackend",
    "KnowledgeHit",
    "KnowledgeService",
    "build_knowledge_service",
]
