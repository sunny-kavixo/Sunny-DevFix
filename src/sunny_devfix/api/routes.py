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
    SandboxRunResponse,
    RootCauseResponse,
    SafetyResponse,
    SourceAnalysisResponse,
    SourceLineResponse,
    SyntaxDiagnosticResponse,
    TracebackFrameResponse,
)
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
