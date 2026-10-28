import json
from pathlib import Path
import pytest

from sunny_devfix.patches import (
    prepare_patch,
    apply_patch,
    rollback_patch,
    PatchError,
)

def test_cloud_generated_repair_full_lifecycle(monkeypatch, tmp_path):
    # 1. Load the authentic live inference evidence record
    record_path = Path("docs/hackathon/LIVE_INFERENCE_RECORD.json")
    assert record_path.exists(), "LIVE_INFERENCE_RECORD.json must exist"
    record = json.loads(record_path.read_text(encoding="utf-8"))

    assert record["provider"] == "Nebius Token Factory"
    assert record["is_ai_generated"] is True
    assert "Nemotron" in record["model"]
    assert record["syntax_valid"] is True
    assert record["root_cause_title"] == "Variable name mismatch"

    # Original buggy code as diagnosed by Nebius/NVIDIA
    buggy_source = """def compute_discount(price, rate):
    discount = price * rte
    return price - discount

print(compute_discount(100, 0.15))
"""
    repaired_source = record["after_source"]

    # 2. Setup disposable authorized target in temporary workspace
    monkeypatch.setenv("DEVFIX_PROJECT_ROOTS", str(tmp_path))
    target_path = tmp_path / "pricing.py"
    target_path.write_text(buggy_source, encoding="utf-8")
    original_bytes = target_path.read_bytes()

    # 3. Preview cloud-generated patch
    preview = prepare_patch(
        project_root=str(tmp_path),
        relative_path="pricing.py",
        before=buggy_source,
        after=repaired_source,
    )
    assert preview.approval_id is not None
    assert preview.relative_path == "pricing.py"

    # 4. Enforce Human-in-the-Loop Approval Barrier
    # Attempting apply without confirmation must fail
    with pytest.raises(PatchError, match="confirmation"):
        apply_patch(preview.approval_id, confirm=False)

    # 5. Apply with valid preview token (authorized approval)
    receipt = apply_patch(preview.approval_id, confirm=True)
    assert receipt.status == "applied"
    assert receipt.rollback_id is not None

    # Verify disk write: contains NVIDIA-generated fix
    modified_content = target_path.read_text(encoding="utf-8")
    assert "discount = price * rate" in modified_content
    assert "discount = price * rte" not in modified_content

    # 6. Execute Rollback
    rollback_receipt = rollback_patch(receipt.rollback_id, confirm=True)
    assert rollback_receipt.status == "rolled-back"

    # Verify disk restored byte-for-byte
    assert target_path.read_bytes() == original_bytes
