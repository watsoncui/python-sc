"""Typed exception hierarchy for the AI subsystem.

Why a dedicated hierarchy?
--------------------------
* The route layer needs to map provider failures to the correct HTTP status
  (`429` for rate-limit, `504` for upstream timeout, `502` for upstream 5xx, …).
* The orchestrator needs to decide *generically* whether a failure is
  **retryable** without inspecting third-party exception types.
* Tests can assert on stable types instead of httpx internals.

The classes live in :mod:`common.ai` so both ServerProvider and LocalProvider
can raise them; routers consume them via a single mapping table.
"""

from __future__ import annotations

from typing import Any


class LLMError(Exception):
    """Base class for every LLM-related failure surfaced to the orchestrator."""

    #: Recommended HTTP status code (used by the route-layer mapping).
    http_status: int = 502
    #: Whether the orchestrator should retry the call (with backoff).
    retryable: bool = False

    def __init__(self, message: str, *, provider: str | None = None,
                 details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.provider = provider
        self.details = details or {}


class LLMConfigurationError(LLMError):
    """Provider is mis-configured (e.g. missing key, unknown endpoint)."""

    http_status = 400
    retryable = False


class LLMAuthError(LLMError):
    """Upstream rejected the API key (401/403)."""

    http_status = 401
    retryable = False


class LLMRateLimitError(LLMError):
    """Upstream returned 429 or the local token bucket fired."""

    http_status = 429
    retryable = True

    def __init__(self, message: str, *, retry_after: float | None = None,
                 provider: str | None = None,
                 details: dict[str, Any] | None = None) -> None:
        super().__init__(message, provider=provider, details=details)
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    """Upstream took too long. Distinct from connection errors so the route
    layer can return 504 instead of 502."""

    http_status = 504
    retryable = True


class LLMNetworkError(LLMError):
    """Connection refused, DNS failure, TLS error, etc."""

    http_status = 502
    retryable = True


class LLMUpstreamError(LLMError):
    """Upstream returned 5xx with no specific signal."""

    http_status = 502
    retryable = True


class LLMResponseError(LLMError):
    """Upstream returned a malformed payload (no choices, bad JSON, …)."""

    http_status = 502
    retryable = False
