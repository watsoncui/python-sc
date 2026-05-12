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
        X = np.asarray(req.data, dtype=np.float64)
        if X.ndim != 2:
            raise ValueError(f"Expected a 2-D point cloud, got shape {X.shape}.")

        t0 = time.perf_counter()
        warnings: list[str] = []

        if self.is_available and req.pipeline in ("vietoris_rips", "alpha"):
            diagrams = self._giotto_persistence(X, req)
        else:
            if not self.is_available:
                warnings.append(
                    "giotto-tda not installed; using NumPy fallback "
                    "(approximate, H0 only)."
                )
            diagrams = self._numpy_fallback(X, req)

        elapsed = (time.perf_counter() - t0) * 1000
        payload = self._to_payload(diagrams, X, req)
        return TDAResponse(
            diagram=payload,
            elapsed_ms=elapsed,
            backend="giotto-tda" if self.is_available else "numpy-fallback",
            warnings=warnings,
        )

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

        preview: list[list[float]] | None = None
        if req.downsample_preview > 0 and X.shape[0] > 0:
            k = min(req.downsample_preview, X.shape[0])
            idx = np.linspace(0, X.shape[0] - 1, k).astype(int)
            preview = X[idx].astype(float).tolist()

        return PersistenceDiagramPayload(
            points=points,
            max_filtration=max_filt,
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
