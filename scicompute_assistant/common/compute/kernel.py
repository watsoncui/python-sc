"""High-level compute facade used by FastAPI routers.

Wraps the lower-level :class:`Sandbox` and exposes:

* ``run_code`` – generic execution with stdout/stderr capture.
* ``run_with_dataset`` – passes a NumPy array into the sandbox namespace.

Heavy lifting (TDA, ODE solvers, etc.) lives in dedicated modules; this
facade is intentionally thin so the route layer stays trivial.
"""

from __future__ import annotations

from typing import Any

from .sandbox import Sandbox, SandboxResult


class ComputeKernel:
    def __init__(self, *, timeout_sec: float = 5.0, restricted: bool = True) -> None:
        self._timeout = timeout_sec
        self._restricted = restricted

    def run_code(
        self,
        code: str,
        *,
        inputs: dict[str, Any] | None = None,
        timeout_sec: float | None = None,
    ) -> SandboxResult:
        sandbox = Sandbox(
            timeout_sec=timeout_sec if timeout_sec is not None else self._timeout,
            allow_restricted=self._restricted,
        )
        return sandbox.run(code, inputs=inputs or {})
