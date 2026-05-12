"""Knowledge service – minimal local RAG.

By default uses a tiny in-memory bag-of-words index so the prototype runs
without ChromaDB; production deployments swap the backend by subclassing
:class:`KnowledgeService` (see :func:`make_chroma_service` for a hook).
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

log = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


@dataclass
class KnowledgeHit:
    doc_id: str
    text: str
    score: float
    tags: list[str]


@dataclass
class _Doc:
    doc_id: str
    text: str
    tags: list[str]
    tokens: Counter[str]


class KnowledgeService:
    """In-memory bag-of-words index over Markdown courseware.

    The index re-loads on demand (cheap for course-sized corpora) so the
    desktop build can drop new ``.md`` files in ``assets/courseware/`` and
    immediately see them surfaced.
    """

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._docs: list[_Doc] = []
        self.reindex()

    # ------------------------------------------------------------------ #
    def reindex(self) -> None:
        self._docs.clear()
        if not self._root.exists():
            log.info("KnowledgeService root %s does not exist; skipping index.", self._root)
            return
        for md in sorted(self._root.rglob("*.md")):
            text = md.read_text("utf-8")
            tags = self._parse_tags(text)
            self._docs.append(
                _Doc(
                    doc_id=str(md.relative_to(self._root)),
                    text=text,
                    tags=tags,
                    tokens=Counter(_tokenize(text)),
                )
            )

    @staticmethod
    def _parse_tags(text: str) -> list[str]:
        # naive front-matter style: lines like `tags: week:3, numpy`
        for line in text.splitlines()[:10]:
            if line.lower().startswith("tags:"):
                return [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]
        return []

    # ------------------------------------------------------------------ #
    def retrieve(
        self,
        *,
        query: str,
        tags: Iterable[str] = (),
        k: int = 4,
    ) -> list[KnowledgeHit]:
        if not self._docs:
            return []
        q_tokens = Counter(_tokenize(query))
        tag_set = set(tags)
        scored: list[tuple[float, _Doc]] = []
        for doc in self._docs:
            # exact-tag match boost
            tag_boost = 1.0 + sum(1.0 for t in tag_set if t in doc.tags)
            inter = sum(min(q_tokens[w], doc.tokens[w]) for w in q_tokens)
            denom = max(1, sum(q_tokens.values()))
            score = (inter / denom) * tag_boost
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, doc in scored[:k]:
            snippet = doc.text[:400]
            out.append(
                KnowledgeHit(
                    doc_id=doc.doc_id,
                    text=snippet,
                    score=round(score, 4),
                    tags=doc.tags,
                )
            )
        return out


def make_chroma_service(*args, **kwargs):  # pragma: no cover - production hook
    """Placeholder factory – wire-in ChromaDB when the optional extra is installed."""
    raise NotImplementedError(
        "ChromaDB backend requires `pip install scicompute-assistant[rag]`."
    )
