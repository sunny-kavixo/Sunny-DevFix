"""Fast, conservative, non-executing diagnostics for code as it is typed."""

from __future__ import annotations

import ast
import builtins

from sunny_devfix.analysis.insights import build_insights
from sunny_devfix.analysis.models import (
    FixSuggestion,
    GuardianAnalysis,
    GuardianDiagnostic,
    TracebackFrame,
    TracebackInfo,
)
from sunny_devfix.analysis.source_analysis import analyze_source

_BUILTIN_NAMES = set(dir(builtins))


def diagnose_source(source: str) -> GuardianAnalysis:
    """Return diagnostics without importing or executing the submitted source."""

    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()
    source_analysis = analyze_source(normalized)
    if source_analysis.syntax_error is not None:
        diagnostic = source_analysis.syntax_error
        line_number = diagnostic.line_number or 1
        traceback_info = _synthetic_traceback(
            "SyntaxError", diagnostic.message, line_number
        )
        insights = build_insights(normalized, traceback_info, source_analysis)
        return GuardianAnalysis(
            valid_syntax=False,
            line_count=len(lines),
            diagnostics=(
                GuardianDiagnostic(
                    code="syntax-error",
                    message=diagnostic.message,
                    explanation=insights.root_cause.explanation,
                    line_number=line_number,
                    column=diagnostic.column,
                    severity="error",
                    confidence=insights.root_cause.confidence,
                    fix=insights.suggestion,
                ),
            ),
        )

    tree = ast.parse(normalized, filename="<guardian>")
    defined = _defined_names(tree)
    diagnostics: list[GuardianDiagnostic] = []
    seen: set[tuple[str, int, int | None]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in defined or node.id in _BUILTIN_NAMES:
                continue
            key = ("undefined-name", node.lineno, node.col_offset)
            if key in seen:
                continue
            seen.add(key)
            fix = _name_error_fix(normalized, node.id, node.lineno)
            diagnostics.append(
                GuardianDiagnostic(
                    code="undefined-name",
                    message=f"Name '{node.id}' may be undefined here.",
                    explanation=(
                        "Python will look for this name at runtime, but no local "
                        "definition or import was found in the supplied source."
                    ),
                    line_number=node.lineno,
                    column=node.col_offset + 1,
                    severity="error",
                    confidence="high" if fix and fix.available else "medium",
                    fix=fix,
                )
            )

    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp) or not isinstance(
            node.op, (ast.Div, ast.FloorDiv, ast.Mod)
        ):
            continue
        if not isinstance(node.right, ast.Constant) or node.right.value != 0:
            continue
        key = ("division-by-zero", node.lineno, node.col_offset)
        if key in seen:
            continue
        seen.add(key)
        diagnostics.append(
            GuardianDiagnostic(
                code="division-by-zero",
                message="This operation divides by zero on every execution.",
                explanation=(
                    "The denominator is the literal 0, so this expression will "
                    "raise ZeroDivisionError when reached."
                ),
                line_number=node.lineno,
                column=node.col_offset + 1,
                severity="warning",
                confidence="high",
            )
        )

    diagnostics.sort(key=lambda item: (item.line_number, item.column or 0))
    return GuardianAnalysis(
        valid_syntax=True,
        line_count=len(lines),
        diagnostics=tuple(diagnostics),
    )


def _name_error_fix(
    source: str,
    name: str,
    line_number: int,
) -> FixSuggestion | None:
    traceback_info = _synthetic_traceback(
        "NameError", f"name '{name}' is not defined", line_number
    )
    targeted_analysis = analyze_source(source, traceback_info)
    return build_insights(source, traceback_info, targeted_analysis).suggestion


def _synthetic_traceback(
    exception_type: str, message: str, line_number: int
) -> TracebackInfo:
    return TracebackInfo(
        exception_type=exception_type,
        message=message,
        frames=(
            TracebackFrame(
                filename="<guardian>",
                line_number=line_number,
                function="<module>",
            ),
        ),
        raw="",
    )


def _defined_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".", 1)[0])
    return names
