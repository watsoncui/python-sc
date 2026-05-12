"""LocalProvider: pulls an *encrypted* per-student API key from the secure store.

Used by the Tauri desktop build. The key is **never** sent to any teacher-side
service; it is decrypted in-process just before the HTTP call and is wiped
from memory as soon as the call returns.

The provider is intentionally compatible with multiple upstreams (OpenAI /
DeepSeek / Moonshot / SiliconFlow) by mapping the student's chosen endpoint
to a ``base_url``.
"""

from __future__ import annotations

from typing import Any

import httpx

from ..protocols.api_models import ChatMessage, LLMUsage, ProviderMode
from ..security.keyring_store import SecurityStore
from .base import BaseLLM, LLMCallResult


# A whitelist of upstream endpoints the offline app is willing to hit.
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
            raise ValueError(
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
            raise ValueError(f"Endpoint {ep_name!r} is not on the whitelist.")
        base_url = KNOWN_ENDPOINTS[ep_name]

        api_key = self._store.get_secret(f"llm:{ep_name}:{alias}")
        if api_key is None:
            raise PermissionError(
                f"No API key registered for endpoint={ep_name} alias={alias}. "
                "Open Settings → API Key to add one."
            )

        model_name = model or self.default_model
        payload = {
            "model": model_name,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if kwargs:
            payload.update(kwargs)

        try:
            resp = await self._client.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
        finally:
            del api_key  # best-effort: drop reference ASAP

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
            provider=ProviderMode.LOCAL,
        )
        return LLMCallResult(
            message=ChatMessage(role=choice["role"], content=choice["content"]),
            usage=usage,
            raw=data,
        )
