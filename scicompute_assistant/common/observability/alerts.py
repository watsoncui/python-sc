"""Alert sinks (Slack webhook + null) used by the orchestrator on hard failures.

Why a dedicated abstraction?
----------------------------
* The same alert needs to fire from FastAPI handlers *and* CLI scripts; both
  contexts must avoid blocking the caller, so dispatch is fire-and-forget.
* Production wants Slack; tests want a Null sink; both must satisfy the
  exact same contract so swapping is a one-liner (Strategy pattern).
"""

from __future__ import annotations

import abc
import asyncio
import json
import logging
import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Literal

log = logging.getLogger(__name__)

Severity = Literal["info", "warning", "error", "critical"]


@dataclass
class AlertEvent:
    severity: Severity
    title: str
    body: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


class AlertSink(abc.ABC):
    @abc.abstractmethod
    async def emit(self, event: AlertEvent) -> None: ...


class NullAlertSink(AlertSink):
    """Default sink – drops everything but logs at DEBUG so tests can introspect."""

    async def emit(self, event: AlertEvent) -> None:  # noqa: D401
        log.debug("[alert/null] %s %s %s", event.severity, event.title, event.fields)


class SlackWebhookAlertSink(AlertSink):
    """Fire-and-forget Slack Incoming Webhook sink.

    Notes
    -----
    * Uses :mod:`urllib.request` inside ``asyncio.to_thread`` to avoid pulling
      :mod:`httpx` into the alerting path (one less dependency to fail).
    * Failures are *swallowed* (logged at WARNING). Alerts must never bring
      down the request that triggered them.
    * Webhook secret comes from the constructor or the ``SLACK_WEBHOOK_URL``
      environment variable so it is never committed.
    """

    def __init__(self, webhook_url: str | None = None, *, timeout: float = 3.0) -> None:
        self._url = webhook_url or os.getenv("SLACK_WEBHOOK_URL") or ""
        self._timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self._url)

    async def emit(self, event: AlertEvent) -> None:
        if not self.is_configured:
            log.debug("Slack alert sink not configured; dropping %s.", event.title)
            return
        payload = self._render(event)
        try:
            await asyncio.to_thread(self._post, payload)
        except Exception:  # noqa: BLE001 - we promised never to raise
            log.warning("Slack alert delivery failed for %s.", event.title, exc_info=True)

    def _post(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            if resp.status >= 300:
                raise RuntimeError(f"Slack returned HTTP {resp.status}")

    @staticmethod
    def _render(event: AlertEvent) -> dict[str, Any]:
        color = {
            "info": "#36a64f",
            "warning": "#f2c744",
            "error": "#e01e5a",
            "critical": "#7c0000",
        }.get(event.severity, "#999999")
        fields = [
            {"title": k, "value": str(v), "short": True}
            for k, v in event.fields.items()
        ]
        return {
            "attachments": [
                {
                    "color": color,
                    "title": event.title,
                    "text": event.body,
                    "fields": fields,
                    "footer": "SciCompute-Assistant",
                    "ts": int(event.ts),
                }
            ]
        }


class PagerDutyAlertSink(AlertSink):
    """PagerDuty Events API v2 sink.

    Why a separate sink class instead of "another Slack URL"?
    --------------------------------------------------------
    * PagerDuty has a different payload schema and a much shorter SLA – its
      acknowledgements should not be coupled to chat-style sinks.
    * Per-call ``dedup_key`` lets us deduplicate identical alerts (e.g.
      ``LLMUpstreamError@server``) so on-call doesn't get woken twice.

    Just like Slack, delivery is fire-and-forget and never raises.
    """

    EVENTS_URL = "https://events.pagerduty.com/v2/enqueue"

    def __init__(
        self,
        routing_key: str | None = None,
        *,
        source: str = "scicompute-assistant",
        timeout: float = 3.0,
    ) -> None:
        self._routing_key = routing_key or os.getenv("PAGERDUTY_ROUTING_KEY") or ""
        self._source = source
        self._timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self._routing_key)

    async def emit(self, event: AlertEvent) -> None:
        if not self.is_configured:
            log.debug("PagerDuty sink not configured; dropping %s.", event.title)
            return
        # PagerDuty only pages on warning+; ``info`` would just spam.
        if event.severity == "info":
            return
        payload = self._render(event)
        try:
            await asyncio.to_thread(self._post, payload)
        except Exception:  # noqa: BLE001 - alerting must never raise
            log.warning("PagerDuty delivery failed for %s.", event.title, exc_info=True)

    def _post(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.EVENTS_URL,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            if resp.status >= 300:
                raise RuntimeError(f"PagerDuty returned HTTP {resp.status}")

    def _render(self, event: AlertEvent) -> dict[str, Any]:
        severity = "critical" if event.severity == "critical" else (
            "error" if event.severity == "error" else "warning"
        )
        # Stable dedup key: title + first request-field, if available.
        dedup_seed = event.title
        if "request_id" in event.fields:
            dedup_seed = f"{event.title}@{event.fields.get('provider', '?')}"
        return {
            "routing_key": self._routing_key,
            "event_action": "trigger",
            "dedup_key": dedup_seed,
            "payload": {
                "summary": event.title,
                "source": self._source,
                "severity": severity,
                "component": event.fields.get("op", "ai"),
                "custom_details": {**event.fields, "body": event.body, "ts": event.ts},
            },
        }


class CompositeAlertSink(AlertSink):
    """Fan-out sink that delivers to N child sinks concurrently.

    Implements the **Composite design pattern** – `CompositeAlertSink` is
    itself an `AlertSink`, so callers cannot tell whether they are talking
    to one channel or ten. Failures in one child do **not** block the others
    (we await all with ``return_exceptions=True``).
    """

    def __init__(self, sinks: list[AlertSink]) -> None:
        self._sinks = list(sinks)

    @property
    def sinks(self) -> tuple[AlertSink, ...]:
        return tuple(self._sinks)

    async def emit(self, event: AlertEvent) -> None:
        if not self._sinks:
            return
        results = await asyncio.gather(
            *(s.emit(event) for s in self._sinks),
            return_exceptions=True,
        )
        for s, r in zip(self._sinks, results):
            if isinstance(r, Exception):
                log.warning(
                    "Child sink %s failed to deliver alert: %s",
                    type(s).__name__, r,
                )


def build_alert_sink(
    *,
    slack_webhook_url: str | None = None,
    pagerduty_routing_key: str | None = None,
) -> AlertSink:
    """Convenience factory used by the server bootstrap.

    Empty configuration → :class:`NullAlertSink`. One channel → that channel.
    Multiple → wrapped in :class:`CompositeAlertSink`.
    """
    sinks: list[AlertSink] = []
    slack = SlackWebhookAlertSink(webhook_url=slack_webhook_url)
    if slack.is_configured:
        sinks.append(slack)
    pager = PagerDutyAlertSink(routing_key=pagerduty_routing_key)
    if pager.is_configured:
        sinks.append(pager)
    if not sinks:
        return NullAlertSink()
    if len(sinks) == 1:
        return sinks[0]
    return CompositeAlertSink(sinks)


# --------------------------------------------------------------------------- #
# Singleton holder (Strategy pattern, swappable from app bootstrap)
# --------------------------------------------------------------------------- #
_global_sink: AlertSink = NullAlertSink()


def get_alert_sink() -> AlertSink:
    return _global_sink


def set_alert_sink(sink: AlertSink) -> None:
    global _global_sink  # noqa: PLW0603 – intentional, single bootstrap call
    _global_sink = sink
