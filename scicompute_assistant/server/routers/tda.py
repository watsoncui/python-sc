"""TDA pipeline route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ...common.compute import TDAEngine
from ...common.protocols.tda_payload import TDARequest, TDAResponse
from ..dependencies import tda_dep

router = APIRouter(prefix="/tda", tags=["tda"])


@router.post("/pipeline", response_model=TDAResponse)
async def pipeline(req: TDARequest, engine: TDAEngine = Depends(tda_dep)) -> TDAResponse:
    if req.data is None:
        raise HTTPException(
            status_code=400,
            detail="Provide `data` (2D point cloud). Code-mode is gated by the sandbox route.",
        )
    try:
        return engine.compute(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/health")
async def health(engine: TDAEngine = Depends(tda_dep)) -> dict[str, object]:
    return {"giotto_available": engine.is_available}
