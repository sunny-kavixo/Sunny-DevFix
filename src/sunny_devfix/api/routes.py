"""FastAPI routes for local-first traceback analysis."""

from fastapi import APIRouter, HTTPException

from sunny_devfix.analysis.models import (
    AnalysisInputError,
    AnalysisInsights,
    CodeComparison,
    FixSuggestion,
    RootCauseExplanation,
    SourceAnalysis,
    SyntaxDiagnostic,
    TracebackFrame,
    TracebackParseError,
)
from sunny_devfix.analysis.guardian import diagnose_source
from sunny_devfix.analysis.insights import build_insights
from sunny_devfix.analysis.source_analysis import analyze_source
from sunny_devfix.analysis.traceback_parser import parse_traceback
from sunny_devfix.api.schemas import (
    AgentApplyRequest,
    AgentApplyResponse,
    AgentRepairRequest,
    AgentRepairResponse,
    AgentRepairResultResponse,
    AgentTimelineItem,
    AnalyzeRequest,
    AnalyzeResponse,
    CodeComparisonResponse,
    FixSuggestionResponse,
    EvidenceRequest,
    EvidenceResponse,
    EvidenceScorecardResponse,
    GuardianDiagnosticResponse,
    GuardianRequest,
    GuardianResponse,
    ModelInfoResponse,
    SandboxRunResponse,
    PatchActionRequest,
    PatchActionResponse,
    PatchPreviewRequest,
    PatchPreviewResponse,
    RootCauseResponse,
    SafetyResponse,
    SourceAnalysisResponse,
    SourceLineResponse,
    SyntaxDiagnosticResponse,
    TracebackFrameResponse,
)
from sunny_devfix.agent import (
    execute_agent_apply,
    execute_agent_rollback,
    run_agent_analysis_and_proposal,
)
from sunny_devfix.patches import PatchError, apply_patch, prepare_patch, rollback_patch
from sunny_devfix.providers.nebius import NebiusClient
from sunny_devfix.sandbox import (
    EvidenceResult,
    SandboxRun,
    confirmation_required_result,
    run_evidence,
)

router = APIRouter(prefix="/api")


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    """Parse a traceback and map its deepest frame to submitted source."""

    try:
        traceback_info = parse_traceback(payload.traceback)
        source_analysis = analyze_source(
            payload.source,
            traceback_info,
            filename=payload.filename,
            context_radius=payload.context_radius,
        )
        insights = build_insights(payload.source, traceback_info, source_analysis)
    except (AnalysisInputError, TracebackParseError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    frames = [_frame_response(frame) for frame in traceback_info.frames]
    deepest_frame = frames[-1] if frames else None
    return AnalyzeResponse(
        exception_type=traceback_info.exception_type,
        message=traceback_info.message,
        frames=frames,
        deepest_frame=deepest_frame,
        source_analysis=_source_response(source_analysis),
        root_cause=_root_cause_response(insights),
        suggestion=_suggestion_response(insights),
        safety=SafetyResponse(
            executed=False,
            message=(
                "Analysis only: the submitted source was parsed, never imported "
                "or executed."
            ),
        ),
    )


@router.post("/guardian", response_model=GuardianResponse)
def guardian(payload: GuardianRequest) -> GuardianResponse:
    """Run bounded diagnostics while a user is editing source."""

    try:
        result = diagnose_source(payload.source)
    except (AnalysisInputError, SyntaxError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return GuardianResponse(
        valid_syntax=result.valid_syntax,
        line_count=result.line_count,
        diagnostics=[
            GuardianDiagnosticResponse(
                code=item.code,
                message=item.message,
                explanation=item.explanation,
                line_number=item.line_number,
                column=item.column,
                severity=item.severity,
                confidence=item.confidence,
                fix=(
                    _suggestion_response_from_fix(item.fix)
                    if item.fix is not None
                    else None
                ),
            )
            for item in result.diagnostics
        ],
    )


@router.post("/evidence", response_model=EvidenceResponse)
def evidence(payload: EvidenceRequest) -> EvidenceResponse:
    """Run an explicitly confirmed before/after Docker reproduction."""

    if not payload.confirm:
        return _evidence_response(confirmation_required_result())
    return _evidence_response(
        run_evidence(
            payload.source_before,
            payload.source_after,
            stdin=payload.stdin,
            timeout_seconds=payload.timeout_seconds,
        )
    )


@router.post("/patches/preview", response_model=PatchPreviewResponse)
def patch_preview(payload: PatchPreviewRequest) -> PatchPreviewResponse:
    """Validate a patch without writing and bind approval to its exact content."""

    try:
        preview = prepare_patch(
            payload.project_root, payload.relative_path, payload.before, payload.after
        )
    except PatchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PatchPreviewResponse(**preview.__dict__)


@router.post("/patches/apply", response_model=PatchActionResponse)
def patch_apply(payload: PatchActionRequest) -> PatchActionResponse:
    """Apply one prepared patch after explicit confirmation."""

    try:
        result = apply_patch(payload.token, confirm=payload.confirm)
    except PatchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PatchActionResponse(**result.__dict__)


@router.post("/patches/rollback", response_model=PatchActionResponse)
def patch_rollback(payload: PatchActionRequest) -> PatchActionResponse:
    """Rollback one applied patch after explicit confirmation."""

    try:
        result = rollback_patch(payload.token, confirm=payload.confirm)
    except PatchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PatchActionResponse(**result.__dict__)


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    """Return runtime configuration and diagnostic metadata for Nebius & NVIDIA models."""
    client = NebiusClient()
    diag = client.get_diagnostics()
    return ModelInfoResponse(**diag)


@router.post("/agent/repair", response_model=AgentRepairResponse)
def agent_repair(payload: AgentRepairRequest) -> AgentRepairResponse:
    """Execute end-to-end agentic analysis and repair proposal."""
    client = NebiusClient() if payload.use_nebius else None
    result = run_agent_analysis_and_proposal(
        payload.source,
        payload.traceback,
        filename=payload.filename,
        project_root=payload.project_root,
        relative_path=payload.relative_path,
        client=client,
    )

    repair_resp = None
    if result.get("repair"):
        r = result["repair"]
        repair_resp = AgentRepairResultResponse(
            available=r.available,
            provider=r.provider,
            model=r.model,
            is_ai_generated=r.is_ai_generated,
            root_cause_title=r.root_cause_title,
            root_cause_explanation=r.root_cause_explanation,
            next_step=r.next_step,
            confidence=r.confidence,
            fix_description=r.fix_description,
            before_source=r.before_source,
            after_source=r.after_source,
            unified_diff=r.unified_diff,
            syntax_valid=r.syntax_valid,
            error_message=r.error_message,
        )

    preview_resp = None
    if result.get("patch_preview"):
        preview_resp = PatchPreviewResponse(**result["patch_preview"].__dict__)

    timeline_items = [
        AgentTimelineItem(
            state=item["state"],
            description=item["description"],
            metadata={
                k: v for k, v in item.items() if k not in {"state", "description"}
            },
        )
        for item in result.get("timeline", [])
    ]

    return AgentRepairResponse(
        state=result["state"],
        repair=repair_resp,
        patch_preview=preview_resp,
        timeline=timeline_items,
        error=result.get("error"),
    )


@router.post("/agent/apply", response_model=AgentApplyResponse)
def agent_apply(payload: AgentApplyRequest) -> AgentApplyResponse:
    """Apply an approved repair patch with optional Docker container verification."""
    res = execute_agent_apply(
        payload.token,
        confirm=payload.confirm,
        run_sandbox_evidence=payload.run_sandbox_evidence,
        stdin=payload.stdin,
        source_before=payload.source_before,
        source_after=payload.source_after,
    )

    patch_result_resp = None
    if res.get("patch_result"):
        patch_result_resp = PatchActionResponse(**res["patch_result"].__dict__)

    evidence_resp = None
    if res.get("evidence"):
        evidence_resp = _evidence_response(res["evidence"])

    timeline_items = [
        AgentTimelineItem(
            state=item["state"],
            description=item["description"],
            metadata={
                k: v for k, v in item.items() if k not in {"state", "description"}
            },
        )
        for item in res.get("timeline", [])
    ]

    return AgentApplyResponse(
        state=res["state"],
        patch_result=patch_result_resp,
        evidence=evidence_resp,
        timeline=timeline_items,
        error=res.get("error"),
    )


@router.post("/agent/rollback", response_model=PatchActionResponse)
def agent_rollback(payload: PatchActionRequest) -> PatchActionResponse:
    """Roll back an applied patch to its exact pre-patch contents."""
    res = execute_agent_rollback(payload.token, confirm=payload.confirm)
    if res.get("error"):
        raise HTTPException(status_code=422, detail=res["error"])
    return PatchActionResponse(**res["patch_result"].__dict__)



def _frame_response(frame: TracebackFrame) -> TracebackFrameResponse:
    return TracebackFrameResponse(
        filename=frame.filename,
        line_number=frame.line_number,
        function=frame.function,
        source_line=frame.source_line,
    )


def _source_response(analysis: SourceAnalysis) -> SourceAnalysisResponse:
    return SourceAnalysisResponse(
        valid_syntax=analysis.valid_syntax,
        line_count=analysis.line_count,
        target_line=analysis.target_line,
        context=[
            SourceLineResponse(
                line_number=line.line_number,
                text=line.text,
                is_target=line.is_target,
            )
            for line in analysis.context
        ],
        syntax_error=(
            _syntax_response(analysis.syntax_error)
            if analysis.syntax_error is not None
            else None
        ),
        warnings=list(analysis.warnings),
    )


def _syntax_response(diagnostic: SyntaxDiagnostic) -> SyntaxDiagnosticResponse:
    return SyntaxDiagnosticResponse(
        message=diagnostic.message,
        line_number=diagnostic.line_number,
        column=diagnostic.column,
        source_line=diagnostic.source_line,
    )


def _root_cause_response(insights: AnalysisInsights) -> RootCauseResponse:
    root_cause: RootCauseExplanation = insights.root_cause
    return RootCauseResponse(
        code=root_cause.code,
        title=root_cause.title,
        explanation=root_cause.explanation,
        next_step=root_cause.next_step,
        confidence=root_cause.confidence,
    )


def _suggestion_response(insights: AnalysisInsights) -> FixSuggestionResponse:
    return _suggestion_response_from_fix(insights.suggestion)


def _suggestion_response_from_fix(suggestion: FixSuggestion) -> FixSuggestionResponse:
    comparison: CodeComparison = suggestion.comparison
    return FixSuggestionResponse(
        available=suggestion.available,
        title=suggestion.title,
        description=suggestion.description,
        confidence=suggestion.confidence,
        comparison=CodeComparisonResponse(
            before=comparison.before,
            after=comparison.after,
            unified_diff=comparison.unified_diff,
            changed=comparison.changed,
            before_valid_syntax=comparison.before_valid_syntax,
            after_valid_syntax=comparison.after_valid_syntax,
        ),
        limitation=suggestion.limitation,
    )


def _evidence_response(result: EvidenceResult) -> EvidenceResponse:
    return EvidenceResponse(
        available=result.available,
        message=result.message,
        before=_sandbox_run_response(result.before),
        after=_sandbox_run_response(result.after),
        regression_detected=result.regression_detected,
        scorecard=EvidenceScorecardResponse(
            overall=result.scorecard.overall,
            syntax_valid=result.scorecard.syntax_valid,
            reproduction_passed=result.scorecard.reproduction_passed,
            no_regression=result.scorecard.no_regression,
            claim=result.scorecard.claim,
        ),
    )


def _sandbox_run_response(run: SandboxRun | None) -> SandboxRunResponse | None:
    if run is None:
        return None
    return SandboxRunResponse(
        status=run.status,
        exit_code=run.exit_code,
        stdout=run.stdout,
        stderr=run.stderr,
        duration_ms=run.duration_ms,
        timed_out=run.timed_out,
    )
