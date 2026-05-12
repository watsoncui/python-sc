"""TDA pipeline routes.

* ``POST /tda/pipeline`` – run a registered operator. The heavy NumPy / giotto
  work is offloaded to a worker thread so the event loop stays responsive.
* ``GET  /tda/operators`` – enumerate registered operators (Plugin Registry
  exposed to the front-end so it can build the parameter form dynamically).
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends

from ...common.compute import TDAEngine
from ...common.compute.operators import list_operators
from ...common.protocols.tda_payload import TDARequest, TDAResponse
from ..dependencies import tda_dep

router = APIRouter(prefix="/tda", tags=["tda"])


@router.post("/pipeline", response_model=TDAResponse)
async def pipeline(req: TDARequest, engine: TDAEngine = Depends(tda_dep)) -> TDAResponse:
    if req.data is None:
        # Route-level validation (raises ValueError → 400 via error handler).
        raise ValueError(
            "Provide `data` (2D point cloud). Code-mode is gated by the sandbox route."
        )
    return await asyncio.to_thread(engine.compute, req)


@router.get("/operators")
async def operators() -> list[dict[str, object]]:
    return [
        {
            "operator_id": d.operator_id,
            "title": d.title,
            "description": d.description,
            "params_schema": d.params_schema,
            "output_homology_dims": d.output_homology_dims,
        }
        for d in list_operators()
    ]


@router.get("/health")
async def health(engine: TDAEngine = Depends(tda_dep)) -> dict[str, object]:
    return {"giotto_available": engine.is_available,
            "registered_operators": [d.operator_id for d in engine.list_operators()]}
