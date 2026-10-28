"""Unit tests for the agentic code repair orchestrator."""

import json
import os
import tempfile
from pathlib import Path

import httpx
import pytest

from sunny_devfix.agent import (
    AgentState,
    execute_agent_apply,
    execute_agent_rollback,
    run_agent_analysis_and_proposal,
)
from sunny_devfix.providers.nebius import NebiusClient


def test_agent_lifecycle_in_memory():
    # Test lifecycle when no disk path is configured (pure in-memory virtual preview)
    source = "def compute(x):\n    return x + missing\n"
    tb = """Traceback (most recent call last):
  File "test.py", line 2, in compute
    return x + missing
NameError: name 'missing' is not defined"""

    res = run_agent_analysis_and_proposal(source, tb)
    assert res["state"] in {AgentState.AWAITING_APPROVAL.value, AgentState.FAILED.value}
    assert res["timeline"]
    assert res["timeline"][0]["state"] == AgentState.ANALYZED.value


def test_agent_lifecycle_with_approval_and_rollback(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir).resolve()
        target_file = project_root / "service.py"
        before_code = "def get_total(price, tax):\n    return price + tx\n"
        target_file.write_text(before_code, encoding="utf-8")

        monkeypatch.setenv("DEVFIX_PROJECT_ROOTS", str(project_root))

        mock_payload = {
            "root_cause_title": "Typo in tax variable",
            "root_cause_explanation": "tx was referenced instead of tax.",
            "recommended_next_step": "Change tx to tax.",
            "confidence": "high",
            "fix_description": "Correct typo tx to tax.",
            "repaired_source": "def get_total(price, tax):\n    return price + tax\n",
        }

        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"choices": [{"message": {"role": "assistant", "content": json.dumps(mock_payload)}}]},
            )

        transport = httpx.MockTransport(mock_handler)
        client = NebiusClient(api_key="neb-test", enabled=True, transport=transport)

        tb = """Traceback (most recent call last):
  File "service.py", line 2, in get_total
    return price + tx
NameError: name 'tx' is not defined"""

        # Step 1: Propose
        proposal = run_agent_analysis_and_proposal(
            before_code,
            tb,
            filename="service.py",
            project_root=str(project_root),
            relative_path="service.py",
            client=client,
        )

        assert proposal["state"] == AgentState.AWAITING_APPROVAL.value
        assert proposal["patch_preview"] is not None
        approval_token = proposal["patch_preview"].approval_id

        # Step 2: Deny apply without confirmation
        denied = execute_agent_apply(approval_token, confirm=False)
        assert denied["state"] == AgentState.FAILED.value
        assert "Explicit user confirmation is mandatory" in denied["error"]
        assert target_file.read_text(encoding="utf-8") == before_code

        # Step 3: Approve and apply with confirmation
        applied = execute_agent_apply(
            approval_token,
            confirm=True,
            source_before=before_code,
            source_after=proposal["repair"].after_source,
        )
        assert applied["state"] == AgentState.APPLIED.value
        assert target_file.read_text(encoding="utf-8") == "def get_total(price, tax):\n    return price + tax\n"
        rollback_id = applied["patch_result"].rollback_id
        assert rollback_id is not None

        # Step 4: Deny rollback without confirmation
        denied_rb = execute_agent_rollback(rollback_id, confirm=False)
        assert denied_rb["state"] == AgentState.FAILED.value
        assert target_file.read_text(encoding="utf-8") == "def get_total(price, tax):\n    return price + tax\n"

        # Step 5: Roll back with confirmation
        rb_res = execute_agent_rollback(rollback_id, confirm=True)
        assert rb_res["state"] == AgentState.ROLLED_BACK.value
        assert target_file.read_text(encoding="utf-8") == before_code
