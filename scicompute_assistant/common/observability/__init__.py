"""Observability primitives: structured logging + alert sinks."""

from .alerts import AlertEvent, AlertSink, NullAlertSink, SlackWebhookAlertSink, get_alert_sink, set_alert_sink
from .logging import bind_request_context, configure_logging, get_logger

__all__ = [
    "AlertEvent",
    "AlertSink",
    "NullAlertSink",
    "SlackWebhookAlertSink",
    "bind_request_context",
    "configure_logging",
    "get_alert_sink",
    "get_logger",
    "set_alert_sink",
]
