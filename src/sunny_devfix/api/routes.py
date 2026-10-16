"""FastAPI routes for local-first traceback analysis."""

from fastapi import APIRouter, HTTPException

from sunny_devfix.analysis.models import (
    AnalysisInputError,
    SourceAnalysis,
    SyntaxDiagnostic,
    TracebackFrame,
    TracebackParseError,
)
from sunny_devfix.analysis.source_analysis import analyze_source
from sunny_devfix.analysis.traceback_parser import parse_traceback
from sunny_devfix.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    SafetyResponse,
    SourceAnalysisResponse,
    SourceLineResponse,
    SyntaxDiagnosticResponse,
    TracebackFrameResponse,
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
        safety=SafetyResponse(
            executed=False,
            message=(
                "Analysis only: the submitted source was parsed, never imported "
                "or executed."
            ),
        ),
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
