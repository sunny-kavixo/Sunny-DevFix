"""Validate source syntax and map a traceback location to source context."""

from __future__ import annotations

import ast

from sunny_devfix.analysis.models import (
    InputLimitError,
    SourceAnalysis,
    SourceLine,
    SyntaxDiagnostic,
    TracebackInfo,
)

MAX_SOURCE_BYTES = 20_000
DEFAULT_CONTEXT_RADIUS = 2


def analyze_source(
    source: str,
    traceback_info: TracebackInfo | None = None,
    *,
    filename: str = "<submitted>",
    context_radius: int = DEFAULT_CONTEXT_RADIUS,
    max_bytes: int = MAX_SOURCE_BYTES,
) -> SourceAnalysis:
    """Parse source and return a bounded context window around its target.

    Parsing uses :func:`ast.parse` only. It does not import modules or execute
    any submitted code.
    """

    if not isinstance(source, str):
        raise TypeError("Source input must be text.")
    if context_radius < 0:
        raise ValueError("context_radius must not be negative.")

    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    _check_size(normalized, max_bytes)
    lines = normalized.splitlines()

    syntax_error = _parse_syntax(normalized, filename)
    target_line, warnings = _target_line(
        traceback_info=traceback_info,
        syntax_error=syntax_error,
        line_count=len(lines),
    )
    context = _context_window(lines, target_line, context_radius)

    return SourceAnalysis(
        valid_syntax=syntax_error is None,
        line_count=len(lines),
        target_line=target_line,
        context=context,
        syntax_error=syntax_error,
        warnings=tuple(warnings),
    )


def _check_size(text: str, max_bytes: int) -> None:
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive.")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise InputLimitError("Source input is not valid UTF-8 text.") from exc
    if size > max_bytes:
        raise InputLimitError(f"Source input exceeds the {max_bytes}-byte limit.")


def _parse_syntax(source: str, filename: str) -> SyntaxDiagnostic | None:
    try:
        ast.parse(source, filename=filename)
    except SyntaxError as exc:
        return SyntaxDiagnostic(
            message=exc.msg or "Invalid Python syntax.",
            line_number=exc.lineno,
            column=exc.offset,
            source_line=(exc.text or "").strip() or None,
        )
    except (TypeError, ValueError) as exc:
        return SyntaxDiagnostic(message=str(exc) or "Source could not be parsed.")
    return None


def _target_line(
    *,
    traceback_info: TracebackInfo | None,
    syntax_error: SyntaxDiagnostic | None,
    line_count: int,
) -> tuple[int | None, list[str]]:
    warnings: list[str] = []
    candidate: int | None = None

    if traceback_info is not None and traceback_info.deepest_frame is not None:
        candidate = traceback_info.deepest_frame.line_number
    elif syntax_error is not None:
        candidate = syntax_error.line_number

    if candidate is None:
        if line_count:
            warnings.append("No traceback frame or syntax location was supplied.")
        return None, warnings

    if not 1 <= candidate <= line_count:
        warnings.append(
            f"Traceback line {candidate} is outside the supplied source ({line_count} lines)."
        )
        return None, warnings
    return candidate, warnings


def _context_window(
    lines: list[str], target_line: int | None, context_radius: int
) -> tuple[SourceLine, ...]:
    if target_line is None:
        return ()
    start = max(1, target_line - context_radius)
    end = min(len(lines), target_line + context_radius)
    return tuple(
        SourceLine(
            line_number=line_number,
            text=lines[line_number - 1],
            is_target=line_number == target_line,
        )
        for line_number in range(start, end + 1)
    )
