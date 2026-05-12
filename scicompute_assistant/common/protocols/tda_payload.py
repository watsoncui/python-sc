"""Data protocol for TDA (Topological Data Analysis) results.

This is the contract between the heavy Python compute layer (giotto-tda /
NumPy / SciPy) and the lightweight front-end visualization layer (Plotly /
Three.js). It is intentionally:

  1.  **Flat & JSON-native** – arrays are emitted as plain `list[list[float]]`
      so Plotly can read them without any post-processing.
  2.  **Dimension-aware** – persistence points carry their homology dimension
      explicitly, which lets the front-end map them to colour channels.
  3.  **Decoupled from giotto-tda internals** – converters live in
      `common.compute.tda` so swapping the engine (e.g. to ``ripser``) does
      not break the API.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PersistencePoint(BaseModel):
    """A single (birth, death) pair in a persistence diagram."""

    birth: float
    death: float
    dimension: int = Field(..., ge=0, description="Homology dimension (H0, H1, ...)")
    # Optional persistence (= death - birth) - precomputed for FE filtering.
    persistence: float = 0.0


class BettiCurve(BaseModel):
    """Betti curve sampled on a shared filtration axis."""

    dimension: int
    filtration: list[float]
    values: list[int]


class PersistenceDiagramPayload(BaseModel):
    """The wire format consumed by the Plotly front-end widget."""

    points: list[PersistencePoint]
    max_filtration: float
    # Ready-to-render Plotly traces: H_k scattergl layers plus the diagonal.
    plotly_traces: list[dict[str, Any]] = Field(default_factory=list)
    # Layered helpers so the FE can draw the diagonal & framing axes immediately
    # without a second round-trip.
    axis_limits: tuple[float, float] = (0.0, 1.0)
    betti_curves: list[BettiCurve] = Field(default_factory=list)
    # Original point cloud (downsampled) – useful for side-by-side cloud/diagram views.
    point_cloud_preview: list[list[float]] | None = None
    # Whether the diagram has been re-scaled (e.g. log axis).
    scale: Literal["linear", "log"] = "linear"


class TDARequest(BaseModel):
    """Request envelope for `/tda/pipeline`.

    Either ``data`` (raw point cloud) **or** ``code`` (custom NumPy snippet
    producing a ``points`` ndarray named ``X``) must be provided. The latter
    is gated through the sandbox.
    """

    data: list[list[float]] | None = None
    code: str | None = None
    pipeline: Literal["vietoris_rips", "alpha", "cubical", "mapper"] = "vietoris_rips"
    max_dimension: int = Field(2, ge=0, le=3)
    max_edge_length: float = Field(1.0, gt=0.0)
    n_bins: int = Field(100, ge=10, le=1024, description="Sampling for Betti curves.")
    downsample_preview: int = Field(
        500,
        ge=0,
        le=10_000,
        description="Cap on point-cloud preview points (0 disables).",
    )


class TDAResponse(BaseModel):
    diagram: PersistenceDiagramPayload
    elapsed_ms: float
    backend: str = "giotto-tda"
    warnings: list[str] = Field(default_factory=list)
