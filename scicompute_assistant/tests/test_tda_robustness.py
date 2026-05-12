"""Edge-case tests for the TDA engine: NaN handling, vectorisation, registry."""

from __future__ import annotations

import math

import numpy as np
import pytest

from scicompute_assistant.common.compute import TDAEngine
from scicompute_assistant.common.compute.operators import (
    Operator,
    OperatorDescriptor,
    is_registered,
    list_operators,
    register_operator,
)
from scicompute_assistant.common.compute.tda import _betti_curves_vectorised
from scicompute_assistant.common.protocols.tda_payload import TDARequest


# --------------------------------------------------------------------------- #
# Registry – extensibility (Open/Closed)
# --------------------------------------------------------------------------- #
class _FakeOp(Operator):
    operator_id = "_test_fake_op"

    def descriptor(self) -> OperatorDescriptor:
        return OperatorDescriptor(
            operator_id=self.operator_id,
            title="Fake",
            description="returns 1 H0 point.",
            params_schema={},
        )

    def run(self, points, params):  # noqa: ANN001
        from scicompute_assistant.common.compute.tda import _PersistenceResult

        return _PersistenceResult(
            diagram=np.array([[0.0, 0.5, 0]], dtype=np.float64),
            warnings=[],
        )


def test_registry_pickup_new_operator():
    if not is_registered("_test_fake_op"):
        register_operator(_FakeOp())
    descriptors = {d.operator_id for d in list_operators()}
    assert "_test_fake_op" in descriptors

    engine = TDAEngine()
    resp = engine.compute(TDARequest(
        data=[[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
        operator="_test_fake_op",
        max_edge_length=1.0,
    ))
    assert resp.diagram.points[0].dimension == 0
    assert resp.diagram.points[0].death == pytest.approx(0.5)


def test_registry_unknown_operator_raises():
    engine = TDAEngine()
    with pytest.raises(ValueError, match="Unknown operator"):
        engine.compute(TDARequest(
            data=[[0.0, 0.0], [1.0, 0.0]],
            operator="does_not_exist",
            max_edge_length=1.0,
        ))


# --------------------------------------------------------------------------- #
# Vectorised Betti curves match the original loop version
# --------------------------------------------------------------------------- #
def _loop_betti(births, deaths, dims, n_bins, t_max):
    """Reference (slow) implementation against which we compare."""
    if t_max <= 0 or births.size == 0:
        return {}
    grid = np.linspace(0.0, t_max, n_bins)
    out = {}
    for d in np.unique(dims):
        sel = dims == d
        b = births[sel]
        e = deaths[sel]
        counts = np.zeros_like(grid, dtype=int)
        for bi, ei in zip(b, e):
            counts += ((grid >= bi) & (grid < ei)).astype(int)
        out[int(d)] = counts.tolist()
    return out


def test_vectorised_betti_matches_loop_implementation():
    rng = np.random.default_rng(0)
    births = rng.uniform(0, 0.5, size=40)
    deaths = births + rng.uniform(0.01, 1.0, size=40)
    dims = rng.integers(0, 3, size=40)
    n_bins = 64
    t_max = float(deaths.max())

    fast = _betti_curves_vectorised(
        births=births, deaths=deaths, dims=dims, n_bins=n_bins, t_max=t_max
    )
    slow = _loop_betti(births, deaths, dims, n_bins, t_max)

    fast_map = {c.dimension: c.values for c in fast}
    assert fast_map == slow


# --------------------------------------------------------------------------- #
# NaN / Inf robustness
# --------------------------------------------------------------------------- #
def test_tda_drops_nonfinite_input_rows():
    engine = TDAEngine()
    cloud = [[0.0, 0.0], [1.0, 0.0], [float("nan"), 1.0], [float("inf"), 2.0]]
    resp = engine.compute(TDARequest(data=cloud, max_edge_length=2.0))
    assert any("non-finite rows" in w for w in resp.warnings)


def test_tda_min_persistence_filters_noise():
    engine = TDAEngine()
    # 5-point line; MST H0 yields 4 finite features at ~unit length + 1 cap.
    cloud = [[i, 0.0] for i in range(5)]
    resp_all = engine.compute(TDARequest(
        data=cloud, operator="mst_h0", max_edge_length=10.0))
    resp_filt = engine.compute(TDARequest(
        data=cloud, operator="mst_h0", max_edge_length=10.0, min_persistence=2.0))
    assert len(resp_filt.diagram.points) < len(resp_all.diagram.points)
    assert any("low-persistence" in w for w in resp_filt.warnings)


def test_tda_standardize_emits_warning():
    engine = TDAEngine()
    cloud = [[0.0, 100.0], [1.0, 200.0], [2.0, 300.0]]
    resp = engine.compute(TDARequest(
        data=cloud, operator="mst_h0", standardize=True, max_edge_length=10.0))
    assert any("standardisation" in w for w in resp.warnings)


def test_tda_auto_max_edge_length_kicks_in():
    engine = TDAEngine()
    cloud = [[i * 100.0, 0.0] for i in range(10)]
    resp = engine.compute(TDARequest(
        data=cloud, operator="mst_h0", auto_max_edge_length=True, max_edge_length=0.0))
    assert any("auto-set" in w for w in resp.warnings)
    # MST features should appear because the auto edge length is large enough.
    assert len(resp.diagram.points) > 1


def test_tda_handles_empty_input_gracefully():
    engine = TDAEngine()
    resp = engine.compute(TDARequest(data=[], operator="mst_h0", max_edge_length=1.0))
    assert resp.diagram.points == []


def test_tda_single_point_does_not_crash():
    engine = TDAEngine()
    resp = engine.compute(TDARequest(
        data=[[0.0, 0.0]], operator="mst_h0", max_edge_length=1.0))
    # No edges → no finite features, only the infinite component capped.
    assert len(resp.diagram.points) <= 1


# --------------------------------------------------------------------------- #
# Sandbox NaN / Inf scrubbing
# --------------------------------------------------------------------------- #
def test_sandbox_replaces_nan_with_none():
    from scicompute_assistant.common.compute import ComputeKernel

    k = ComputeKernel(timeout_sec=2)
    res = k.run_code("result = {'a': 1.0, 'b': float('nan'), 'c': [1.0, float('inf')]}")
    assert res.ok
    assert res.result["a"] == 1.0
    assert res.result["b"] is None
    assert res.result["c"] == [1.0, None]
    assert "b" in "\n".join(res.nonfinite_keys)
    assert any("c[1]" in k for k in res.nonfinite_keys)
