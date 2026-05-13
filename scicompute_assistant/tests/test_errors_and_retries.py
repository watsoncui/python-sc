"""Edge-case tests for the AI subsystem: error mapping, retry policy, dual-mode isolation."""

from __future__ import annotations

from typing import Any

import pytest

from scicompute_assistant.common.ai import AIOrchestrator
from scicompute_assistant.common.ai.base import BaseLLM, LLMCallResult
from scicompute_assistant.common.ai.errors import (
    LLMAuthError,
    LLMConfigurationError,
    LLMNetworkError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUpstreamError,
)
from scicompute_assistant.common.ai.server_provider import ServerProvider
from scicompute_assistant.common.protocols.api_models import (
    AuditRequest,
    ChatMessage,
    ChatRequest,
    LLMUsage,
    ProviderMode,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
class _ScriptedProvider(BaseLLM):
    """Provider whose ``acomplete`` plays back a queued sequence of outcomes."""

    name = "scripted"
    mode = ProviderMode.SERVER

    def __init__(self, outcomes: list[Any]) -> None:
        super().__init__(default_model="scripted")
        self._outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []

    async def acomplete(self, messages, **kwargs):  # type: ignore[override]
        self.calls.append({"messages": messages, "kwargs": kwargs})
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _ok_result(text: str = "hi") -> LLMCallResult:
    return LLMCallResult(
        message=ChatMessage(role="assistant", content=text),
        usage=LLMUsage(model="scripted", provider=ProviderMode.SERVER),
    )


# --------------------------------------------------------------------------- #
# Dual-mode robustness
# --------------------------------------------------------------------------- #
async def test_orchestrator_refuses_local_when_not_configured():
    orch = AIOrchestrator(server=_ScriptedProvider([_ok_result()]), local=None)
    req = ChatRequest(messages=[ChatMessage(role="user", content="hi")],
                      provider=ProviderMode.LOCAL)
    with pytest.raises(LLMConfigurationError):
        await orch.chat(req)


async def test_orchestrator_refuses_server_when_not_configured():
    orch = AIOrchestrator(server=None, local=_ScriptedProvider([_ok_result()]))
    req = AuditRequest(code="x = 1", provider=ProviderMode.SERVER)
    with pytest.raises(LLMConfigurationError):
        await orch.audit_vectorize(req)


async def test_orchestrator_routes_to_correct_provider():
    """Audit calls in SERVER mode must only touch the server provider – the
    student-key provider must never see the request body."""
    server = _ScriptedProvider([_ok_result('{"summary":"ok","suggestions":[]}')])
    local = _ScriptedProvider([_ok_result('{"summary":"BAD","suggestions":[]}')])
    orch = AIOrchestrator(server=server, local=local)
    await orch.audit_vectorize(
        AuditRequest(code="for x in arr: pass", provider=ProviderMode.SERVER)
    )
    assert len(server.calls) == 1
    assert local.calls == []  # critical: local provider untouched


# --------------------------------------------------------------------------- #
# Audit JSON parser edge cases
# --------------------------------------------------------------------------- #
def test_audit_parser_drops_malformed_suggestion_rows():
    raw = (
        '{"summary":"x","suggestions":'
        '[{"category":"vectorization","severity":"info","line_range":[1,2],'
        '"rationale":"r"},'
        '{"this_row":"is_garbage"}],'
        '"refactored_code":"y"}'
    )
    out = AIOrchestrator._parse_audit_response(raw, usage=LLMUsage())
    assert len(out.suggestions) == 1
    assert out.summary == "x"


def test_audit_parser_handles_empty_content():
    out = AIOrchestrator._parse_audit_response("", usage=LLMUsage())
    assert "无法解析" in out.summary


# --------------------------------------------------------------------------- #
# Retry policy (rate limit + transient errors)
# --------------------------------------------------------------------------- #
async def test_server_provider_retries_rate_limit_then_succeeds(monkeypatch):
    sp = ServerProvider(api_key="sk-test", max_retries=3, rpm_limit=1_000_000, burst=100)
    # Patch the inner call to fail twice (429) then succeed.
    outcomes: list[Any] = [
        LLMRateLimitError("first", retry_after=0.0),
        LLMRateLimitError("second", retry_after=0.0),
        _ok_result("done"),
    ]

    async def fake_call(self_, payload, *, model_name):  # noqa: ANN001
        out = outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out

    monkeypatch.setattr(ServerProvider, "_call_once", fake_call)

    result = await sp.acomplete([ChatMessage(role="user", content="hi")])
    assert result.message.content == "done"
    assert outcomes == []  # all consumed


async def test_server_provider_gives_up_after_max_retries(monkeypatch):
    sp = ServerProvider(api_key="sk-test", max_retries=2, rpm_limit=1_000_000, burst=100)

    async def always_fail(self_, payload, *, model_name):  # noqa: ANN001
        raise LLMUpstreamError("upstream down")

    monkeypatch.setattr(ServerProvider, "_call_once", always_fail)
    with pytest.raises(LLMUpstreamError):
        await sp.acomplete([ChatMessage(role="user", content="hi")])


async def test_server_provider_does_not_retry_auth_errors(monkeypatch):
    sp = ServerProvider(api_key="sk-test", max_retries=5, rpm_limit=1_000_000, burst=100)
    calls = {"n": 0}

    async def fail_auth(self_, payload, *, model_name):  # noqa: ANN001
        calls["n"] += 1
        raise LLMAuthError("bad key")

    monkeypatch.setattr(ServerProvider, "_call_once", fail_auth)
    with pytest.raises(LLMAuthError):
        await sp.acomplete([ChatMessage(role="user", content="hi")])
    assert calls["n"] == 1  # one shot, no retry


async def test_server_provider_maps_httpx_timeout(monkeypatch):
    """A real httpx.TimeoutException must become an LLMTimeoutError."""
    import httpx

    sp = ServerProvider(api_key="sk-test", max_retries=1, rpm_limit=1_000_000, burst=100)

    async def boom(self, url, *, json, headers):  # noqa: ANN001
        raise httpx.TimeoutException("read timeout")

    monkeypatch.setattr(sp._client, "post", boom.__get__(sp._client, sp._client.__class__))
    with pytest.raises(LLMTimeoutError):
        await sp._call_once({"foo": 1}, model_name="m")


async def test_server_provider_maps_httpx_network_error(monkeypatch):
    import httpx

    sp = ServerProvider(api_key="sk-test", max_retries=1, rpm_limit=1_000_000, burst=100)

    async def boom(self, url, *, json, headers):  # noqa: ANN001
        raise httpx.ConnectError("dns failed")

    monkeypatch.setattr(sp._client, "post", boom.__get__(sp._client, sp._client.__class__))
    with pytest.raises(LLMNetworkError):
        await sp._call_once({"foo": 1}, model_name="m")
