"""Centralised mapping from typed exceptions to HTTP responses.

Why centralise?
---------------
Distributing ``try/except`` over every route creates drift (one route
returns 502, another returns 500 for the same underlying error). A single
exception handler ensures uniform behaviour and uniform logging.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from ..common.ai.errors import (
    LLMAuthError,
    LLMConfigurationError,
    LLMError,
    LLMRateLimitError,
)

log = logging.getLogger(__name__)


def install_exception_handlers(app: FastAPI) -> None:
    """Wire all our typed exceptions into FastAPI's handler chain."""

    @app.exception_handler(LLMError)
    async def _llm_error(request: Request, exc: LLMError) -> JSONResponse:
        log.warning(
            "LLM error on %s: %s",
            request.url.path,
            exc,
            extra={"error_type": type(exc).__name__, "provider": exc.provider},
        )
        body: dict[str, object] = {
            "detail": str(exc),
            "error_type": type(exc).__name__,
            "retryable": exc.retryable,
        }
        if isinstance(exc, LLMRateLimitError) and exc.retry_after is not None:
            body["retry_after"] = exc.retry_after
        if isinstance(exc, (LLMConfigurationError, LLMAuthError)):
            body["hint"] = (
                "Open Settings → API Key to add a valid key, "
                "or switch to the cloud provider."
            )
        headers = {}
        if isinstance(exc, LLMRateLimitError) and exc.retry_after is not None:
            headers["Retry-After"] = str(int(exc.retry_after))
        return JSONResponse(status_code=exc.http_status, content=body, headers=headers)

    @app.exception_handler(ValueError)
    async def _value_error(request: Request, exc: ValueError) -> JSONResponse:
        # Compute/TDA validation errors surface here as ValueError.
        log.info("400 on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # Re-raise HTTPException so FastAPI's built-in handler does its thing.
    @app.exception_handler(HTTPException)
    async def _http(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None) or {},
        )
