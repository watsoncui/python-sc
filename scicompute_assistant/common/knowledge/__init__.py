"""Course-aware RAG layer used by both server and desktop builds."""

from .service import KnowledgeHit, KnowledgeService

__all__ = ["KnowledgeHit", "KnowledgeService"]
