"""``BaseLLM`` – the abstract contract every provider must implement.

Notes
-----
* The contract is intentionally minimal (``acomplete``) so providers can wrap
  *any* upstream API (OpenAI, DeepSeek, Anthropic, a local Ollama, ...).
* Token-counting and rate-limiting are **policy** concerns and belong on
  individual subclasses, not the abstract base.
* All methods are async to keep request handlers non-blocking, especially in
  the FastAPI server build where many students may share a single key.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field

from ..protocols.api_models import ChatMessage, LLMUsage, ProviderMode


@dataclass
class LLMCallResult:
    """Plain result object returned by every provider."""

    message: ChatMessage
    usage: LLMUsage = field(default_factory=LLMUsage)
    raw: dict | None = None  # provider-specific payload, for debugging only.


class BaseLLM(abc.ABC):
    """Abstract LLM provider.

    Subclasses **must** implement :meth:`acomplete`. They **may** override
    :meth:`count_tokens` for accurate billing; the default is a rough
    word-based heuristic suitable for prototyping.
    """

    name: str = "base"
    mode: ProviderMode = ProviderMode.SERVER

    def __init__(self, *, default_model: str) -> None:
        self.default_model = default_model

    # ------------------------------------------------------------------ #
    # Core
    # ------------------------------------------------------------------ #
    @abc.abstractmethod
    async def acomplete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: object,
    ) -> LLMCallResult:
        """Run a single chat completion request and return the result."""

    # ------------------------------------------------------------------ #
    # Optional utilities (override for accuracy)
    # ------------------------------------------------------------------ #
    def count_tokens(self, text: str) -> int:
        """A naive token estimate (~ 1 token per 0.75 words / 4 chars).

        Subclasses with access to ``tiktoken`` or a tokenizer SHOULD override.
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    async def aclose(self) -> None:
        """Hook for releasing HTTP clients / sockets at app shutdown."""
        return None
