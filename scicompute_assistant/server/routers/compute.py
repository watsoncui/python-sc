"""Code execution routes (sandboxed).

Hardening
---------
The sandbox is CPU-bound. Running it inline inside the async handler would
block the FastAPI event loop and starve unrelated requests (chat,
knowledge search, /healthz). We delegate it to ``anyio.to_thread`` /
``asyncio.to_thread`` so the worker only re-attaches to the loop on
completion.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends

from ...common.compute import ComputeKernel
from ...common.protocols.api_models import ComputeRequest, ComputeResponse
from ..dependencies import kernel_dep

router = APIRouter(prefix="/compute", tags=["compute"])


@router.post("/run", response_model=ComputeResponse)
async def run(req: ComputeRequest, kernel: ComputeKernel = Depends(kernel_dep)) -> ComputeResponse:
    res = await asyncio.to_thread(
        kernel.run_code,
        req.code,
        inputs=req.inputs,
        timeout_sec=req.timeout_sec,
    )
    return ComputeResponse(
        ok=res.ok,
        stdout=res.stdout if req.capture_stdout else "",
        stderr=res.stderr if req.capture_stdout else "",
        result=res.result,
        elapsed_ms=res.elapsed_ms,
        error=res.error,
        nonfinite_keys=res.nonfinite_keys,
    )
