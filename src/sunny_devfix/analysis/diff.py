"""Build copyable unified diffs without executing source code."""

from __future__ import annotations

from difflib import unified_diff


def build_unified_diff(before: str, after: str) -> str:
    """Return a stable, copyable diff between two source strings."""

    if before == after:
        return ""

    return "".join(
        unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile="before.py",
            tofile="after.py",
        )
    )
