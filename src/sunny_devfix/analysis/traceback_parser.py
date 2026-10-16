"""Parse Python traceback text without importing or executing user code."""

from __future__ import annotations

import re

from sunny_devfix.analysis.models import (
    InputLimitError,
    TracebackFrame,
    TracebackInfo,
    TracebackParseError,
)

MAX_TRACEBACK_BYTES = 20_000

_FRAME_RE = re.compile(
    r'^\s*File "(?P<filename>.+?)", line (?P<line>\d+)'
    r'(?:, in (?P<function>.+?))?\s*$'
)
_EXCEPTION_RE = re.compile(
    r'^(?P<name>(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)'
    r'(?::\s*(?P<message>.*))?$'
)
_KNOWN_EXCEPTIONS = {
    "BaseException",
    "Exception",
    "GeneratorExit",
    "KeyboardInterrupt",
    "SystemExit",
    "StopAsyncIteration",
    "StopIteration",
}


def parse_traceback(raw: str, *, max_bytes: int = MAX_TRACEBACK_BYTES) -> TracebackInfo:
    """Return structured traceback data from bounded text.

    This function treats traceback text as data only. It never imports a
    referenced module, opens a referenced filename, or executes source code.
    """

    if not isinstance(raw, str):
        raise TracebackParseError("Traceback input must be text.")

    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    _check_size(normalized, max_bytes)
    if not normalized.strip():
        raise TracebackParseError("Traceback input is empty.")

    lines = normalized.splitlines()
    frames = tuple(_parse_frames(lines))
    exception = _find_exception(lines)
    if exception is None:
        raise TracebackParseError("No recognizable Python exception was found.")

    exception_type, message = exception
    return TracebackInfo(
        exception_type=exception_type,
        message=message,
        frames=frames,
        raw=normalized,
    )


def _check_size(text: str, max_bytes: int) -> None:
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive.")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise TracebackParseError("Traceback input is not valid UTF-8 text.") from exc
    if size > max_bytes:
        raise InputLimitError(
            f"Traceback input exceeds the {max_bytes}-byte limit."
        )


def _parse_frames(lines: list[str]) -> list[TracebackFrame]:
    frames: list[TracebackFrame] = []
    for index, line in enumerate(lines):
        match = _FRAME_RE.match(line)
        if match is None:
            continue

        source_line = None
        if index + 1 < len(lines):
            candidate = lines[index + 1]
            stripped = candidate.strip()
            if (
                stripped
                and candidate != candidate.lstrip()
                and not stripped.startswith('File "')
                and not stripped.startswith("Traceback (")
            ):
                source_line = stripped

        frames.append(
            TracebackFrame(
                filename=match.group("filename"),
                line_number=int(match.group("line")),
                function=match.group("function") or "<unknown>",
                source_line=source_line,
            )
        )
    return frames


def _find_exception(lines: list[str]) -> tuple[str, str] | None:
    for line in reversed(lines):
        if not line or line != line.lstrip():
            continue
        match = _EXCEPTION_RE.match(line)
        if match is None:
            continue

        name = match.group("name")
        short_name = name.rsplit(".", 1)[-1]
        if not _looks_like_exception(short_name, name):
            continue
        return name, match.group("message") or ""
    return None


def _looks_like_exception(short_name: str, qualified_name: str) -> bool:
    return (
        short_name in _KNOWN_EXCEPTIONS
        or short_name.endswith(("Error", "Exception", "Warning"))
        or ("." in qualified_name and short_name[:1].isupper())
    )
