"""Validated request and response models for the analysis endpoint."""

from pydantic import BaseModel, ConfigDict, Field

from sunny_devfix.analysis.traceback_parser import MAX_TRACEBACK_BYTES
from sunny_devfix.analysis.source_analysis import MAX_SOURCE_BYTES


class AnalyzeRequest(BaseModel):
    """Input accepted by the deterministic analysis endpoint."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(default="", max_length=MAX_SOURCE_BYTES)
    traceback: str = Field(
        min_length=1,
        max_length=MAX_TRACEBACK_BYTES,
        description="The Python traceback to inspect.",
    )
    filename: str = Field(default="<submitted>", min_length=1, max_length=512)
    context_radius: int = Field(default=2, ge=0, le=8)


class TracebackFrameResponse(BaseModel):
    """A traceback frame safe to render in the browser."""

    filename: str
    line_number: int
    function: str
    source_line: str | None = None


class SyntaxDiagnosticResponse(BaseModel):
    """A syntax diagnostic safe to render in the browser."""

    message: str
    line_number: int | None = None
    column: int | None = None
    source_line: str | None = None


class SourceLineResponse(BaseModel):
    """One source line in the focused context window."""

    line_number: int
    text: str
    is_target: bool


class SourceAnalysisResponse(BaseModel):
    """Source validation and location mapping returned by the API."""

    valid_syntax: bool
    line_count: int
    target_line: int | None
    context: list[SourceLineResponse]
    syntax_error: SyntaxDiagnosticResponse | None = None
    warnings: list[str]


class SafetyResponse(BaseModel):
    """Explicit statement of what the analysis request did not execute."""

    executed: bool
    message: str


class RootCauseResponse(BaseModel):
    """Beginner-friendly explanation of the recognized error family."""

    code: str
    title: str
    explanation: str
    next_step: str
    confidence: str


class CodeComparisonResponse(BaseModel):
    """Before/after source and its copyable unified diff."""

    before: str
    after: str
    unified_diff: str
    changed: bool
    before_valid_syntax: bool
    after_valid_syntax: bool


class FixSuggestionResponse(BaseModel):
    """A proposed patch or an explicit explanation of why one was withheld."""

    available: bool
    title: str
    description: str
    confidence: str
    comparison: CodeComparisonResponse
    limitation: str | None = None


class AnalyzeResponse(BaseModel):
    """Complete structured result for a traceback analysis request."""

    exception_type: str
    message: str
    frames: list[TracebackFrameResponse]
    deepest_frame: TracebackFrameResponse | None
    source_analysis: SourceAnalysisResponse
    root_cause: RootCauseResponse
    suggestion: FixSuggestionResponse
    safety: SafetyResponse
