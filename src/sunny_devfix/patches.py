"""Approval-bound, project-scoped patch application with one-time rollback."""

from __future__ import annotations

import hashlib
import os
import secrets
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

MAX_PATCH_BYTES = 20_000
APPROVAL_TTL_SECONDS = 300
_patch_lock = threading.Lock()


class PatchError(ValueError):
    """Raised when a patch cannot be prepared, applied, or rolled back safely."""


@dataclass(frozen=True)
class PatchPreview:
    approval_id: str
    relative_path: str
    before_sha256: str
    after_sha256: str
    expires_in_seconds: int


@dataclass(frozen=True)
class PatchResult:
    status: str
    relative_path: str
    rollback_id: str | None = None


@dataclass(frozen=True)
class _Approval:
    root: Path
    target: Path
    relative_path: str
    before: str
    after: str
    expires_at: float


@dataclass(frozen=True)
class _Rollback:
    root: Path
    target: Path
    relative_path: str
    expected_current: str
    restore: str
    expires_at: float


_approvals: dict[str, _Approval] = {}
_rollbacks: dict[str, _Rollback] = {}


def prepare_patch(project_root: str, relative_path: str, before: str, after: str) -> PatchPreview:
    """Validate a patch and return a short-lived approval bound to exact content."""

    _check_text(before, "Original source")
    _check_text(after, "Suggested source")
    if before == after:
        raise PatchError("The suggested source does not change the file.")
    root, target, normalized = _resolve_target(project_root, relative_path)
    current = _read_target(target)
    if current != before:
        raise PatchError("The file changed or does not match the supplied original source.")

    with _patch_lock:
        _prune_expired()
        approval_id = secrets.token_urlsafe(24)
        _approvals[approval_id] = _Approval(
            root=root,
            target=target,
            relative_path=normalized,
            before=before,
            after=after,
            expires_at=time.monotonic() + APPROVAL_TTL_SECONDS,
        )
    return PatchPreview(
        approval_id=approval_id,
        relative_path=normalized,
        before_sha256=_digest(before),
        after_sha256=_digest(after),
        expires_in_seconds=APPROVAL_TTL_SECONDS,
    )


def apply_patch(approval_id: str, *, confirm: bool) -> PatchResult:
    """Apply the exact approved patch once, after explicit confirmation."""

    if not confirm:
        raise PatchError("Explicit confirmation is required before applying a patch.")
    with _patch_lock:
        _prune_expired()
        approval = _approvals.pop(approval_id, None)
    if approval is None:
        raise PatchError("The patch approval is invalid, expired, or already used.")
    _revalidate_target(approval.root, approval.target)
    if _read_target(approval.target) != approval.before:
        raise PatchError("The file changed after preview; prepare a new patch before applying.")

    _atomic_write(approval.target, approval.after)
    rollback_id = secrets.token_urlsafe(24)
    with _patch_lock:
        _rollbacks[rollback_id] = _Rollback(
            root=approval.root,
            target=approval.target,
            relative_path=approval.relative_path,
            expected_current=approval.after,
            restore=approval.before,
            expires_at=time.monotonic() + APPROVAL_TTL_SECONDS,
        )
    return PatchResult("applied", approval.relative_path, rollback_id)


def rollback_patch(rollback_id: str, *, confirm: bool) -> PatchResult:
    """Restore the exact pre-patch content once, unless the file changed again."""

    if not confirm:
        raise PatchError("Explicit confirmation is required before rolling back a patch.")
    with _patch_lock:
        _prune_expired()
        rollback = _rollbacks.pop(rollback_id, None)
    if rollback is None:
        raise PatchError("The rollback is invalid, expired, or already used.")
    _revalidate_target(rollback.root, rollback.target)
    if _read_target(rollback.target) != rollback.expected_current:
        raise PatchError("The file changed after the patch; rollback was withheld.")
    _atomic_write(rollback.target, rollback.restore)
    return PatchResult("rolled-back", rollback.relative_path)


def _configured_roots() -> tuple[Path, ...]:
    raw = os.getenv("DEVFIX_PROJECT_ROOTS", "")
    roots = tuple(Path(item).expanduser().resolve() for item in raw.split(os.pathsep) if item)
    if not roots:
        raise PatchError("Patch writes are disabled; configure DEVFIX_PROJECT_ROOTS first.")
    return roots


def _resolve_target(project_root: str, relative_path: str) -> tuple[Path, Path, str]:
    supplied_root = Path(project_root).expanduser().resolve()
    if supplied_root not in _configured_roots():
        raise PatchError("The project root is not explicitly authorized.")
    candidate = Path(relative_path)
    if candidate.is_absolute() or not candidate.parts:
        raise PatchError("The patch path must be a non-empty relative path.")
    target = (supplied_root / candidate).resolve()
    _revalidate_target(supplied_root, target)
    return supplied_root, target, target.relative_to(supplied_root).as_posix()


def _revalidate_target(root: Path, target: Path) -> None:
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PatchError("The patch path escapes the authorized project root.") from exc
    if not target.is_file():
        raise PatchError("The patch target must be an existing regular file.")


def _read_target(target: Path) -> str:
    try:
        data = target.read_bytes()
        if len(data) > MAX_PATCH_BYTES:
            raise PatchError(f"The patch target exceeds the {MAX_PATCH_BYTES}-byte limit.")
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PatchError("The patch target must be UTF-8 text.") from exc
    except OSError as exc:
        raise PatchError(f"The patch target could not be read: {exc.__class__.__name__}.") from exc


def _atomic_write(target: Path, content: str) -> None:
    mode = target.stat().st_mode
    descriptor, temporary_name = tempfile.mkstemp(prefix=".devfix-", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    except OSError as exc:
        raise PatchError(f"The patch could not be written: {exc.__class__.__name__}.") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _check_text(value: str, label: str) -> None:
    if not isinstance(value, str):
        raise PatchError(f"{label} must be text.")
    if len(value.encode("utf-8")) > MAX_PATCH_BYTES:
        raise PatchError(f"{label} exceeds the {MAX_PATCH_BYTES}-byte limit.")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _prune_expired() -> None:
    now = time.monotonic()
    for store in (_approvals, _rollbacks):
        for token in tuple(store):
            if store[token].expires_at <= now:
                del store[token]
