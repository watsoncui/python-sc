"""Plugin registry for TDA operators.

Why a registry?
---------------
The v0.1 protocol pinned ``pipeline`` to a hard-coded ``Literal["vietoris_rips",
"alpha", "cubical", "mapper"]``. Every time a teacher wants to add (say) a
*Witness complex* or *Sliding-window embedding*, they had to touch:

    1. The Pydantic Literal (breaking schema cache),
    2. The TDAEngine if/else cascade,
    3. The FastAPI route docs,
    4. The front-end dropdown.

This is the classic **Open/Closed Principle violation** – every new operator
forces edits to all four locations.

We refactor towards a tiny **Plugin Registry** (Strategy + Registry design
patterns combined): each operator implements an :class:`Operator` interface
and registers itself with a string ID. The wire protocol carries that ID +
a free-form ``params`` dict; the engine looks up the operator by ID, validates
its parameters via the operator's own JSON schema, and runs it.

Result: adding an operator requires creating *one* file and a *single*
``register_operator(MyOp())`` call – no Pydantic edits, no engine edits.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, ClassVar  # noqa: F401  - ClassVar referenced in subclasses


@dataclass
class OperatorDescriptor:
    """Self-description that the registry exposes to clients."""

    operator_id: str
    title: str
    description: str
    params_schema: dict[str, Any]
    output_homology_dims: list[int] = field(default_factory=lambda: [0, 1])

    # ------------------------------------------------------------------ #
    # Lightweight params validation
    # ------------------------------------------------------------------ #
    # ``params_schema`` is a *tiny* subset of JSON Schema – we only support
    # ``type``, ``default``, ``min``, ``max`` per field. Pulling in the full
    # ``jsonschema`` library would dwarf the rest of the dependency tree;
    # the current shape is enough to (a) auto-fill defaults so engines never
    # see ``KeyError``, and (b) reject the typical student typos
    # (``max_dimension=2.5`` or ``max_edge_length=-1``).
    _TYPE_PY: ClassVar[dict[str, tuple[type, ...]]] = {
        "integer": (int,),
        "number": (int, float),
        "string": (str,),
        "boolean": (bool,),
    }

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Return a *new* params dict with defaults filled in and types coerced.

        Raises :class:`ValueError` on any irrecoverable mismatch. Unknown
        fields are kept as-is (forwards-compat – tomorrow's giotto-tda flag
        should not require touching the engine today).
        """
        out: dict[str, Any] = dict(params or {})
        for name, spec in self.params_schema.items():
            expected_types = self._TYPE_PY.get(spec.get("type", "number"), (int, float))
            if name not in out:
                if "default" in spec:
                    out[name] = spec["default"]
                    continue
                raise ValueError(
                    f"Operator {self.operator_id!r}: missing required param "
                    f"{name!r}."
                )
            value = out[name]
            # bool is a subclass of int; reject the cross-mapping explicitly so
            # `max_dimension=True` doesn't pass as an integer.
            if expected_types == (int,) and isinstance(value, bool):
                raise ValueError(
                    f"Operator {self.operator_id!r}: param {name!r} must be "
                    f"an integer, got bool."
                )
            if not isinstance(value, expected_types):
                raise ValueError(
                    f"Operator {self.operator_id!r}: param {name!r} expected "
                    f"{spec.get('type', 'number')}, got {type(value).__name__}."
                )
            if "min" in spec and value < spec["min"]:
                raise ValueError(
                    f"Operator {self.operator_id!r}: param {name!r}={value} "
                    f"is below the allowed minimum {spec['min']}."
                )
            if "max" in spec and value > spec["max"]:
                raise ValueError(
                    f"Operator {self.operator_id!r}: param {name!r}={value} "
                    f"exceeds the allowed maximum {spec['max']}."
                )
        return out


class Operator(abc.ABC):
    """Abstract base for any TDA / point-cloud operator.

    ``descriptor`` is exposed via ``/tda/operators`` so the front-end can
    render a parameter form *without* hard-coding any operator. The schema
    is a tiny subset of JSON Schema (enough for inputs, types, defaults).
    """

    operator_id: ClassVar[str]

    @abc.abstractmethod
    def descriptor(self) -> OperatorDescriptor: ...

    @abc.abstractmethod
    def run(self, points: "Any", params: dict[str, Any]) -> "Any":
        """Run the operator on a 2D ``points`` ndarray. Implementations decide
        the return type – the engine adapts it to ``PersistenceDiagramPayload``.
        """


class _Registry:
    def __init__(self) -> None:
        self._ops: dict[str, Operator] = {}

    def register(self, op: Operator) -> None:
        if op.operator_id in self._ops:
            raise ValueError(f"Operator {op.operator_id!r} is already registered.")
        self._ops[op.operator_id] = op

    def unregister(self, operator_id: str) -> None:
        self._ops.pop(operator_id, None)

    def get(self, operator_id: str) -> Operator:
        try:
            return self._ops[operator_id]
        except KeyError as exc:
            available = ", ".join(sorted(self._ops)) or "(none)"
            raise KeyError(
                f"Unknown operator {operator_id!r}. Registered: {available}."
            ) from exc

    def descriptors(self) -> list[OperatorDescriptor]:
        return [op.descriptor() for op in self._ops.values()]

    def __contains__(self, operator_id: str) -> bool:
        return operator_id in self._ops


_global_registry = _Registry()


def register_operator(op: Operator) -> None:
    _global_registry.register(op)


def get_operator(operator_id: str) -> Operator:
    return _global_registry.get(operator_id)


def list_operators() -> list[OperatorDescriptor]:
    return _global_registry.descriptors()


def is_registered(operator_id: str) -> bool:
    return operator_id in _global_registry


# Used by tests / hot-reload scenarios to start fresh.
def _reset_registry() -> None:
    global _global_registry  # noqa: PLW0603
    _global_registry = _Registry()
