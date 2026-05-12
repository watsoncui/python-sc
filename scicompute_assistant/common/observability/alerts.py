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


# --------------------------------------------------------------------------- #
# Singleton holder (Strategy pattern, swappable from app bootstrap)
# --------------------------------------------------------------------------- #
_global_sink: AlertSink = NullAlertSink()


def get_alert_sink() -> AlertSink:
    return _global_sink


def set_alert_sink(sink: AlertSink) -> None:
    global _global_sink  # noqa: PLW0603 – intentional, single bootstrap call
    _global_sink = sink
