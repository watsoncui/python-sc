"""Simple in-memory IP-based rate limiter (per-process)."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware


class IPRateLimiter(BaseHTTPMiddleware):
    """Token-bucket-ish: at most ``max_requests`` per ``window_sec`` per client."""

    def __init__(self, app, *, max_requests: int = 30, window_sec: float = 60.0) -> None:
        super().__init__(app)
        self._max = max_requests
        self._window = window_sec
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "anon"
        bucket = self._hits[ip]
        now = time.monotonic()
        while bucket and now - bucket[0] > self._window:
            bucket.popleft()
        if len(bucket) >= self._max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: max {self._max} requests / {self._window:g}s.",
            )
        bucket.append(now)
        return await call_next(request)
