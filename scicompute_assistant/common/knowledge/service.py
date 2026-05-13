"""Knowledge service — dual-backend RAG over Markdown courseware.

Architecture
------------
Two concrete backends share the same :class:`KnowledgeService` interface
(Strategy pattern), selected at construction time:

* :class:`BowBackend` — zero-dependency bag-of-words; runs everywhere,
  good enough for < 200 snippets.
* :class:`ChromaBackend` — persistent dense-embedding index via ChromaDB +
  sentence-transformers; activates automatically when both packages are
  installed.  The first call to :meth:`reindex` downloads or loads the
  embedding model from the sentence-transformers cache.

The public API is identical for both backends so the server bootstrap and
the orchestrator never need to know which one is running.

Why not subclass KnowledgeService?
-----------------------------------
Because the two backends differ only in their *retrieve* implementation,
and composition avoids the fragile-base-class problem.  ``KnowledgeService``
owns the file-walking and tag-parsing logic; the injected backend owns the
scoring.

Auto-selection
--------------
``build_knowledge_service(root)`` picks the backend automatically:
1. Try ChromaDB + sentence-transformers — if both are importable, build
   :class:`ChromaBackend`.
2. Otherwise fall back to :class:`BowBackend` and emit a one-time INFO log.

Hot-reload
----------
``KnowledgeService.reindex()`` re-walks the ``root`` directory and
rebuilds the backend index without restarting the server.  The desktop
build calls this on startup so newly-dropped courseware files are
immediately searchable.
"""

from __future__ import annotations

import abc
import hashlib
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


# --------------------------------------------------------------------------- #
# Shared data structures
# --------------------------------------------------------------------------- #
@dataclass
class KnowledgeHit:
    doc_id: str
    text: str
    score: float
    tags: list[str]


@dataclass
class _Document:
    doc_id: str
    text: str
    tags: list[str]


# --------------------------------------------------------------------------- #
# Backend interface
# --------------------------------------------------------------------------- #
class _Backend(abc.ABC):
    """Scoring/retrieval strategy.  Implementations hold no document I/O logic."""

    @abc.abstractmethod
    def index(self, docs: list[_Document]) -> None:
        """Rebuild the index from scratch."""

    @abc.abstractmethod
    def query(
        self,
        query: str,
        tags: Iterable[str],
        k: int,
    ) -> list[KnowledgeHit]:
        """Return top-k hits, most relevant first."""

    @property
    @abc.abstractmethod
    def name(self) -> str: ...


# --------------------------------------------------------------------------- #
# Backend 1: Bag-of-Words (zero deps)
# --------------------------------------------------------------------------- #
@dataclass
class _BowDoc:
    base: _Document
    tokens: Counter[str]


class BowBackend(_Backend):
    """TF-style intersection + exact-tag boost. O(n_docs × query_tokens)."""

    name = "bow"

    def __init__(self) -> None:
        self._docs: list[_BowDoc] = []

    def index(self, docs: list[_Document]) -> None:
        self._docs = [
            _BowDoc(base=d, tokens=Counter(_tokenize(d.text))) for d in docs
        ]

    def query(self, query: str, tags: Iterable[str], k: int) -> list[KnowledgeHit]:
        if not self._docs:
            return []
        q_tokens = Counter(_tokenize(query))
        tag_set = set(tags)
        scored: list[tuple[float, _BowDoc]] = []
        for doc in self._docs:
            tag_boost = 1.0 + sum(1.0 for t in tag_set if t in doc.base.tags)
            inter = sum(min(q_tokens[w], doc.tokens[w]) for w in q_tokens)
            denom = max(1, sum(q_tokens.values()))
            score = (inter / denom) * tag_boost
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            KnowledgeHit(
                doc_id=bd.base.doc_id,
                text=bd.base.text[:500],
                score=round(sc, 4),
                tags=bd.base.tags,
            )
            for sc, bd in scored[:k]
        ]


# --------------------------------------------------------------------------- #
# Backend 2: ChromaDB + sentence-transformers
# --------------------------------------------------------------------------- #
class ChromaBackend(_Backend):
    """Persistent dense-embedding retrieval.

    Parameters
    ----------
    persist_directory
        Folder where Chroma stores its SQLite + Parquet files.  Uses an
        in-memory collection when ``None`` (useful for tests).
    embedding_model
        Any sentence-transformers model name.  Defaults to the small but
        capable ``all-MiniLM-L6-v2`` (22 MB).  Swap to a Chinese-aware
        model such as ``shibing624/text2vec-base-chinese`` for Chinese-
        heavy courseware.
    collection_name
        Chroma collection identifier.  Change when shipping multiple
        independent knowledge bases in the same deployment.
    """

    name = "chroma"

    def __init__(
        self,
        *,
        persist_directory: str | None = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "scicompute_courseware",
    ) -> None:
        import chromadb
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )

        if persist_directory is not None:
            self._client = chromadb.PersistentClient(path=persist_directory)
        else:
            self._client = chromadb.Client()

        self._ef = SentenceTransformerEmbeddingFunction(
            model_name=embedding_model,
            device="cpu",
        )
        self._collection_name = collection_name
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._doc_map: dict[str, _Document] = {}

    def index(self, docs: list[_Document]) -> None:
        """Full re-index: delete the old collection and re-add all docs.

        We re-use the doc_id as the Chroma ID after hashing it to a
        safe alphanumeric string.  Tags are stored as metadata so the
        filter step can boost exact matches.
        """
        if not docs:
            return

        # Clear by deleting and re-creating the collection.
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:  # noqa: BLE001 — may not exist on first run
            pass
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._doc_map = {d.doc_id: d for d in docs}

        ids = [_safe_id(d.doc_id) for d in docs]
        texts = [d.text for d in docs]
        metas = [{"doc_id": d.doc_id, "tags": ",".join(d.tags)} for d in docs]
        # Chroma limits a single add() call to 41 666 docs; chunk if needed.
        batch = 500
        for i in range(0, len(docs), batch):
            self._collection.add(
                ids=ids[i : i + batch],
                documents=texts[i : i + batch],
                metadatas=metas[i : i + batch],
            )
        log.info(
            "ChromaBackend: indexed %d documents into collection '%s'.",
            len(docs),
            self._collection_name,
        )

    def query(self, query: str, tags: Iterable[str], k: int) -> list[KnowledgeHit]:
        if self._collection.count() == 0:
            return []
        tag_list = list(tags)
        n_results = min(k * 3, max(self._collection.count(), 1))
        result = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["distances", "documents", "metadatas"],
        )

        # Merge dense distance with tag-exact-match boost; normalise to [0,1].
        hits: list[KnowledgeHit] = []
        distances = result["distances"][0]
        metadatas = result["metadatas"][0]
        documents = result["documents"][0]
        for dist, meta, doc_text in zip(distances, metadatas, documents):
            # cosine distance ∈ [0,2]; convert to similarity [0,1]
            similarity = max(0.0, 1.0 - dist / 2.0)
            doc_tags = [t for t in meta.get("tags", "").split(",") if t]
            boost = 1.0 + sum(0.2 for t in tag_list if t in doc_tags)
            score = similarity * boost
            hits.append(
                KnowledgeHit(
                    doc_id=meta.get("doc_id", "?"),
                    text=doc_text[:500],
                    score=round(score, 4),
                    tags=doc_tags,
                )
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]


def _safe_id(s: str) -> str:
    """Chroma requires IDs that don't contain slashes; use a stable hash."""
    return hashlib.sha1(s.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# KnowledgeService (owns file I/O; delegates scoring to backend)
# --------------------------------------------------------------------------- #
class KnowledgeService:
    """Walk ``root`` for Markdown files and forward retrieval to a backend.

    The ``backend`` is injected at construction, so both the BoW and the
    Chroma path produce an identical public API.
    """

    def __init__(self, root: Path, *, backend: _Backend | None = None) -> None:
        self._root = Path(root)
        self._backend: _Backend = backend or BowBackend()
        self._docs: list[_Document] = []
        self.reindex()

    @property
    def backend_name(self) -> str:
        return self._backend.name

    def reindex(self) -> None:
        self._docs.clear()
        if not self._root.exists():
            log.info(
                "KnowledgeService root %s does not exist; index will be empty.",
                self._root,
            )
            self._backend.index([])
            return
        for md in sorted(self._root.rglob("*.md")):
            try:
                text = md.read_text("utf-8")
            except OSError as exc:
                log.warning("Cannot read %s: %s", md, exc)
                continue
            tags = _parse_tags(text)
            self._docs.append(
                _Document(
                    doc_id=str(md.relative_to(self._root)),
                    text=text,
                    tags=tags,
                )
            )
        self._backend.index(self._docs)
        log.info(
            "KnowledgeService: reindexed %d files via %s backend.",
            len(self._docs),
            self._backend.name,
        )

    def retrieve(
        self,
        *,
        query: str,
        tags: Iterable[str] = (),
        k: int = 4,
    ) -> list[KnowledgeHit]:
        return self._backend.query(query, tags, k)

    def __len__(self) -> int:
        return len(self._docs)


def _parse_tags(text: str) -> list[str]:
    """Extract a ``tags: a, b, c`` line from the first 10 lines."""
    for line in text.splitlines()[:10]:
        if line.lower().startswith("tags:"):
            return [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]
    return []


# --------------------------------------------------------------------------- #
# Smart factory
# --------------------------------------------------------------------------- #
def _chroma_available() -> bool:
    try:
        import chromadb  # noqa: F401
        from chromadb.utils.embedding_functions import (  # noqa: F401
            SentenceTransformerEmbeddingFunction,
        )
        return True
    except Exception:  # noqa: BLE001
        return False


def build_knowledge_service(
    root: Path,
    *,
    persist_directory: str | None = None,
    embedding_model: str = "all-MiniLM-L6-v2",
    force_bow: bool = False,
) -> KnowledgeService:
    """Auto-select backend and return a ready-to-use KnowledgeService.

    Parameters
    ----------
    root
        Directory of Markdown courseware files.
    persist_directory
        Where Chroma stores its data.  Defaults to ``<root>/.chroma``.
        Pass ``None`` to use an in-memory (non-persistent) collection;
        useful for tests and ephemeral containers.
    embedding_model
        sentence-transformers model name.
    force_bow
        Set to ``True`` to skip Chroma even when it is installed
        (useful for offline tests without GPU/network).
    """
    if not force_bow and _chroma_available():
        persist_dir = persist_directory or str(Path(root) / ".chroma")
        backend: _Backend = ChromaBackend(
            persist_directory=persist_dir,
            embedding_model=embedding_model,
        )
        log.info(
            "KnowledgeService: using ChromaDB backend "
            "(persist=%s, model=%s).",
            persist_dir,
            embedding_model,
        )
    else:
        backend = BowBackend()
        if not force_bow:
            log.info(
                "KnowledgeService: chromadb/sentence-transformers not "
                "installed; falling back to BoW backend."
            )
    return KnowledgeService(root=root, backend=backend)
