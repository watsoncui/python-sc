"""Observability primitives: structured logging + alert sinks."""

from .alerts import (
    AlertEvent,
    AlertSink,
    CompositeAlertSink,
    NullAlertSink,
    PagerDutyAlertSink,
    SlackWebhookAlertSink,
    build_alert_sink,
    get_alert_sink,
    set_alert_sink,
)
from .logging import bind_request_context, configure_logging, get_logger

__all__ = [
    "AlertEvent",
    "AlertSink",
    "CompositeAlertSink",
    "NullAlertSink",
    "PagerDutyAlertSink",
    "SlackWebhookAlertSink",
    "bind_request_context",
    "build_alert_sink",
    "configure_logging",
    "get_alert_sink",
    "get_logger",
    "set_alert_sink",
]
