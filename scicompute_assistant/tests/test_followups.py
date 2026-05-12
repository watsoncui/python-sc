"""Follow-up tests for the items closed in REVIEW_PROCESS.md §7.

Covers three additions:
    F1. Operator param schema validation (defaults + types + bounds).
    F2. AIOrchestrator.describe() public API.
    F3. CompositeAlertSink + PagerDutyAlertSink (Composite + Strategy).
"""

from __future__ import annotations

import pytest

# --------------------------------------------------------------------------- #
# F1. Operator params schema
# --------------------------------------------------------------------------- #
from scicompute_assistant.common.compute import TDAEngine
from scicompute_assistant.common.compute.operators import get_operator
from scicompute_assistant.common.protocols.tda_payload import TDARequest


def test_operator_descriptor_fills_in_defaults():
    op = get_operator("vietoris_rips")
    params = op.descriptor().validate_params({"max_dimension": 1})
    assert params["max_dimension"] == 1
    assert params["max_edge_length"] == 1.0


def test_operator_descriptor_rejects_wrong_type():
    op = get_operator("vietoris_rips")
    with pytest.raises(ValueError, match="expected integer"):
        op.descriptor().validate_params({"max_dimension": 2.5, "max_edge_length": 1.0})


def test_operator_descriptor_rejects_bool_disguised_as_int():
    op = get_operator("vietoris_rips")
    with pytest.raises(ValueError, match="must be an integer"):
        op.descriptor().validate_params({"max_dimension": True, "max_edge_length": 1.0})


def test_operator_descriptor_enforces_min_bound():
    op = get_operator("vietoris_rips")
    with pytest.raises(ValueError, match="below the allowed minimum"):
        op.descriptor().validate_params({"max_dimension": -1, "max_edge_length": 1.0})


def test_operator_descriptor_enforces_max_bound():
    op = get_operator("vietoris_rips")
    with pytest.raises(ValueError, match="exceeds the allowed maximum"):
        op.descriptor().validate_params({"max_dimension": 99, "max_edge_length": 1.0})


def test_tda_engine_rejects_bad_params_before_numpy_runs():
    engine = TDAEngine()
    # Wrap the would-be-invalid override in TDARequest.params: schema validation
    # should fire *before* anything touches NumPy or giotto-tda.
    req = TDARequest(
        data=[[0.0, 0.0], [1.0, 0.0]],
        operator="vietoris_rips",
        max_edge_length=1.0,
        params={"max_dimension": 2.5},  # bad type
    )
    with pytest.raises(ValueError, match="expected integer"):
        engine.compute(req)


# --------------------------------------------------------------------------- #
# F2. AIOrchestrator.describe()
# --------------------------------------------------------------------------- #
from scicompute_assistant.common.ai import AIOrchestrator
from scicompute_assistant.common.ai.base import BaseLLM, LLMCallResult
from scicompute_assistant.common.protocols.api_models import (
    ChatMessage,
    LLMUsage,
    ProviderMode,
)


class _StubProvider(BaseLLM):
    name = "stub"
    mode = ProviderMode.SERVER

    def __init__(self) -> None:
        super().__init__(default_model="m")

    async def acomplete(self, *a, **kw):  # type: ignore[override]
        return LLMCallResult(
            message=ChatMessage(role="assistant", content=""),
            usage=LLMUsage(),
        )


class _LocalStub(_StubProvider):
    name = "local-stub"
    mode = ProviderMode.LOCAL


def test_describe_reports_both_providers_when_configured():
    orch = AIOrchestrator(server=_StubProvider(), local=_LocalStub())
    info = orch.describe()
    assert info["server_available"] is True
    assert info["local_available"] is True
    assert info["default"] == "server"
    modes = {p["mode"] for p in info["providers"]}
    assert modes == {"server", "local"}


def test_describe_reports_local_only_when_no_server():
    orch = AIOrchestrator(server=None, local=_LocalStub())
    info = orch.describe()
    assert info["server_available"] is False
    assert info["local_available"] is True
    assert info["default"] == "local"


def test_describe_reports_no_providers_when_empty():
    orch = AIOrchestrator(server=None, local=None)
    info = orch.describe()
    assert info == {
        "server_available": False,
        "local_available": False,
        "default": "local",
        "providers": [],
    }


# --------------------------------------------------------------------------- #
# F3. CompositeAlertSink + PagerDutyAlertSink
# --------------------------------------------------------------------------- #
from scicompute_assistant.common.observability import (
    AlertEvent,
    AlertSink,
    CompositeAlertSink,
    NullAlertSink,
    PagerDutyAlertSink,
    SlackWebhookAlertSink,
    build_alert_sink,
)


class _RecordingSink(AlertSink):
    def __init__(self) -> None:
        self.events: list[AlertEvent] = []

    async def emit(self, event):  # type: ignore[override]
        self.events.append(event)


class _ExplodingSink(AlertSink):
    async def emit(self, event):  # type: ignore[override]
        raise RuntimeError("boom")


async def test_composite_fans_out_to_all_children():
    a, b = _RecordingSink(), _RecordingSink()
    sink = CompositeAlertSink([a, b])
    await sink.emit(AlertEvent(severity="error", title="x"))
    assert len(a.events) == 1 and len(b.events) == 1


async def test_composite_isolates_failing_children():
    good = _RecordingSink()
    sink = CompositeAlertSink([_ExplodingSink(), good])
    # MUST NOT raise even though one child throws.
    await sink.emit(AlertEvent(severity="error", title="x"))
    assert len(good.events) == 1


async def test_pagerduty_sink_skips_info_severity(monkeypatch):
    sink = PagerDutyAlertSink(routing_key="r-1")
    called = {"n": 0}

    def fake_post(payload):
        called["n"] += 1

    monkeypatch.setattr(sink, "_post", fake_post)
    await sink.emit(AlertEvent(severity="info", title="boring"))
    assert called["n"] == 0


async def test_pagerduty_sink_pages_on_error(monkeypatch):
    sink = PagerDutyAlertSink(routing_key="r-1")
    seen: list[dict] = []

    def fake_post(payload):
        seen.append(payload)

    monkeypatch.setattr(sink, "_post", fake_post)
    await sink.emit(
        AlertEvent(
            severity="error",
            title="LLM call failed",
            fields={"provider": "server", "request_id": "abc"},
        )
    )
    assert len(seen) == 1
    assert seen[0]["routing_key"] == "r-1"
    assert seen[0]["payload"]["severity"] == "error"
    assert seen[0]["dedup_key"] == "LLM call failed@server"


async def test_pagerduty_sink_swallows_delivery_errors(monkeypatch):
    sink = PagerDutyAlertSink(routing_key="r-1")

    def boom(payload):
        raise RuntimeError("network")

    monkeypatch.setattr(sink, "_post", boom)
    # Must not raise.
    await sink.emit(AlertEvent(severity="critical", title="x"))


def test_build_alert_sink_picks_null_when_unconfigured():
    sink = build_alert_sink()
    assert isinstance(sink, NullAlertSink)


def test_build_alert_sink_picks_single_when_one_channel():
    sink = build_alert_sink(slack_webhook_url="https://hooks.slack.com/services/T/X/Y")
    assert isinstance(sink, SlackWebhookAlertSink)


def test_build_alert_sink_composes_when_two_channels():
    sink = build_alert_sink(
        slack_webhook_url="https://hooks.slack.com/services/T/X/Y",
        pagerduty_routing_key="r-1",
    )
    assert isinstance(sink, CompositeAlertSink)
    types = {type(s).__name__ for s in sink.sinks}
    assert types == {"SlackWebhookAlertSink", "PagerDutyAlertSink"}
