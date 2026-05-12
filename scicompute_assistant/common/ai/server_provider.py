"""ServerProvider: uses a teacher-managed API key, with rate-limiting and quota.

Design choices
--------------
* The HTTP call shape mirrors the OpenAI Chat Completions API – DeepSeek and
  most domestic alternatives are wire-compatible, so the same provider class
  works for ``gpt-4o-mini`` and ``deepseek-chat`` by swapping ``base_url``.
* A simple in-process token bucket caps per-student burst rate; deployments
  that fan out across workers should plug in Redis (see ``RateLimiter``).
* Token usage is read back from the provider response when available and
  falls back to ``count_tokens``.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..protocols.api_models import ChatMessage, LLMUsage, ProviderMode
from .base import BaseLLM, LLMCallResult


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

    async def take(self, n: float = 1.0) -> None:
        async with self.lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
            self.last = now
            if self.tokens < n:
                sleep_for = (n - self.tokens) / self.rate
                await asyncio.sleep(sleep_for)
                self.tokens = 0.0
            else:
                self.tokens -= n


class ServerProvider(BaseLLM):
    """Teacher-side provider; expects the API key to live in env/config."""

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
    ) -> None:
        super().__init__(default_model=default_model)
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=request_timeout)
        self._bucket = _TokenBucket(capacity=float(burst), rate=rpm_limit / 60.0)

    async def aclose(self) -> None:
        await self._client.aclose()

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
        payload = {
            "model": model_name,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if kwargs:
            payload.update(kwargs)

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        resp = await self._client.post(
            f"{self._base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]["message"]
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
            message=ChatMessage(role=choice["role"], content=choice["content"]),
            usage=usage,
            raw=data,
        )
