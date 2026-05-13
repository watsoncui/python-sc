"""AI orchestration layer: provider abstraction + prompt library + dispatcher."""

from . import errors
from .base import BaseLLM, LLMCallResult
from .errors import (
    LLMAuthError,
    LLMConfigurationError,
    LLMError,
    LLMNetworkError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
    LLMUpstreamError,
)
from .local_provider import LocalProvider
from .orchestrator import AIOrchestrator
from .prompts import PromptLibrary
from .server_provider import ServerProvider

__all__ = [
    "AIOrchestrator",
    "BaseLLM",
    "LLMAuthError",
    "LLMCallResult",
    "LLMConfigurationError",
    "LLMError",
    "LLMNetworkError",
    "LLMRateLimitError",
    "LLMResponseError",
    "LLMTimeoutError",
    "LLMUpstreamError",
    "LocalProvider",
    "PromptLibrary",
    "ServerProvider",
    "errors",
]
