"""Tests for the observability layer: structured logging + Slack alert sink."""

from __future__ import annotations

import logging


from scicompute_assistant.common.observability import (
    AlertEvent,
    NullAlertSink,
    SlackWebhookAlertSink,
    bind_request_context,
    configure_logging,
    get_logger,
)
from scicompute_assistant.common.observability.logging import unbind_request_context


async def test_null_sink_emits_silently():
    sink = NullAlertSink()
    await sink.emit(AlertEvent(severity="info", title="x"))


async def test_slack_sink_skips_when_unconfigured():
    sink = SlackWebhookAlertSink(webhook_url=None)
    assert sink.is_configured is False
    # Should not raise even though no URL is set.
    await sink.emit(AlertEvent(severity="error", title="x"))


async def test_slack_sink_swallows_delivery_errors(monkeypatch):
    sink = SlackWebhookAlertSink(webhook_url="https://hooks.slack.com/services/T/X/Y")

    def boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(sink, "_post", boom)
    # Must NOT raise – alerting may never break the request that fired it.
    await sink.emit(AlertEvent(severity="critical", title="x"))


def test_request_context_attaches_fields_to_log_records(caplog):
    configure_logging(level=logging.INFO, json_lines=False)
    log = get_logger("scicompute.test")
    token = bind_request_context(request_id="rid-1", provider="server")
    try:
        with caplog.at_level(logging.INFO):
            log.info("hello")
        record = caplog.records[-1]
        assert record.request_id == "rid-1"
        assert record.provider == "server"
    finally:
        unbind_request_context(token)
