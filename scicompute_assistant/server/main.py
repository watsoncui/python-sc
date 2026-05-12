"""FastAPI app factory + uvicorn launcher.

Run::

    uvicorn scicompute_assistant.server.main:app --reload

Or via the console script::

    scicompute-server
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import load_settings
from .dependencies import (
    get_orchestrator,
    get_settings,
)
from .middleware.rate_limit import IPRateLimiter
from .routers import ai, compute, knowledge, tda

log = logging.getLogger("scicompute.server")


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    yield
    await get_orchestrator().aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SciCompute-Assistant",
        version="0.1.0",
        description=(
            "Dual-mode (server/local) teaching assistant for Python scientific "
            "computing, with TDA visualization support."
        ),
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(IPRateLimiter, max_requests=60, window_sec=60.0)

    app.include_router(ai.router)
    app.include_router(compute.router)
    app.include_router(tda.router)
    app.include_router(knowledge.router)

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, object]:
        return {
            "name": "SciCompute-Assistant",
            "mode": settings.mode,
            "version": "0.1.0",
        }

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


def run() -> None:  # pragma: no cover - thin shim
    import uvicorn

    settings = load_settings()
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "scicompute_assistant.server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":  # pragma: no cover
    run()
