"""Performance baselines using pytest-benchmark.

Run:
    pytest scicompute_assistant/tests/test_benchmarks.py -v --benchmark-sort=mean

These tests are NOT run in the standard CI test suite (they require
``--benchmark-enable`` or they are run as a separate step) but can be
triggered locally or in a dedicated GitHub Actions job.  The numbers are
stored as JSON via ``--benchmark-autosave`` and compared with
``--benchmark-compare`` on subsequent runs.

Baselines (AMD Epyc-class, single-core, pure Python 3.12):
    betti_curves_100pts  < 5 ms
    tda_mst_200pts       < 150 ms
    sandbox_run_basic    < 50 ms
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
import pytest

from scicompute_assistant.common.compute import ComputeKernel, TDAEngine
from scicompute_assistant.common.compute.tda import _betti_curves_vectorised
from scicompute_assistant.common.knowledge import KnowledgeService
from scicompute_assistant.common.knowledge.service import BowBackend
from scicompute_assistant.common.protocols.tda_payload import TDARequest


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _make_random_diagram(n: int, max_dim: int = 2, seed: int = 0) -> tuple:
    rng = np.random.default_rng(seed)
    births = rng.uniform(0, 0.5, size=n)
    deaths = births + rng.uniform(0.01, 1.0, size=n)
    dims = rng.integers(0, max_dim + 1, size=n)
    return births, deaths, dims


def _make_circle(n: int, noise: float = 0.02, seed: int = 7) -> list[list[float]]:
    random.seed(seed)
    return [
        [
            math.cos(2 * math.pi * i / n) + random.gauss(0, noise),
            math.sin(2 * math.pi * i / n) + random.gauss(0, noise),
        ]
        for i in range(n)
    ]


def _build_bow_service(tmp_path: Path, n_docs: int = 30) -> KnowledgeService:
    for i in range(n_docs):
        f = tmp_path / f"week{i:02d}.md"
        f.write_text(
            f"tags: week:{i}, numpy\n"
            f"# Week {i}\n"
            f"NumPy vectorisation broadcasting ufunc {' '.join(str(j) for j in range(20))}\n",
            encoding="utf-8",
        )
    return KnowledgeService(root=tmp_path, backend=BowBackend())


# --------------------------------------------------------------------------- #
# Betti curve vectorisation
# --------------------------------------------------------------------------- #
@pytest.mark.benchmark(group="betti")
def test_bench_betti_100pts(benchmark):
    births, deaths, dims = _make_random_diagram(100)
    t_max = float(deaths.max())
    benchmark(
        _betti_curves_vectorised,
        births=births,
        deaths=deaths,
        dims=dims,
        n_bins=100,
        t_max=t_max,
    )


@pytest.mark.benchmark(group="betti")
def test_bench_betti_1000pts(benchmark):
    births, deaths, dims = _make_random_diagram(1000)
    t_max = float(deaths.max())
    benchmark(
        _betti_curves_vectorised,
        births=births,
        deaths=deaths,
        dims=dims,
        n_bins=200,
        t_max=t_max,
    )


# --------------------------------------------------------------------------- #
# TDA end-to-end (MST fallback, no giotto-tda needed)
# --------------------------------------------------------------------------- #
@pytest.mark.benchmark(group="tda")
def test_bench_tda_mst_100pts(benchmark):
    engine = TDAEngine()
    cloud = _make_circle(100)
    req = TDARequest(data=cloud, operator="mst_h0", max_edge_length=1.5, n_bins=50)
    benchmark(engine.compute, req)


@pytest.mark.benchmark(group="tda")
def test_bench_tda_mst_500pts(benchmark):
    engine = TDAEngine()
    cloud = _make_circle(500)
    req = TDARequest(data=cloud, operator="mst_h0", max_edge_length=1.5, n_bins=100)
    benchmark(engine.compute, req)


# --------------------------------------------------------------------------- #
# Sandbox execution
# --------------------------------------------------------------------------- #
@pytest.mark.benchmark(group="sandbox")
def test_bench_sandbox_numpy_mean(benchmark):
    kernel = ComputeKernel(timeout_sec=5.0)
    code = (
        "import numpy as np\n"
        "arr = np.arange(10_000, dtype=np.float64)\n"
        "result = {'mean': float(arr.mean())}\n"
    )
    benchmark(kernel.run_code, code)


@pytest.mark.benchmark(group="sandbox")
def test_bench_sandbox_pure_python(benchmark):
    """Pure Python loop – shows the floor without NumPy."""
    kernel = ComputeKernel(timeout_sec=5.0)
    code = (
        "total = 0\n"
        "for i in range(1_000):\n"
        "    total += i\n"
        "result = {'total': total}\n"
    )
    benchmark(kernel.run_code, code)


# --------------------------------------------------------------------------- #
# KnowledgeService BoW retrieval
# --------------------------------------------------------------------------- #
@pytest.mark.benchmark(group="knowledge")
def test_bench_knowledge_bow_30docs(benchmark, tmp_path):
    svc = _build_bow_service(tmp_path, n_docs=30)
    benchmark(svc.retrieve, query="NumPy 广播 vectorisation", tags=["week:3"], k=4)
