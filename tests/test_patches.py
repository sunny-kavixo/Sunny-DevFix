from pathlib import Path

import pytest

from sunny_devfix.patches import PatchError, apply_patch, prepare_patch, rollback_patch


def authorize(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setenv("DEVFIX_PROJECT_ROOTS", str(root))


def test_patch_requires_authorized_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "app.py"
    target.write_text("before\n")
    monkeypatch.delenv("DEVFIX_PROJECT_ROOTS", raising=False)

    with pytest.raises(PatchError, match="disabled"):
        prepare_patch(str(tmp_path), "app.py", "before\n", "after\n")


def test_patch_rejects_traversal_and_symlink_escape(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("before\n")
    (root / "link.py").symlink_to(outside)
    authorize(monkeypatch, root)

    for path in ("../outside.py", "link.py"):
        with pytest.raises(PatchError, match="escapes"):
            prepare_patch(str(root), path, "before\n", "after\n")


def test_patch_apply_and_one_time_rollback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "app.py"
    target.write_text("before\n")
    authorize(monkeypatch, tmp_path)
    preview = prepare_patch(str(tmp_path), "app.py", "before\n", "after\n")

    with pytest.raises(PatchError, match="confirmation"):
        apply_patch(preview.approval_id, confirm=False)
    result = apply_patch(preview.approval_id, confirm=True)
    assert target.read_text() == "after\n"
    assert result.status == "applied"
    assert result.rollback_id

    rolled_back = rollback_patch(result.rollback_id or "", confirm=True)
    assert rolled_back.status == "rolled-back"
    assert target.read_text() == "before\n"
    with pytest.raises(PatchError, match="already used"):
        rollback_patch(result.rollback_id or "", confirm=True)


def test_patch_is_withheld_when_file_changes_after_preview(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "app.py"
    target.write_text("before\n")
    authorize(monkeypatch, tmp_path)
    preview = prepare_patch(str(tmp_path), "app.py", "before\n", "after\n")
    target.write_text("user edit\n")

    with pytest.raises(PatchError, match="changed after preview"):
        apply_patch(preview.approval_id, confirm=True)
    assert target.read_text() == "user edit\n"


def test_rollback_is_withheld_when_file_changes_again(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "app.py"
    target.write_text("before\n")
    authorize(monkeypatch, tmp_path)
    preview = prepare_patch(str(tmp_path), "app.py", "before\n", "after\n")
    result = apply_patch(preview.approval_id, confirm=True)
    target.write_text("newer user edit\n")

    with pytest.raises(PatchError, match="changed after the patch"):
        rollback_patch(result.rollback_id or "", confirm=True)
    assert target.read_text() == "newer user edit\n"
