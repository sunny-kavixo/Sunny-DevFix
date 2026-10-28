"""Agentic Python Code Repair Orchestrator with state lifecycle and human-in-the-loop safety."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sunny_devfix.analysis.diff import build_unified_diff
from sunny_devfix.analysis.models import TracebackInfo
from sunny_devfix.analysis.source_analysis import analyze_source
from sunny_devfix.analysis.traceback_parser import parse_traceback
from sunny_devfix.patches import (
    PatchError,
    PatchPreview,
    PatchResult,
    apply_patch,
    prepare_patch,
    rollback_patch,
)
from sunny_devfix.providers.nebius import NebiusClient
from sunny_devfix.providers.nvidia_repair import NvidiaRepairResult, run_nvidia_repair
from sunny_devfix.sandbox import EvidenceResult, run_evidence

logger = logging.getLogger("sunny_devfix.agent")


class AgentState(str, Enum):
    """Lifecycle states for the repair agent."""

    IDLE = "IDLE"
    ANALYZED = "ANALYZED"
    PATCH_PROPOSED = "PATCH_PROPOSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPLIED = "APPLIED"
    TESTING = "TESTING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass
class AgentTimelineEvent:
    """Timeline entry recording an agent phase transition."""

    state: AgentState
    timestamp: float
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentSession:
    """Encapsulates one stateful debugging and repair iteration."""

    session_id: str
    state: AgentState
    source_before: str
    traceback_text: str
    target_filename: str | None
    project_root: str | None
    relative_path: str | None
    repair_result: NvidiaRepairResult | None = None
    patch_preview: PatchPreview | None = None
    patch_result: PatchResult | None = None
    evidence_result: EvidenceResult | None = None
    retry_count: int = 0
    max_retries: int = 1
    timeline: list[AgentTimelineEvent] = field(default_factory=list)


def run_agent_analysis_and_proposal(
    source: str,
    traceback_text: str,
    *,
    filename: str | None = None,
    project_root: str | None = None,
    relative_path: str | None = None,
    client: NebiusClient | None = None,
) -> dict[str, Any]:
    """Execute analysis and propose patch, leaving state in AWAITING_APPROVAL or FAILED."""
    timeline: list[dict[str, Any]] = []

    # Phase 1: Local AST & Traceback analysis
    try:
        tb_info: TracebackInfo = parse_traceback(traceback_text)
        src_analysis = analyze_source(source, tb_info, filename=filename)
        timeline.append({
            "state": AgentState.ANALYZED.value,
            "description": f"Analyzed {len(tb_info.frames)} frames; deepest frame at line {src_analysis.target_line or 'unknown'}.",
            "valid_syntax": src_analysis.valid_syntax,
        })
    except Exception as exc:
        return {
            "state": AgentState.FAILED.value,
            "error": f"Initial static analysis failed: {exc}",
            "timeline": timeline,
            "repair": None,
            "patch_preview": None,
        }

    # Phase 2: Query NVIDIA model via Nebius Token Factory
    repair_result: NvidiaRepairResult = run_nvidia_repair(
        source,
        traceback_text,
        filename=filename,
        client=client,
        fallback_on_error=True,
    )

    if not repair_result.available or not repair_result.unified_diff:
        timeline.append({
            "state": AgentState.FAILED.value,
            "description": repair_result.error_message or "No repair could be confidently generated.",
        })
        return {
            "state": AgentState.FAILED.value,
            "repair": repair_result,
            "patch_preview": None,
            "timeline": timeline,
            "error": repair_result.error_message or "No candidate patch available.",
        }

    timeline.append({
        "state": AgentState.PATCH_PROPOSED.value,
        "description": f"Generated patch via {repair_result.provider} ({repair_result.model}).",
        "is_ai_generated": repair_result.is_ai_generated,
        "confidence": repair_result.confidence,
    })

    # Phase 3: Prepare cryptographic patch token if workspace path is authorized
    patch_preview = None
    if project_root and relative_path:
        try:
            patch_preview = prepare_patch(
                project_root=project_root,
                relative_path=relative_path,
                before=source,
                after=repair_result.after_source,
            )
            timeline.append({
                "state": AgentState.AWAITING_APPROVAL.value,
                "description": f"Patch approval token generated for {relative_path}. Awaiting user confirmation.",
                "approval_id": patch_preview.approval_id,
            })
        except PatchError as p_exc:
            logger.info(f"Patch preview preparation withheld: {p_exc}")
            timeline.append({
                "state": AgentState.AWAITING_APPROVAL.value,
                "description": f"In-memory preview ready. Disk patch withheld: {p_exc}",
            })
    else:
        timeline.append({
            "state": AgentState.AWAITING_APPROVAL.value,
            "description": "Virtual patch preview ready for user review (in-memory).",
        })

    return {
        "state": AgentState.AWAITING_APPROVAL.value,
        "repair": repair_result,
        "patch_preview": patch_preview,
        "timeline": timeline,
        "error": None,
    }


def execute_agent_apply(
    approval_token: str,
    *,
    confirm: bool,
    run_sandbox_evidence: bool = False,
    stdin: str = "",
    source_before: str = "",
    source_after: str = "",
) -> dict[str, Any]:
    """Execute human-approved patch application with optional Docker sandbox verification."""
    timeline: list[dict[str, Any]] = []

    if not confirm:
        return {
            "state": AgentState.FAILED.value,
            "error": "Explicit user confirmation is mandatory to apply changes.",
            "timeline": timeline,
        }

    try:
        apply_result = apply_patch(approval_token, confirm=confirm)
        timeline.append({
            "state": AgentState.APPLIED.value,
            "description": f"Applied patch to {apply_result.relative_path}. Rollback token issued.",
            "rollback_id": apply_result.rollback_id,
        })
    except PatchError as exc:
        return {
            "state": AgentState.FAILED.value,
            "error": f"Failed to apply patch: {exc}",
            "timeline": timeline,
        }

    evidence = None
    final_state = AgentState.APPLIED

    # Phase 4: Optional isolated container verification
    if run_sandbox_evidence and source_before and source_after:
        timeline.append({
            "state": AgentState.TESTING.value,
            "description": "Running before/after reproduction in isolated disposable Docker container.",
        })
        evidence = run_evidence(source_before, source_after, stdin=stdin)
        if evidence.available:
            if evidence.scorecard.overall == "verified":
                final_state = AgentState.VERIFIED
                timeline.append({
                    "state": AgentState.VERIFIED.value,
                    "description": "Verification passed: reproduction converted from failing to passing.",
                })
            elif evidence.regression_detected:
                final_state = AgentState.FAILED
                timeline.append({
                    "state": AgentState.FAILED.value,
                    "description": "Regression detected in container test! Immediate rollback recommended.",
                })
            else:
                final_state = AgentState.APPLIED
                timeline.append({
                    "state": AgentState.APPLIED.value,
                    "description": f"Container run completed with status: {evidence.scorecard.overall}.",
                })

    return {
        "state": final_state.value,
        "patch_result": apply_result,
        "evidence": evidence,
        "timeline": timeline,
        "error": None,
    }


def execute_agent_rollback(rollback_token: str, *, confirm: bool) -> dict[str, Any]:
    """Execute single-step rollback of a previously applied patch."""
    timeline: list[dict[str, Any]] = []

    if not confirm:
        return {
            "state": AgentState.FAILED.value,
            "error": "Explicit user confirmation is mandatory to roll back changes.",
            "timeline": timeline,
        }

    try:
        result = rollback_patch(rollback_token, confirm=confirm)
        timeline.append({
            "state": AgentState.ROLLED_BACK.value,
            "description": f"Successfully rolled back file {result.relative_path} to exact pre-patch content.",
        })
        return {
            "state": AgentState.ROLLED_BACK.value,
            "patch_result": result,
            "timeline": timeline,
            "error": None,
        }
    except PatchError as exc:
        return {
            "state": AgentState.FAILED.value,
            "error": f"Rollback failed: {exc}",
            "timeline": timeline,
        }
