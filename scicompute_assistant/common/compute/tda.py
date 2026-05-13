"""TDA computation bridge.

Hardenings vs. the v0.1 prototype
---------------------------------
* **Operator registry** (Strategy + Registry pattern) replaces the
  if/elif cascade on ``pipeline``. Adding a new operator is a one-file change.
* **Vectorised Betti curves** – the previous nested Python loop is replaced
  with a single broadcasting expression that is O(n_points × n_bins) in
  C, not in the Python interpreter.
* **NaN / Inf hardening** – points with non-finite birth/death are dropped
  with a warning instead of poisoning Plotly.
* **Standardisation & min_persistence** – the request can ask for
  z-score normalisation (helps when features live on different scales) and
  for filtering noise features below a threshold.
* **Automatic ``max_edge_length``** – if the caller leaves it at the
  protocol default, we estimate it from the point-cloud diameter so the
  pipeline doesn't silently miss large H1/H2 features.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from ..protocols.tda_payload import (
    BettiCurve,
    PersistenceDiagramPayload,
    PersistencePoint,
    TDARequest,
    TDAResponse,
)
from .operators import (
    Operator,
    OperatorDescriptor,
    get_operator,
    is_registered,
    list_operators,
    register_operator,
)

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Helper: giotto-tda detection (cached)
# --------------------------------------------------------------------------- #
def _try_import_giotto() -> Any:
    try:
        from gtda import homology  # type: ignore
        return homology
    except Exception:  # noqa: BLE001
        return None


_GIOTTO = _try_import_giotto()


def _is_giotto_available() -> bool:
    return _GIOTTO is not None


# --------------------------------------------------------------------------- #
# Operator implementations
# --------------------------------------------------------------------------- #
@dataclass
class _PersistenceResult:
    """Internal envelope returned by all operators."""

    diagram: np.ndarray  # shape (n_features, 3): birth, death, dim
    warnings: list[str]


class _GiottoVietorisRips(Operator):
    operator_id = "vietoris_rips"

    def descriptor(self) -> OperatorDescriptor:
        return OperatorDescriptor(
            operator_id=self.operator_id,
            title="Vietoris–Rips Persistence",
            description="Standard filtration on a metric point cloud; supports H0-H2.",
            params_schema={
                "max_dimension": {"type": "integer", "default": 2, "min": 0, "max": 3},
                "max_edge_length": {"type": "number", "default": 1.0, "min": 0.0},
            },
            output_homology_dims=[0, 1, 2],
        )

    def run(self, points: np.ndarray, params: dict[str, Any]) -> _PersistenceResult:
        warnings: list[str] = []
        if _is_giotto_available():
            from gtda import homology
            dims = tuple(range(params.get("max_dimension", 2) + 1))
            vr = homology.VietorisRipsPersistence(
                homology_dimensions=dims,
                max_edge_length=params["max_edge_length"],
            )
            diag = np.asarray(vr.fit_transform([points])[0])
            return _PersistenceResult(diagram=diag, warnings=warnings)
        warnings.append("giotto-tda not installed; using NumPy MST fallback (H0 only).")
        return _PersistenceResult(diagram=_mst_h0(points, params["max_edge_length"]),
                                  warnings=warnings)


class _GiottoAlpha(Operator):
    operator_id = "alpha"

    def descriptor(self) -> OperatorDescriptor:
        return OperatorDescriptor(
            operator_id=self.operator_id,
            title="Alpha / Weak Alpha Persistence",
            description="Tighter complex for low-dimensional Euclidean data.",
            params_schema={
                "max_dimension": {"type": "integer", "default": 2, "min": 0, "max": 3},
                "max_edge_length": {"type": "number", "default": 1.0, "min": 0.0},
            },
            output_homology_dims=[0, 1, 2],
        )

    def run(self, points: np.ndarray, params: dict[str, Any]) -> _PersistenceResult:
        warnings: list[str] = []
        if _is_giotto_available():
            from gtda import homology
            dims = tuple(range(params.get("max_dimension", 2) + 1))
            wa = homology.WeakAlphaPersistence(
                homology_dimensions=dims,
                max_edge_length=params["max_edge_length"],
            )
            diag = np.asarray(wa.fit_transform([points])[0])
            return _PersistenceResult(diagram=diag, warnings=warnings)
        warnings.append("giotto-tda not installed; falling back to MST (H0 only).")
        return _PersistenceResult(diagram=_mst_h0(points, params["max_edge_length"]),
                                  warnings=warnings)


class _NumpyMST(Operator):
    """Pure-NumPy/SciPy fallback. Useful as an explicit operator for teaching."""

    operator_id = "mst_h0"

    def descriptor(self) -> OperatorDescriptor:
        return OperatorDescriptor(
            operator_id=self.operator_id,
            title="MST H0 (NumPy fallback)",
            description="Single-linkage H0 via minimum spanning tree; no extra deps.",
            params_schema={
                "max_edge_length": {"type": "number", "default": 1.0, "min": 0.0},
            },
            output_homology_dims=[0],
        )

    def run(self, points: np.ndarray, params: dict[str, Any]) -> _PersistenceResult:
        return _PersistenceResult(
            diagram=_mst_h0(points, params["max_edge_length"]),
            warnings=[],
        )


def _mst_h0(points: np.ndarray, max_edge_length: float) -> np.ndarray:
    """Vectorised MST-based H0 persistence.

    Returns a (k, 3) ndarray (birth, death, dim=0). We allocate the output
    in a single ``np.column_stack`` call – no Python list-of-lists.
    """
    from scipy.sparse.csgraph import minimum_spanning_tree
    from scipy.spatial.distance import pdist, squareform

    if points.shape[0] < 2:
        return np.zeros((0, 3), dtype=np.float64)

    d = squareform(pdist(points))
    mst = minimum_spanning_tree(d).toarray()
    lengths = mst[mst > 0]
    lengths.sort()
    lengths = lengths[lengths <= max_edge_length]

    births = np.zeros_like(lengths)
    dims = np.zeros_like(lengths, dtype=np.float64)
    finite = np.column_stack([births, lengths, dims])
    inf_row = np.array([[0.0, float(max_edge_length), 0.0]])
    return np.vstack([finite, inf_row])


# --------------------------------------------------------------------------- #
# Auto-registration
# --------------------------------------------------------------------------- #
def _ensure_default_operators() -> None:
    """Idempotently register the three built-in operators."""
    for op_cls in (_GiottoVietorisRips, _GiottoAlpha, _NumpyMST):
        if not is_registered(op_cls.operator_id):
            register_operator(op_cls())


_ensure_default_operators()


# --------------------------------------------------------------------------- #
# Engine façade
# --------------------------------------------------------------------------- #
class TDAEngine:
    """Façade that the FastAPI route layer talks to."""

    def __init__(self) -> None:
        _ensure_default_operators()

    @property
    def is_available(self) -> bool:
        return _is_giotto_available()

    def list_operators(self) -> list[OperatorDescriptor]:
        return list_operators()

    # ------------------------------------------------------------------ #
    def compute(self, req: TDARequest) -> TDAResponse:
        if req.data is None:
            raise ValueError(
                "TDAEngine.compute requires `data` to be populated."
            )
        if len(req.data) == 0:
            X_raw = np.zeros((0, 0), dtype=np.float64)
        else:
            X_raw = np.asarray(req.data, dtype=np.float64)
            if X_raw.ndim != 2:
                raise ValueError(f"Expected a 2-D point cloud, got shape {X_raw.shape}.")

        warnings: list[str] = []
        X, std_warnings = _sanitize_point_cloud(X_raw, standardize=req.standardize)
        warnings.extend(std_warnings)
        if X.shape[0] == 0:
            return TDAResponse(
                diagram=PersistenceDiagramPayload(
                    points=[], max_filtration=0.0, axis_limits=(0.0, 1.0)
                ),
                elapsed_ms=0.0,
                backend="empty",
                warnings=warnings or ["Point cloud was empty after sanitisation."],
            )

        # Auto-scale max_edge_length if the caller relied on the default.
        max_edge = req.max_edge_length
        if req.auto_max_edge_length or max_edge <= 0.0:
            max_edge = _suggest_max_edge(X)
            warnings.append(
                f"max_edge_length auto-set to {max_edge:.4f} (cloud diameter heuristic)."
            )

        operator_id = req.operator or req.pipeline
        try:
            op = get_operator(operator_id)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc

        # Defaults from the protocol level are overridden by request-level
        # ``params``; operator-specific schema then fills any remaining gaps
        # and rejects malformed values *before* the call hits NumPy.
        merged_params: dict[str, Any] = {
            "max_dimension": req.max_dimension,
            "max_edge_length": max_edge,
            **(req.params or {}),
        }
        params = op.descriptor().validate_params(merged_params)

        t0 = time.perf_counter()
        result = op.run(X, params)
        elapsed = (time.perf_counter() - t0) * 1000
        warnings.extend(result.warnings)

        backend = "giotto-tda" if (_is_giotto_available() and operator_id != "mst_h0") else "numpy-fallback"
        if operator_id == "mst_h0":
            backend = "numpy-mst"

        payload = _diagram_to_payload(
            result.diagram, X_raw, req, max_filtration_fallback=max_edge,
            warnings=warnings,
        )
        return TDAResponse(
            diagram=payload,
            elapsed_ms=elapsed,
            backend=backend,
            warnings=warnings,
        )


# --------------------------------------------------------------------------- #
# Point-cloud sanitisation
# --------------------------------------------------------------------------- #
def _sanitize_point_cloud(X: np.ndarray, *, standardize: bool) -> tuple[np.ndarray, list[str]]:
    warnings: list[str] = []
    mask = np.isfinite(X).all(axis=1)
    dropped = int((~mask).sum())
    if dropped:
        warnings.append(f"Dropped {dropped} non-finite rows from the input cloud.")
        X = X[mask]
    if X.shape[0] == 0:
        return X, warnings
    if standardize:
        mu = X.mean(axis=0, keepdims=True)
        sigma = X.std(axis=0, keepdims=True)
        # Avoid division by zero for degenerate axes (constant columns).
        sigma = np.where(sigma < 1e-12, 1.0, sigma)
        X = (X - mu) / sigma
        warnings.append("Applied z-score standardisation before filtration.")
    return np.ascontiguousarray(X, dtype=np.float64), warnings


def _suggest_max_edge(X: np.ndarray) -> float:
    """A robust diameter estimate: 90th-percentile pairwise distance.

    Computing the full pdist is O(n²); we cap to ``n=1024`` via uniform
    subsampling so this stays cheap even on big clouds.
    """
    from scipy.spatial.distance import pdist

    n = X.shape[0]
    if n > 1024:
        idx = np.linspace(0, n - 1, 1024).astype(np.int64)
        sample = X[idx]
    else:
        sample = X
    if sample.shape[0] < 2:
        return 1.0
    d = pdist(sample)
    if d.size == 0:
        return 1.0
    return float(max(np.percentile(d, 90), 1e-6))


# --------------------------------------------------------------------------- #
# Diagram → wire format (fully vectorised)
# --------------------------------------------------------------------------- #
def _diagram_to_payload(
    diagrams: np.ndarray,
    X: np.ndarray,
    req: TDARequest,
    *,
    max_filtration_fallback: float,
    warnings: list[str],
) -> PersistenceDiagramPayload:
    if diagrams.size == 0:
        return PersistenceDiagramPayload(
            points=[],
            max_filtration=max_filtration_fallback,
            axis_limits=(0.0, max_filtration_fallback),
        )

    births = diagrams[:, 0].astype(np.float64, copy=False)
    deaths = diagrams[:, 1].astype(np.float64, copy=False)
    dims = diagrams[:, 2].astype(np.int64, copy=False)

    finite_mask = np.isfinite(births) & np.isfinite(deaths)
    dropped = int((~finite_mask).sum())
    if dropped:
        warnings.append(f"Filtered {dropped} non-finite persistence rows.")
        births, deaths, dims = births[finite_mask], deaths[finite_mask], dims[finite_mask]

    persistence = np.maximum(deaths - births, 0.0)

    if req.min_persistence is not None and req.min_persistence > 0:
        keep = persistence >= req.min_persistence
        dropped_noise = int((~keep).sum())
        if dropped_noise:
            warnings.append(
                f"Dropped {dropped_noise} low-persistence features "
                f"(< {req.min_persistence})."
            )
        births, deaths, dims, persistence = (
            births[keep], deaths[keep], dims[keep], persistence[keep]
        )

    max_filt = float(deaths.max()) if deaths.size else max_filtration_fallback
    if max_filt <= 0:
        max_filt = max_filtration_fallback
    axis_lo = 0.0
    axis_hi = max(max_filt, max_filtration_fallback)
    points: list[PersistencePoint] = [
        PersistencePoint(
            birth=float(b),
            death=float(d),
            dimension=int(k),
            persistence=float(p),
        )
        for b, d, k, p in zip(births, deaths, dims, persistence)
    ]
    betti = _betti_curves_vectorised(
        births=births, deaths=deaths, dims=dims, n_bins=req.n_bins, t_max=axis_hi
    )
    preview = _downsample_preview(X, req.downsample_preview)
    return PersistenceDiagramPayload(
        points=points,
        max_filtration=max_filt,
        axis_limits=(axis_lo, axis_hi),
        betti_curves=betti,
        point_cloud_preview=preview,
    )


def _betti_curves_vectorised(
    *,
    births: np.ndarray,
    deaths: np.ndarray,
    dims: np.ndarray,
    n_bins: int,
    t_max: float,
) -> list[BettiCurve]:
    """Compute B_d(t) for every dimension on a shared grid with broadcasting.

    Implementation: for each homology dimension we use a single 2D-broadcast
    comparison ``(grid[:, None] >= births) & (grid[:, None] < deaths)`` and
    reduce along the feature axis. The previous loop was O(n_dim × n_pts ×
    n_bins) in the Python interpreter; this is O(n_pts × n_bins) in C.
    """
    if t_max <= 0 or births.size == 0:
        return []
    grid = np.linspace(0.0, t_max, n_bins, dtype=np.float64)
    out: list[BettiCurve] = []
    for d in np.unique(dims):
        sel = dims == d
        b = births[sel][None, :]  # shape (1, k)
        e = deaths[sel][None, :]
        g = grid[:, None]
        counts = ((g >= b) & (g < e)).sum(axis=1).astype(np.int64)
        out.append(
            BettiCurve(
                dimension=int(d),
                filtration=grid.tolist(),
                values=counts.tolist(),
            )
        )
    return out


def _downsample_preview(X: np.ndarray, cap: int) -> list[list[float]] | None:
    if cap <= 0 or X.shape[0] == 0:
        return None
    k = min(cap, X.shape[0])
    idx = np.linspace(0, X.shape[0] - 1, k).astype(np.int64)
    # ``tolist()`` already copies into Python lists, so doing the slice
    # via fancy indexing is one fewer ndarray allocation than the previous
    # ``X[idx].astype(float).tolist()``.
    return X[idx].tolist()
