"""TDA computation bridge.

Encapsulates giotto-tda's persistent-homology pipelines and converts the
results into :class:`PersistenceDiagramPayload` instances suitable for
Plotly rendering on the front-end.

When ``giotto-tda`` is not installed (e.g. server image without the optional
dependency), :class:`TDAEngine.is_available` returns ``False`` and routes
should fall back to a clear error message instead of crashing.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

from ..protocols.tda_payload import (
    BettiCurve,
    PersistenceDiagramPayload,
    PersistencePoint,
    TDARequest,
    TDAResponse,
)

log = logging.getLogger(__name__)


def _try_import_giotto() -> Any:
    try:
        from gtda import homology  # type: ignore
        return homology
    except Exception:  # noqa: BLE001 - optional dep
        return None


class TDAEngine:
    """Thin wrapper around giotto-tda primitives, with a NumPy fallback."""

    def __init__(self) -> None:
        self._gtda = _try_import_giotto()

    # ------------------------------------------------------------------ #
    @property
    def is_available(self) -> bool:
        return self._gtda is not None

    # ------------------------------------------------------------------ #
    def compute(self, req: TDARequest) -> TDAResponse:
        if req.data is None:
            raise ValueError(
                "TDAEngine.compute requires `data` to be populated; "
                "use `compute_kernel.run_code` first if your input is a code snippet."
            )

        t0 = time.perf_counter()
        X, warnings = self._sanitize_point_cloud(req.data)
        if X.shape[0] == 0 or X.shape[1] == 0:
            elapsed = (time.perf_counter() - t0) * 1000
            payload = self._to_payload(np.empty((0, 3), dtype=np.float64), X, req)
            warnings.append("Point cloud is empty after validation; returned an empty diagram.")
            return TDAResponse(
                diagram=payload,
                elapsed_ms=elapsed,
                backend="giotto-tda" if self.is_available else "numpy-fallback",
                warnings=warnings,
            )

        backend = "numpy-fallback"
        if self.is_available and req.pipeline in ("vietoris_rips", "alpha"):
            try:
                diagrams = self._giotto_persistence(X, req)
                backend = "giotto-tda"
            except Exception as exc:  # noqa: BLE001 - optional backend must not crash API
                warnings.append(
                    "giotto-tda failed; using NumPy fallback "
                    f"(approximate, H0 only): {type(exc).__name__}."
                )
                diagrams = self._numpy_fallback(X, req)
        else:
            if not self.is_available:
                warnings.append(
                    "giotto-tda not installed; using NumPy fallback "
                    "(approximate, H0 only)."
                )
            diagrams = self._numpy_fallback(X, req)

        elapsed = (time.perf_counter() - t0) * 1000
        diagrams, diagram_warnings = self._sanitize_diagrams(diagrams, req)
        warnings.extend(diagram_warnings)
        payload = self._to_payload(diagrams, X, req)
        return TDAResponse(
            diagram=payload,
            elapsed_ms=elapsed,
            backend=backend,
            warnings=warnings,
        )

    # ------------------------------------------------------------------ #
    # Input validation and finite-value handling
    # ------------------------------------------------------------------ #
    @staticmethod
    def _sanitize_point_cloud(data: list[list[float]]) -> tuple[np.ndarray, list[str]]:
        warnings: list[str] = []
        try:
            X = np.asarray(data, dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise ValueError("Expected a rectangular 2-D point cloud of numeric values.") from exc

        if X.ndim == 1 and X.size == 0:
            return np.empty((0, 0), dtype=np.float64), warnings
        if X.ndim != 2:
            raise ValueError(f"Expected a 2-D point cloud, got shape {X.shape}.")

        if X.shape[0] == 0 or X.shape[1] == 0:
            return X.astype(np.float64, copy=False), warnings

        finite_rows = np.all(np.isfinite(X), axis=1)
        dropped = int(X.shape[0] - np.count_nonzero(finite_rows))
        if dropped:
            warnings.append(f"Dropped {dropped} point(s) containing NaN or infinite coordinates.")
            X = X[finite_rows]
        return X.astype(np.float64, copy=False), warnings

    @staticmethod
    def _sanitize_diagrams(diagrams: np.ndarray, req: TDARequest) -> tuple[np.ndarray, list[str]]:
        warnings: list[str] = []
        arr = np.asarray(diagrams, dtype=np.float64)
        if arr.size == 0:
            return np.empty((0, 3), dtype=np.float64), warnings
        arr = np.atleast_2d(arr)
        if arr.shape[1] < 3:
            warnings.append("Discarded malformed persistence diagram rows.")
            return np.empty((0, 3), dtype=np.float64), warnings
        arr = arr[:, :3].astype(np.float64, copy=True)

        finite_birth = np.isfinite(arr[:, 0])
        finite_dim = np.isfinite(arr[:, 2])
        valid = finite_birth & finite_dim
        dropped = int(arr.shape[0] - np.count_nonzero(valid))
        if dropped:
            warnings.append(f"Dropped {dropped} malformed persistence point(s).")
        arr = arr[valid]
        if arr.size == 0:
            return np.empty((0, 3), dtype=np.float64), warnings

        nonfinite_death = ~np.isfinite(arr[:, 1])
        if np.any(nonfinite_death):
            arr[nonfinite_death, 1] = float(req.max_edge_length)
            warnings.append("Capped non-finite death values at max_edge_length for Plotly.")
        arr[:, 1] = np.maximum(arr[:, 1], arr[:, 0])
        arr[:, 2] = np.clip(np.rint(arr[:, 2]), 0, req.max_dimension)
        return arr, warnings

    # ------------------------------------------------------------------ #
    # Giotto-tda path
    # ------------------------------------------------------------------ #
    def _giotto_persistence(self, X: np.ndarray, req: TDARequest) -> np.ndarray:
        from gtda import homology  # type: ignore

        if req.pipeline == "alpha":
            VR = homology.WeakAlphaPersistence(
                homology_dimensions=tuple(range(req.max_dimension + 1)),
                max_edge_length=req.max_edge_length,
            )
        else:
            VR = homology.VietorisRipsPersistence(
                homology_dimensions=tuple(range(req.max_dimension + 1)),
                max_edge_length=req.max_edge_length,
            )
        diagrams = VR.fit_transform([X])
        return np.asarray(diagrams[0])

    # ------------------------------------------------------------------ #
    # Numpy-only fallback (single-linkage H0 via MST)
    # ------------------------------------------------------------------ #
    def _numpy_fallback(self, X: np.ndarray, req: TDARequest) -> np.ndarray:
        from scipy.sparse.csgraph import minimum_spanning_tree
        from scipy.spatial.distance import squareform, pdist

        if X.shape[0] == 0 or X.shape[1] == 0:
            return np.empty((0, 3), dtype=np.float64)
        if X.shape[0] == 1:
            return np.asarray([[0.0, float(req.max_edge_length), 0.0]], dtype=np.float64)

        d = squareform(pdist(X))
        mst = minimum_spanning_tree(d).toarray()
        edge_lengths = np.sort(mst[mst > 0])
        edge_lengths = edge_lengths[edge_lengths <= req.max_edge_length]

        # H0: n-1 connected components born at 0, dying when the MST edge is added.
        rows: list[list[float]] = [[0.0, float(e), 0] for e in edge_lengths]
        # And one infinite component for the whole cloud.
        rows.append([0.0, float(req.max_edge_length), 0])
        return np.asarray(rows, dtype=np.float64)

    # ------------------------------------------------------------------ #
    # Conversion to the FE protocol
    # ------------------------------------------------------------------ #
    def _to_payload(
        self,
        diagrams: np.ndarray,
        X: np.ndarray,
        req: TDARequest,
    ) -> PersistenceDiagramPayload:
        points: list[PersistencePoint] = []
        for row in diagrams:
            birth, death, dim = float(row[0]), float(row[1]), int(row[2])
            points.append(
                PersistencePoint(
                    birth=birth,
                    death=death,
                    dimension=dim,
                    persistence=max(0.0, death - birth),
                )
            )
        max_filt = float(
            np.nanmax(np.where(np.isfinite(diagrams[:, 1]), diagrams[:, 1], 0.0))
            if diagrams.size
            else req.max_edge_length
        )
        axis_limits = (0.0, max(max_filt, req.max_edge_length))
        betti = self._betti_curves(points, n_bins=req.n_bins, t_max=axis_limits[1])
        traces = self._plotly_traces(points, axis_limits=axis_limits)

        preview: list[list[float]] | None = None
        if req.downsample_preview > 0 and X.shape[0] > 0:
            k = min(req.downsample_preview, X.shape[0])
            idx = np.linspace(0, X.shape[0] - 1, k).astype(int)
            preview = X[idx].astype(float).tolist()

        return PersistenceDiagramPayload(
            points=points,
            max_filtration=max_filt,
            plotly_traces=traces,
            axis_limits=axis_limits,
            betti_curves=betti,
            point_cloud_preview=preview,
        )

    @staticmethod
    def _betti_curves(
        points: list[PersistencePoint],
        *,
        n_bins: int,
        t_max: float,
    ) -> list[BettiCurve]:
        if t_max <= 0 or not points:
            return []
        grid = np.linspace(0.0, t_max, n_bins)
        by_dim: dict[int, list[PersistencePoint]] = {}
        for p in points:
            by_dim.setdefault(p.dimension, []).append(p)
        out: list[BettiCurve] = []
        for dim, pts in sorted(by_dim.items()):
            counts = np.zeros_like(grid, dtype=int)
            for p in pts:
                # alive on [birth, death)
                counts += ((grid >= p.birth) & (grid < p.death)).astype(int)
            out.append(
                BettiCurve(
                    dimension=dim,
                    filtration=grid.tolist(),
                    values=counts.tolist(),
                )
            )
        return out

    @staticmethod
    def _plotly_traces(
        points: list[PersistencePoint],
        *,
        axis_limits: tuple[float, float],
    ) -> list[dict[str, Any]]:
        palette = {0: "#1f77b4", 1: "#d62728", 2: "#2ca02c", 3: "#9467bd"}
        traces: list[dict[str, Any]] = []
        by_dim: dict[int, list[PersistencePoint]] = {}
        for point in points:
            by_dim.setdefault(point.dimension, []).append(point)
        for dim, pts in sorted(by_dim.items()):
            traces.append(
                {
                    "type": "scattergl",
                    "mode": "markers",
                    "name": f"H{dim}",
                    "x": [float(point.birth) for point in pts],
                    "y": [float(point.death) for point in pts],
                    "customdata": [float(point.persistence) for point in pts],
                    "marker": {
                        "color": palette.get(dim, "#999999"),
                        "size": 8,
                        "opacity": 0.85,
                    },
                    "hovertemplate": (
                        "birth=%{x:.3f}<br>death=%{y:.3f}"
                        "<br>persistence=%{customdata:.3f}<extra></extra>"
                    ),
                }
            )
        lo, hi = axis_limits
        traces.append(
            {
                "type": "scatter",
                "mode": "lines",
                "name": "birth=death",
                "x": [float(lo), float(hi)],
                "y": [float(lo), float(hi)],
                "line": {"dash": "dot", "color": "#aaaaaa"},
                "showlegend": False,
                "hoverinfo": "skip",
            }
        )
        return traces
