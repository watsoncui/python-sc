"""Tests for the dual-backend KnowledgeService.

Covers:
    - BoW backend: retrieval, tag boost, reindex.
    - ChromaDB backend: round-trip indexing + dense retrieval.
    - build_knowledge_service auto-selection.
    - Config nesting: KnowledgeConfig picks force_bow=True in CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scicompute_assistant.common.knowledge import (
    BowBackend,
    KnowledgeService,
    build_knowledge_service,
)
from scicompute_assistant.common.knowledge.service import (
    ChromaBackend,
    _chroma_available,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _write_md(path: Path, name: str, tags: str, body: str) -> Path:
    f = path / name
    f.write_text(f"tags: {tags}\n{body}", encoding="utf-8")
    return f


# --------------------------------------------------------------------------- #
# BoW backend
# --------------------------------------------------------------------------- #
class TestBowBackend:
    def test_basic_retrieval(self, tmp_path):
        _write_md(tmp_path, "a.md", "numpy, week:3", "NumPy 广播 broadcasting ufunc")
        _write_md(tmp_path, "b.md", "scipy, week:4", "SciPy linear algebra linalg")
        svc = KnowledgeService(root=tmp_path, backend=BowBackend())
        hits = svc.retrieve(query="NumPy 广播", k=5)
        assert hits and hits[0].doc_id == "a.md"

    def test_tag_boost_promotes_matching_doc(self, tmp_path):
        _write_md(tmp_path, "a.md", "week:3", "NumPy ufunc broadcasting")
        _write_md(tmp_path, "b.md", "week:5", "NumPy ufunc broadcasting")
        svc = KnowledgeService(root=tmp_path, backend=BowBackend())
        hits = svc.retrieve(query="NumPy ufunc", tags=["week:3"], k=2)
        assert hits[0].doc_id == "a.md"

    def test_empty_root_returns_nothing(self, tmp_path):
        svc = KnowledgeService(root=tmp_path, backend=BowBackend())
        assert svc.retrieve(query="anything") == []

    def test_reindex_picks_up_new_file(self, tmp_path):
        svc = KnowledgeService(root=tmp_path, backend=BowBackend())
        assert len(svc) == 0
        _write_md(tmp_path, "new.md", "numpy", "NumPy vectorization")
        svc.reindex()
        assert len(svc) == 1
        hits = svc.retrieve(query="NumPy vectorization")
        assert hits and hits[0].doc_id == "new.md"

    def test_nonexistent_root_does_not_raise(self):
        svc = KnowledgeService(root=Path("/no/such/path"), backend=BowBackend())
        assert svc.retrieve(query="x") == []


# --------------------------------------------------------------------------- #
# ChromaDB backend
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not _chroma_available(), reason="chromadb not installed")
class TestChromaBackend:
    def test_chroma_indexes_and_retrieves(self, tmp_path):
        _write_md(tmp_path, "np.md", "numpy, week:3", "NumPy 广播 broadcasting ufunc slicing")
        _write_md(tmp_path, "sp.md", "scipy, week:4", "SciPy 稀疏矩阵 sparse matrix linear")
        backend = ChromaBackend(persist_directory=None)  # in-memory
        svc = KnowledgeService(root=tmp_path, backend=backend)
        hits = svc.retrieve(query="NumPy broadcasting", k=2)
        assert hits, "expected at least one hit"
        top_ids = [h.doc_id for h in hits]
        assert "np.md" in top_ids

    def test_chroma_tag_boost(self, tmp_path):
        for i in range(5):
            _write_md(tmp_path, f"w{i}.md", f"week:{i}", f"NumPy week {i} content broadcasting")
        backend = ChromaBackend(persist_directory=None)
        svc = KnowledgeService(root=tmp_path, backend=backend)
        hits = svc.retrieve(query="NumPy broadcasting", tags=["week:2"], k=3)
        assert hits, "expected hits"
        assert hits[0].doc_id == "w2.md"

    def test_chroma_reindex_clears_stale_docs(self, tmp_path):
        _write_md(tmp_path, "old.md", "numpy", "NumPy old content")
        backend = ChromaBackend(persist_directory=None)
        svc = KnowledgeService(root=tmp_path, backend=backend)
        (tmp_path / "old.md").unlink()
        _write_md(tmp_path, "new.md", "scipy", "SciPy fresh content linalg")
        svc.reindex()
        hits = svc.retrieve(query="linalg fresh")
        doc_ids = [h.doc_id for h in hits]
        assert "old.md" not in doc_ids
        assert "new.md" in doc_ids


# --------------------------------------------------------------------------- #
# Auto-selection factory
# --------------------------------------------------------------------------- #
def test_build_knowledge_service_force_bow(tmp_path):
    """force_bow=True must return BoW even when chromadb is installed."""
    _write_md(tmp_path, "a.md", "numpy", "NumPy broadcasting")
    svc = build_knowledge_service(root=tmp_path, force_bow=True)
    assert svc.backend_name == "bow"
    hits = svc.retrieve(query="NumPy")
    assert hits


@pytest.mark.skipif(not _chroma_available(), reason="chromadb not installed")
def test_build_knowledge_service_picks_chroma_when_available(tmp_path):
    _write_md(tmp_path, "a.md", "numpy", "NumPy broadcasting")
    svc = build_knowledge_service(
        root=tmp_path,
        persist_directory=str(tmp_path / ".chroma"),
        force_bow=False,
    )
    assert svc.backend_name == "chroma"


# --------------------------------------------------------------------------- #
# Config integration: SCICOMP_KNOWLEDGE__FORCE_BOW env var
# --------------------------------------------------------------------------- #
def test_knowledge_config_force_bow_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SCICOMP_KNOWLEDGE__FORCE_BOW", "true")
    monkeypatch.setenv("SCICOMP_COURSEWARE_ROOT", str(tmp_path))
    _write_md(tmp_path, "c.md", "tda", "TDA homology persistence")

    # Reset the singleton cache
    from scicompute_assistant.server import dependencies
    for fn in (
        dependencies.get_settings,
        dependencies.get_knowledge_service,
    ):
        fn.cache_clear()

    svc = dependencies.get_knowledge_service()
    assert svc.backend_name == "bow"
    hits = svc.retrieve(query="homology persistence")
    assert hits
