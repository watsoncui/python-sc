"""Request-scoped logging context middleware."""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ...common.observability.logging import (
    bind_request_context,
    new_request_id,
    unbind_request_context,
)

log = logging.getLogger("scicompute.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Tag every request with a stable ``request_id`` so logs can be joined."""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or new_request_id()
        token = bind_request_context(
            request_id=rid,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "anon",
        )
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            log.info(
                "http.access",
                extra={"elapsed_ms": round(elapsed, 2)},
            )
            unbind_request_context(token)
        response.headers["X-Request-Id"] = rid
        return response
