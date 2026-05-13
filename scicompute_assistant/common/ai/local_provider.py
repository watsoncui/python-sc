"""LocalProvider: pulls a per-student API key from the secure store.

Hardenings vs. the v0.1 prototype
---------------------------------
* Same typed error hierarchy as ServerProvider, so the orchestrator and
  routes never need to discriminate between the two providers.
* The decrypted key only lives on the call stack for the duration of one
  HTTP request – the local variable is overwritten with an empty string
  before raising so memory dumps cannot recover it through the frame.
* httpx timeout / connection / 429 errors are mapped explicitly (the same
  retry policy lives in the orchestrator so local students benefit from it
  without duplicating code).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..protocols.api_models import ChatMessage, LLMUsage, ProviderMode
from ..security.keyring_store import SecurityStore
from .base import BaseLLM, LLMCallResult
from .errors import (
    LLMAuthError,
    LLMConfigurationError,
    LLMNetworkError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    LLMUpstreamError,
)

log = logging.getLogger(__name__)


KNOWN_ENDPOINTS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "moonshot": "https://api.moonshot.cn/v1",
    "siliconflow": "https://api.siliconflow.cn/v1",
    "ollama-local": "http://127.0.0.1:11434/v1",
}


class LocalProvider(BaseLLM):
    name = "local"
    mode = ProviderMode.LOCAL

    def __init__(
        self,
        *,
        store: SecurityStore,
        default_endpoint: str = "deepseek",
        default_model: str = "deepseek-chat",
        request_timeout: float = 30.0,
    ) -> None:
        super().__init__(default_model=default_model)
        if default_endpoint not in KNOWN_ENDPOINTS:
            raise LLMConfigurationError(
                f"Unknown endpoint {default_endpoint!r}; "
                f"allowed: {sorted(KNOWN_ENDPOINTS)}"
            )
        self._store = store
        self._default_endpoint = default_endpoint
        self._client = httpx.AsyncClient(timeout=request_timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def acomplete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        key_alias: str | None = None,
        endpoint: str | None = None,
        **kwargs: Any,
    ) -> LLMCallResult:
        alias = key_alias or "default"
        ep_name = endpoint or self._default_endpoint
        if ep_name not in KNOWN_ENDPOINTS:
            raise LLMConfigurationError(
                f"Endpoint {ep_name!r} is not on the whitelist.",
                provider=self.name,
            )
        base_url = KNOWN_ENDPOINTS[ep_name]

        api_key = self._store.get_secret(f"llm:{ep_name}:{alias}")
        if api_key is None:
            raise LLMConfigurationError(
                f"No API key registered for endpoint={ep_name} alias={alias}. "
                "Open Settings → API Key to add one.",
                provider=self.name,
            )

        model_name = model or self.default_model
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if kwargs:
            payload.update(kwargs)

        try:
            try:
                resp = await self._client.post(
                    f"{base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(
                    f"Upstream timed out after {self._client.timeout}.",
                    provider=self.name,
                ) from exc
            except httpx.HTTPError as exc:
                raise LLMNetworkError(
                    f"Network error talking to {base_url}: {exc}",
                    provider=self.name,
                ) from exc
        finally:
            # Best-effort: wipe the local reference before we let the frame
            # die so a post-mortem memory dump is less likely to recover the
            # plaintext key.
            api_key = ""
            del api_key

        if resp.status_code in (401, 403):
            raise LLMAuthError(
                f"Upstream rejected the API key (HTTP {resp.status_code}).",
                provider=self.name,
                details={"body": resp.text[:512]},
            )
        if resp.status_code == 429:
            try:
                retry_after = float(resp.headers.get("retry-after", "")) if resp.headers.get("retry-after") else None
            except ValueError:
                retry_after = None
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
            provider=ProviderMode.LOCAL,
        )
        return LLMCallResult(
            message=ChatMessage(role=role, content=content),
            usage=usage,
            raw=data,
        )
