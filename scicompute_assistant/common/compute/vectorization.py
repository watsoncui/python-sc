"""Deterministic vectorization audit helpers for scientific Python snippets."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Literal


Severity = Literal["info", "warn", "error"]


@dataclass(frozen=True)
class VectorizationSuggestion:
    """A single loop-to-array rewrite opportunity."""

    category: str
    severity: Severity
    line_range: tuple[int, int] | None
    rationale: str
    rewritten_snippet: str | None = None


@dataclass(frozen=True)
class VectorizationAuditResult:
    """Structured output returned by :func:`audit_vectorized_code`."""

    summary: str
    suggestions: list[VectorizationSuggestion] = field(default_factory=list)
    refactored_code: str | None = None
    changed: bool = False


@dataclass(frozen=True)
class _Binding:
    loop_name: str
    source_expr: ast.expr
    vector_name: str


class _NameVectorizer(ast.NodeTransformer):
    """Replace scalar loop variables and indexed reads with vector variables."""

    def __init__(
        self,
        name_map: dict[str, str],
        index_name: str | None = None,
        indexed_names: set[str] | None = None,
    ) -> None:
        self._name_map = name_map
        self._index_name = index_name
        self._indexed_names = indexed_names or set()

    def visit_Name(self, node: ast.Name) -> ast.AST:  # noqa: N802 - AST API
        if isinstance(node.ctx, ast.Load) and node.id in self._name_map:
            return ast.copy_location(ast.Name(id=self._name_map[node.id], ctx=node.ctx), node)
        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:  # noqa: N802 - AST API
        self.generic_visit(node)
        if self._index_name is None:
            return node
        if not isinstance(node.value, ast.Name) or node.value.id not in self._indexed_names:
            return node
        if _is_name_slice(node.slice, self._index_name):
            return ast.copy_location(ast.Name(id=node.value.id, ctx=ast.Load()), node)
        return node


def audit_vectorized_code(code: str) -> VectorizationAuditResult:
    """Rewrite common explicit-loop scientific code into NumPy array operations.

    The transformer is intentionally conservative: it only rewrites simple,
    semantics-preserving patterns such as reductions, elementwise appends and
    indexed elementwise assignments. Unsupported code is returned unchanged with
    actionable suggestions rather than speculative edits.
    """

    if not code.strip():
        return VectorizationAuditResult(
            summary="输入代码为空；没有可审计的显式循环。",
            suggestions=[],
            refactored_code="",
            changed=False,
        )

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return VectorizationAuditResult(
            summary=f"代码存在语法错误，无法安全改写：{exc.msg}。",
            suggestions=[
                VectorizationSuggestion(
                    category="api_correctness",
                    severity="error",
                    line_range=(exc.lineno or 1, exc.lineno or 1),
                    rationale="先修复语法错误，再进行向量化审计。",
                )
            ],
            refactored_code=None,
            changed=False,
        )

    transformer = _VectorizingFunctionTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    suggestions = transformer.suggestions
    changed = transformer.changed
    if changed and not _has_numpy_import(new_tree):
        new_tree.body.insert(0, ast.Import(names=[ast.alias(name="numpy", asname="np")]))
        ast.fix_missing_locations(new_tree)

    if changed:
        refactored_code = ast.unparse(new_tree)
        summary = f"已将 {transformer.rewrite_count} 处显式循环改写为 NumPy 张量运算。"
    else:
        refactored_code = code
        loop_count = sum(isinstance(node, ast.For) for node in ast.walk(tree))
        summary = (
            "检测到显式循环，但未匹配到保守可自动改写的模式。"
            if loop_count
            else "未检测到需要向量化的显式 for 循环。"
        )
        if loop_count:
            suggestions.append(
                VectorizationSuggestion(
                    category="vectorization",
                    severity="warn",
                    line_range=None,
                    rationale=(
                        "可优先尝试 np.sum、np.mean、np.einsum、np.where 或广播表达式；"
                        "复杂依赖循环需要人工确认数据依赖。"
                    ),
                )
            )

    return VectorizationAuditResult(
        summary=summary,
        suggestions=suggestions,
        refactored_code=refactored_code,
        changed=changed,
    )


class _VectorizingFunctionTransformer(ast.NodeTransformer):
    def __init__(self) -> None:
        self.suggestions: list[VectorizationSuggestion] = []
        self.changed = False
        self.rewrite_count = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # noqa: N802 - AST API
        self.generic_visit(node)
        new_body: list[ast.stmt] = []
        i = 0
        while i < len(node.body):
            replacement = self._rewrite_reduction(node.body, i)
            if replacement is None:
                replacement = self._rewrite_append_map(node.body, i)
            if replacement is None:
                replacement = self._rewrite_indexed_assignment(node.body, i)

            if replacement is None:
                new_body.append(node.body[i])
                i += 1
                continue

            statements, consumed, suggestion = replacement
            new_body.extend(statements)
            self.suggestions.append(suggestion)
            self.changed = True
            self.rewrite_count += 1
            i += consumed

        node.body = new_body
        return node

    def _rewrite_reduction(
        self,
        body: list[ast.stmt],
        index: int,
    ) -> tuple[list[ast.stmt], int, VectorizationSuggestion] | None:
        if index + 2 >= len(body):
            return None
        init_stmt, loop_stmt, return_stmt = body[index : index + 3]
        if not isinstance(init_stmt, ast.Assign) or len(init_stmt.targets) != 1:
            return None
        if not isinstance(init_stmt.targets[0], ast.Name):
            return None
        accumulator = init_stmt.targets[0].id
        if not _is_numeric_zero(init_stmt.value):
            return None
        if not isinstance(loop_stmt, ast.For) or len(loop_stmt.body) != 1:
            return None
        loop_line = getattr(loop_stmt, "lineno", None)
        if not isinstance(return_stmt, ast.Return) or not _is_name_expr(return_stmt.value, accumulator):
            return None
        aug = loop_stmt.body[0]
        if not isinstance(aug, ast.AugAssign) or not isinstance(aug.op, ast.Add):
            return None
        if not isinstance(aug.target, ast.Name) or aug.target.id != accumulator:
            return None

        bindings = _bindings_from_iter(loop_stmt.target, loop_stmt.iter)
        if not bindings:
            return None
        expr = _vectorize_expr(aug.value, bindings)
        vector_setup = _sanitizing_assignments(bindings)
        sum_call = ast.Call(
            func=ast.Attribute(value=ast.Name(id="np", ctx=ast.Load()), attr="sum", ctx=ast.Load()),
            args=[expr],
            keywords=[],
        )
        statements: list[ast.stmt] = [
            *vector_setup,
            ast.Return(value=ast.Call(func=ast.Name(id="float", ctx=ast.Load()), args=[sum_call], keywords=[])),
        ]
        snippet = "\n".join(ast.unparse(stmt) for stmt in statements)
        return (
            statements,
            3,
            VectorizationSuggestion(
                category="vectorization",
                severity="info",
                line_range=(loop_line or 1, getattr(loop_stmt, "end_lineno", loop_line or 1)),
                rationale="显式累加循环可由 np.sum 在连续数组上完成，减少 Python 解释器开销。",
                rewritten_snippet=snippet,
            ),
        )

    def _rewrite_append_map(
        self,
        body: list[ast.stmt],
        index: int,
    ) -> tuple[list[ast.stmt], int, VectorizationSuggestion] | None:
        if index + 2 >= len(body):
            return None
        init_stmt, loop_stmt, return_stmt = body[index : index + 3]
        if not _is_empty_list_assign(init_stmt):
            return None
        target_name = init_stmt.targets[0].id  # type: ignore[union-attr]
        if not isinstance(loop_stmt, ast.For) or len(loop_stmt.body) != 1:
            return None
        if not isinstance(return_stmt, ast.Return) or not _is_name_expr(return_stmt.value, target_name):
            return None
        append_stmt = loop_stmt.body[0]
        if not isinstance(append_stmt, ast.Expr) or not isinstance(append_stmt.value, ast.Call):
            return None
        call = append_stmt.value
        if not _is_append_call(call, target_name) or len(call.args) != 1:
            return None

        bindings = _bindings_from_iter(loop_stmt.target, loop_stmt.iter)
        if not bindings:
            return None
        expr = _vectorize_expr(call.args[0], bindings)
        statements: list[ast.stmt] = [*_sanitizing_assignments(bindings), ast.Return(value=expr)]
        snippet = "\n".join(ast.unparse(stmt) for stmt in statements)
        loop_line = getattr(loop_stmt, "lineno", None)
        return (
            statements,
            3,
            VectorizationSuggestion(
                category="vectorization",
                severity="info",
                line_range=(loop_line or 1, getattr(loop_stmt, "end_lineno", loop_line or 1)),
                rationale="逐元素 append 可改写为广播表达式，直接返回 ndarray。",
                rewritten_snippet=snippet,
            ),
        )

    def _rewrite_indexed_assignment(
        self,
        body: list[ast.stmt],
        index: int,
    ) -> tuple[list[ast.stmt], int, VectorizationSuggestion] | None:
        if index + 2 >= len(body):
            return None
        init_stmt, loop_stmt, return_stmt = body[index : index + 3]
        if not isinstance(init_stmt, ast.Assign) or len(init_stmt.targets) != 1:
            return None
        if not isinstance(init_stmt.targets[0], ast.Name):
            return None
        output_name = init_stmt.targets[0].id
        if not isinstance(loop_stmt, ast.For) or len(loop_stmt.body) != 1:
            return None
        if not isinstance(loop_stmt.target, ast.Name):
            return None
        index_name = loop_stmt.target.id
        length_source = _range_len_source(loop_stmt.iter)
        if length_source is None:
            return None
        if not isinstance(return_stmt, ast.Return) or not _is_name_expr(return_stmt.value, output_name):
            return None
        assign_stmt = loop_stmt.body[0]
        if not isinstance(assign_stmt, ast.Assign) or len(assign_stmt.targets) != 1:
            return None
        target = assign_stmt.targets[0]
        if not (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id == output_name
            and _is_name_slice(target.slice, index_name)
        ):
            return None

        indexed_names = _indexed_names(assign_stmt.value, index_name)
        if not indexed_names:
            indexed_names = {length_source}
        bindings = [
            _Binding(loop_name=name, source_expr=ast.Name(id=name, ctx=ast.Load()), vector_name=name)
            for name in sorted(indexed_names)
        ]
        expr = _vectorize_indexed_expr(assign_stmt.value, index_name, indexed_names)
        statements: list[ast.stmt] = [*_sanitizing_assignments(bindings), ast.Return(value=expr)]
        snippet = "\n".join(ast.unparse(stmt) for stmt in statements)
        loop_line = getattr(loop_stmt, "lineno", None)
        return (
            statements,
            3,
            VectorizationSuggestion(
                category="vectorization",
                severity="info",
                line_range=(loop_line or 1, getattr(loop_stmt, "end_lineno", loop_line or 1)),
                rationale="按下标逐元素写入可改写为数组广播表达式，避免 Python 层循环。",
                rewritten_snippet=snippet,
            ),
        )


def _bindings_from_iter(target: ast.expr, iterator: ast.expr) -> list[_Binding]:
    if isinstance(target, ast.Name):
        if isinstance(iterator, ast.Call) and _call_name(iterator.func) == "zip":
            return []
        source = iterator
        vector_name = iterator.id if isinstance(iterator, ast.Name) else f"{target.id}_array"
        return [_Binding(loop_name=target.id, source_expr=source, vector_name=vector_name)]

    if isinstance(target, ast.Tuple):
        if not isinstance(iterator, ast.Call) or _call_name(iterator.func) != "zip":
            return []
        if len(target.elts) != len(iterator.args):
            return []
        bindings: list[_Binding] = []
        for target_elt, source_expr in zip(target.elts, iterator.args, strict=True):
            if not isinstance(target_elt, ast.Name):
                return []
            vector_name = source_expr.id if isinstance(source_expr, ast.Name) else f"{target_elt.id}_array"
            bindings.append(
                _Binding(
                    loop_name=target_elt.id,
                    source_expr=source_expr,
                    vector_name=vector_name,
                )
            )
        return bindings
    return []


def _vectorize_expr(expr: ast.expr, bindings: list[_Binding]) -> ast.expr:
    mapper = {binding.loop_name: binding.vector_name for binding in bindings}
    new_expr = _NameVectorizer(mapper).visit(ast.fix_missing_locations(ast.copy_location(expr, expr)))
    return ast.fix_missing_locations(new_expr)  # type: ignore[return-value]


def _vectorize_indexed_expr(expr: ast.expr, index_name: str, indexed_names: set[str]) -> ast.expr:
    new_expr = _NameVectorizer({}, index_name=index_name, indexed_names=indexed_names).visit(expr)
    return ast.fix_missing_locations(new_expr)  # type: ignore[return-value]


def _sanitizing_assignments(bindings: list[_Binding]) -> list[ast.Assign]:
    statements: list[ast.Assign] = []
    seen: set[str] = set()
    for binding in bindings:
        if binding.vector_name in seen:
            continue
        seen.add(binding.vector_name)
        array_call = ast.Call(
            func=ast.Attribute(value=ast.Name(id="np", ctx=ast.Load()), attr="asarray", ctx=ast.Load()),
            args=[binding.source_expr],
            keywords=[
                ast.keyword(
                    arg="dtype",
                    value=ast.Attribute(
                        value=ast.Name(id="np", ctx=ast.Load()),
                        attr="float64",
                        ctx=ast.Load(),
                    ),
                )
            ],
        )
        clean_call = ast.Call(
            func=ast.Attribute(value=ast.Name(id="np", ctx=ast.Load()), attr="nan_to_num", ctx=ast.Load()),
            args=[array_call],
            keywords=[
                ast.keyword(arg="nan", value=ast.Constant(value=0.0)),
                ast.keyword(arg="posinf", value=ast.Constant(value=0.0)),
                ast.keyword(arg="neginf", value=ast.Constant(value=0.0)),
            ],
        )
        statements.append(
            ast.Assign(
                targets=[ast.Name(id=binding.vector_name, ctx=ast.Store())],
                value=clean_call,
            )
        )
    return statements


def _has_numpy_import(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "numpy" and alias.asname == "np":
                    return True
        if isinstance(node, ast.ImportFrom) and node.module == "numpy":
            return True
    return False


def _is_numeric_zero(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and node.value == 0


def _is_empty_list_assign(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.List)
        and len(node.value.elts) == 0
    )


def _is_append_call(call: ast.Call, target_name: str) -> bool:
    return (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "append"
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == target_name
    )


def _is_name_expr(node: ast.AST | None, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _is_name_slice(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None


def _range_len_source(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call) or _call_name(node.func) != "range" or len(node.args) != 1:
        return None
    len_call = node.args[0]
    if not isinstance(len_call, ast.Call) or _call_name(len_call.func) != "len" or len(len_call.args) != 1:
        return None
    source = len_call.args[0]
    return source.id if isinstance(source, ast.Name) else None


def _indexed_names(node: ast.AST, index_name: str) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Subscript)
            and isinstance(child.value, ast.Name)
            and _is_name_slice(child.slice, index_name)
        ):
            names.add(child.value.id)
    return names
