"""ServerProvider: teacher-managed API key with rate-limiting, retries, and typed errors.

Hardenings vs. the v0.1 prototype
---------------------------------
* All upstream failures map to the typed exception hierarchy in
  :mod:`common.ai.errors`. Routes can therefore translate them to HTTP without
  importing httpx.
* HTTP 429 / 5xx are retried with exponential backoff that honours the
  ``Retry-After`` header. Auth (401/403) and 4xx (excluding 429) are *not*
  retried – they will not get better.
* Timeouts and connection errors are logged with the request-scoped context
  (``request_id``, ``provider``).
* The HTTP client uses connection pooling (one ``AsyncClient`` per provider
  instance) so concurrent students share TLS handshakes.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..protocols.api_models import ChatMessage, LLMUsage, ProviderMode
from .base import BaseLLM, LLMCallResult
from .errors import (
    LLMAuthError,
    LLMNetworkError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    LLMUpstreamError,
)

log = logging.getLogger(__name__)


@dataclass
class _TokenBucket:
    """Tiny per-key token bucket. ``rate`` = tokens/sec, ``capacity`` = burst."""

    capacity: float
    rate: float
    tokens: float = field(init=False)
    last: float = field(init=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self.tokens = self.capacity
        self.last = time.monotonic()

    async def take(self, n: float = 1.0, *, max_wait: float = 30.0) -> None:
        async with self.lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
            self.last = now
            if self.tokens < n:
                deficit = n - self.tokens
                sleep_for = deficit / self.rate
                if sleep_for > max_wait:
                    raise LLMRateLimitError(
                        f"Local token bucket would block for {sleep_for:.1f}s "
                        f"(> max_wait={max_wait}s).",
                        retry_after=sleep_for,
                    )
                await asyncio.sleep(sleep_for)
                self.tokens = 0.0
            else:
                self.tokens -= n


class ServerProvider(BaseLLM):
    name = "server"
    mode = ProviderMode.SERVER

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o-mini",
        rpm_limit: int = 60,
        burst: int = 10,
        request_timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        super().__init__(default_model=default_model)
        if not api_key:
            raise ValueError("ServerProvider requires a non-empty api_key.")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=request_timeout)
        self._bucket = _TokenBucket(capacity=float(burst), rate=rpm_limit / 60.0)
        self._max_retries = max_retries

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    async def acomplete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMCallResult:
        await self._bucket.take()

        model_name = model or self.default_model
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # ``key_alias`` and ``endpoint`` are accepted by LocalProvider; ignore
        # them silently here so the orchestrator can pass the same kwargs to
        # any provider without branching.
        for ignore_key in ("key_alias", "endpoint"):
            kwargs.pop(ignore_key, None)
        if kwargs:
            payload.update(kwargs)

        return await self._with_retries(payload, model_name=model_name)

    # ------------------------------------------------------------------ #
    # Retry & error mapping
    # ------------------------------------------------------------------ #
    async def _with_retries(self, payload: dict[str, Any], *, model_name: str) -> LLMCallResult:
        delay = 0.5
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return await self._call_once(payload, model_name=model_name)
            except LLMRateLimitError as exc:
                last_exc = exc
                wait = exc.retry_after if exc.retry_after is not None else delay
                log.warning(
                    "Upstream rate-limited; retrying after %.2fs (attempt %d/%d).",
                    wait, attempt, self._max_retries,
                )
                await asyncio.sleep(max(0.0, wait) + random.uniform(0, 0.25))
            except (LLMTimeoutError, LLMNetworkError, LLMUpstreamError) as exc:
                last_exc = exc
                if attempt == self._max_retries:
                    break
                log.warning(
                    "Upstream transient failure (%s); retrying in %.2fs (attempt %d/%d).",
                    type(exc).__name__, delay, attempt, self._max_retries,
                )
                await asyncio.sleep(delay + random.uniform(0, 0.25))
                delay = min(delay * 2, 8.0)
        assert last_exc is not None  # for type checkers; loop must have populated
        raise last_exc

    async def _call_once(self, payload: dict[str, Any], *, model_name: str) -> LLMCallResult:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = await self._client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                f"Upstream timed out after {self._client.timeout}.",
                provider=self.name,
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMNetworkError(
                f"Network error talking to {self._base_url}: {exc}",
                provider=self.name,
            ) from exc

        if resp.status_code == 401 or resp.status_code == 403:
            raise LLMAuthError(
                f"Upstream rejected the API key (HTTP {resp.status_code}).",
                provider=self.name,
                details={"body": resp.text[:512]},
            )
        if resp.status_code == 429:
            retry_after = _parse_retry_after(resp.headers.get("retry-after"))
            raise LLMRateLimitError(
                "Upstream returned HTTP 429.",
                retry_after=retry_after,
                provider=self.name,
                details={"body": resp.text[:512]},
            )
        if resp.status_code >= 500:
            raise LLMUpstreamError(
                f"Upstream HTTP {resp.status_code}.",
                provider=self.name,
                details={"body": resp.text[:512]},
            )
        if resp.status_code >= 400:
            raise LLMResponseError(
                f"Upstream rejected the request (HTTP {resp.status_code}).",
                provider=self.name,
                details={"body": resp.text[:512]},
            )

        try:
            data = resp.json()
            choice = data["choices"][0]["message"]
            content = choice["content"]
            role = choice.get("role", "assistant")
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMResponseError(
                "Malformed completion payload (missing choices/message).",
                provider=self.name,
                details={"body": resp.text[:512]},
            ) from exc

        usage_obj = data.get("usage", {}) or {}
        usage = LLMUsage(
            prompt_tokens=int(usage_obj.get("prompt_tokens", 0)),
            completion_tokens=int(usage_obj.get("completion_tokens", 0)),
            total_tokens=int(
                usage_obj.get(
                    "total_tokens",
                    usage_obj.get("prompt_tokens", 0)
                    + usage_obj.get("completion_tokens", 0),
                )
            ),
            model=model_name,
            provider=ProviderMode.SERVER,
        )
        return LLMCallResult(
            message=ChatMessage(role=role, content=content),
            usage=usage,
            raw=data,
        )


def _parse_retry_after(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
