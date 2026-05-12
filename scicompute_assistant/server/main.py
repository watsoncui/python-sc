"""FastAPI app factory + uvicorn launcher.

Run::

    uvicorn scicompute_assistant.server.main:app --reload
    scicompute-server                             # console script
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..common.observability import (
    build_alert_sink,
    configure_logging,
    set_alert_sink,
)
from .config import load_settings
from .dependencies import get_orchestrator, get_settings
from .error_handlers import install_exception_handlers
from .middleware.observability import RequestContextMiddleware
from .middleware.rate_limit import IPRateLimiter
from .routers import ai, compute, knowledge, tda

log = logging.getLogger("scicompute.server")


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    yield
    await get_orchestrator().aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level=logging.INFO, json_lines=settings.json_logs)

    sink = build_alert_sink(
        slack_webhook_url=settings.slack_webhook_url or None,
        pagerduty_routing_key=settings.pagerduty_routing_key or None,
    )
    set_alert_sink(sink)

    app = FastAPI(
        title="SciCompute-Assistant",
        version="0.2.0",
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
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(IPRateLimiter, max_requests=settings.http_rpm_limit, window_sec=60.0)

    install_exception_handlers(app)

    app.include_router(ai.router)
    app.include_router(compute.router)
    app.include_router(tda.router)
    app.include_router(knowledge.router)

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, object]:
        return {
            "name": "SciCompute-Assistant",
            "mode": settings.mode,
            "version": "0.2.0",
            "alert_sink": type(sink).__name__,
        }

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


def run() -> None:  # pragma: no cover
    import uvicorn

    settings = load_settings()
    uvicorn.run(
        "scicompute_assistant.server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":  # pragma: no cover
    run()
