"""Isolated execution environment for student-submitted Python code.

Threat model
------------
Students may copy/paste arbitrary code from the internet. We want to:

  * **Run** their code reliably for teaching purposes.
  * **Limit** wall-clock time (so a runaway `while True` cannot freeze the
    teacher's server).
  * **Restrict** module imports to a vetted scientific stack.
  * **Capture** stdout / stderr for inline display.

Strategy
--------
We layer two defenses:

1. *Compile-time* gating via :mod:`RestrictedPython` (when available), which
   rejects unsafe AST constructs (``__import__``, attribute access to dunder
   names, ``exec``, ``eval``, file IO).
2. *Runtime* gating via a controlled ``builtins`` mapping and a
   per-process ``signal.alarm`` (POSIX) / ``threading.Timer`` (Windows fallback).

This is **not** a security boundary for production multi-tenant deployments.
For the server build, follow the recommendation in
``docs/ARCHITECTURE.md`` and run the sandbox inside a Firecracker microVM or
gVisor container. The :class:`Sandbox` class is the *first* line of defense,
not the only one.
"""

from __future__ import annotations

import ctypes
import io
import logging
import math
import signal
import threading
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from typing import Any

try:
    from RestrictedPython import compile_restricted, safe_builtins  # type: ignore
    from RestrictedPython.Eval import default_guarded_getitem  # type: ignore
    from RestrictedPython.Guards import (  # type: ignore
        guarded_iter_unpack_sequence,
        guarded_unpack_sequence,
    )

    _HAS_RESTRICTED = True
except Exception:  # noqa: BLE001 - optional dependency
    _HAS_RESTRICTED = False

log = logging.getLogger(__name__)


SAFE_MODULES: set[str] = {
    "numpy",
    "scipy",
    "scipy.signal",
    "scipy.linalg",
    "scipy.sparse",
    "scipy.spatial",
    "scipy.special",
    "pandas",
    "math",
    "statistics",
    "itertools",
    "functools",
    "collections",
}


@dataclass
class SandboxResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0
    error: str | None = None


class _Timeout(Exception):
    pass


def _alarm_handler(signum, frame):  # noqa: ANN001, ARG001
    raise _Timeout("Sandbox wall-clock budget exceeded.")


def _make_safe_import():
    safe = {name.split(".", 1)[0] for name in SAFE_MODULES}

    def _safe_import(name, *args, **kwargs):
        root = name.split(".", 1)[0]
        if root not in safe:
            raise ImportError(f"Import of {name!r} is not allowed in the sandbox.")
        return __import__(name, *args, **kwargs)

    return _safe_import


class Sandbox:
    """Run a single snippet, capture outputs, enforce a wall-clock budget."""

    def __init__(self, *, timeout_sec: float = 5.0, allow_restricted: bool = True) -> None:
        self.timeout_sec = timeout_sec
        self.allow_restricted = allow_restricted and _HAS_RESTRICTED

    def run(self, code: str, *, inputs: dict[str, Any] | None = None) -> SandboxResult:
        stdout = io.StringIO()
        stderr = io.StringIO()
        start = time.perf_counter()

        try:
            compiled = self._compile(code)
        except SyntaxError as exc:
            return SandboxResult(
                ok=False,
                stderr=f"SyntaxError: {exc}",
                error="syntax",
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

        globals_ns = self._build_globals(inputs or {})

        prev_handler = None
        timer: threading.Timer | None = None
        in_main = threading.current_thread() is threading.main_thread()
        use_signal = hasattr(signal, "SIGALRM") and in_main
        try:
            if use_signal:
                prev_handler = signal.signal(signal.SIGALRM, _alarm_handler)
                signal.setitimer(signal.ITIMER_REAL, self.timeout_sec)
            else:
                # When we are not in the main thread (e.g. FastAPI TestClient
                # workers, ASGI worker pools) ``signal`` is unusable. Fall back
                # to delivering an asynchronous exception into the *current*
                # thread via the CPython C API – this is best-effort and only
                # fires between bytecode instructions, but is the standard
                # technique used by Jupyter and timeout-decorator.
                target_tid = threading.get_ident()

                def _raise_timeout() -> None:
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(
                        ctypes.c_long(target_tid),
                        ctypes.py_object(_Timeout),
                    )

                timer = threading.Timer(self.timeout_sec, _raise_timeout)
                timer.daemon = True
                timer.start()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(compiled, globals_ns)  # noqa: S102 - guarded by RestrictedPython
        except _Timeout:
            return SandboxResult(
                ok=False,
                stdout=stdout.getvalue(),
                stderr=stderr.getvalue(),
                elapsed_ms=(time.perf_counter() - start) * 1000,
                error=f"timeout after {self.timeout_sec:g}s",
            )
        except Exception as exc:  # noqa: BLE001 - expose to caller for teaching
            tb = traceback.format_exc(limit=4)
            return SandboxResult(
                ok=False,
                stdout=stdout.getvalue(),
                stderr=stderr.getvalue() + tb,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                error=type(exc).__name__,
            )
        finally:
            if use_signal and prev_handler is not None:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, prev_handler)
            if timer is not None:
                timer.cancel()
                # Clear any pending async exception we may have queued for the
                # rare case where the timer just fired but exec() already returned.
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(threading.get_ident()),
                    ctypes.c_void_p(0),
                )

        elapsed = (time.perf_counter() - start) * 1000
        # Students expose structured values by assigning to a top-level ``result``
        # binding (RestrictedPython forbids dunder names, so we cannot use
        # ``__result__``). Scalars are auto-boxed into ``{"value": ...}``.
        result_payload = globals_ns.get("result", {})
        if not isinstance(result_payload, dict):
            result_payload = {"value": result_payload}

        return SandboxResult(
            ok=True,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            result=result_payload,
            elapsed_ms=elapsed,
        )

    # ------------------------------------------------------------------ #
    def _compile(self, code: str):
        if self.allow_restricted:
            return compile_restricted(code, filename="<sandbox>", mode="exec")
        return compile(code, "<sandbox>", "exec")

    def _build_globals(self, inputs: dict[str, Any]) -> dict[str, Any]:
        safe_builtins_map: dict[str, Any] = {
            "abs": abs, "min": min, "max": max, "sum": sum, "len": len,
            "range": range, "enumerate": enumerate, "zip": zip,
            "round": round, "sorted": sorted, "list": list, "dict": dict,
            "tuple": tuple, "set": set, "float": float, "int": int,
            "str": str, "bool": bool, "print": print, "isinstance": isinstance,
            "True": True, "False": False, "None": None,
            "__import__": _make_safe_import(),
        }
        if self.allow_restricted:
            safe_builtins_map.update(dict(safe_builtins))
            safe_builtins_map["__import__"] = _make_safe_import()

        globals_ns: dict[str, Any] = {
            "__builtins__": safe_builtins_map,
            "math": math,
            "result": {},
            **inputs,
        }
        if self.allow_restricted:
            globals_ns["_getitem_"] = default_guarded_getitem
            globals_ns["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence
            globals_ns["_unpack_sequence_"] = guarded_unpack_sequence
            globals_ns["_getattr_"] = getattr
            globals_ns["_getiter_"] = iter
            globals_ns["_write_"] = lambda x: x
        return globals_ns
