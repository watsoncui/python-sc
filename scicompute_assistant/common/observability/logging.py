"""Structured logging helpers.

We do **not** force students to install ``structlog`` or ``loguru`` – the
standard library is sufficient when we go through a single ``LoggerAdapter``
that injects a context dict (``request_id``, ``provider``, ``mode`` …) into
each record. Production deployments can swap ``configure_logging`` for a
JSON formatter without changing call sites.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
import uuid
from typing import Any

_request_ctx: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "scicompute_request_ctx", default={}
)


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        ctx = _request_ctx.get()
        for key, value in ctx.items():
            setattr(record, key, value)
        return True


class _JSONFormatter(logging.Formatter):
    """Minimal JSON log line formatter – one event per line."""

    _STANDARD = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key in self._STANDARD or key.startswith("_"):
                continue
            payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


_HANDLER_MARKER = "_scicompute_handler"


def configure_logging(*, level: int = logging.INFO, json_lines: bool = False) -> None:
    """Idempotently install **our** stream handler without touching existing ones.

    We deliberately do NOT remove pre-existing handlers (uvicorn's, pytest's
    ``caplog``, …). Instead we install a single tagged handler and skip the
    install if it is already present – this keeps third-party handlers such
    as ``caplog`` working alongside our context filter.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Always install our context filter on the root logger; cheap and idempotent.
    have_filter = any(isinstance(f, _ContextFilter) for f in root.filters)
    if not have_filter:
        root.addFilter(_ContextFilter())

    if any(getattr(h, _HANDLER_MARKER, False) for h in root.handlers):
        return  # already installed

    handler = logging.StreamHandler(sys.stderr)
    if json_lines:
        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)-5s %(name)s :: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
    handler.addFilter(_ContextFilter())
    setattr(handler, _HANDLER_MARKER, True)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def bind_request_context(**fields: Any) -> contextvars.Token:
    """Push request-scoped context (request_id, provider, mode, …).

    Use inside a ``with`` block or via the ASGI middleware to ensure the
    token is popped on response. The returned token can be passed to
    :func:`unbind_request_context` for explicit cleanup.
    """
    ctx = {**_request_ctx.get(), **fields}
    return _request_ctx.set(ctx)


def unbind_request_context(token: contextvars.Token) -> None:
    _request_ctx.reset(token)


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]
