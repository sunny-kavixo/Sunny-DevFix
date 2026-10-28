"""Validated request and response models for the analysis endpoint."""

from pydantic import BaseModel, ConfigDict, Field

from sunny_devfix.analysis.traceback_parser import MAX_TRACEBACK_BYTES
from sunny_devfix.analysis.source_analysis import MAX_SOURCE_BYTES
from sunny_devfix.sandbox import (
    DEFAULT_TIMEOUT_SECONDS,
    MAX_EVIDENCE_STDIN_BYTES,
)
from sunny_devfix.patches import MAX_PATCH_BYTES


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


class GuardianRequest(BaseModel):
    """Bounded source submitted by the live code guardian."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(default="", max_length=MAX_SOURCE_BYTES)


class GuardianDiagnosticResponse(BaseModel):
    """A line-level diagnostic returned during typing."""

    code: str
    message: str
    explanation: str
    line_number: int
    column: int | None
    severity: str
    confidence: str
    fix: FixSuggestionResponse | None = None


class GuardianResponse(BaseModel):
    """Complete live guardian pass."""

    valid_syntax: bool
    line_count: int
    diagnostics: list[GuardianDiagnosticResponse]


class EvidenceRequest(BaseModel):
    """Explicitly confirmed before/after reproduction request."""

    model_config = ConfigDict(extra="forbid")

    source_before: str = Field(max_length=MAX_SOURCE_BYTES)
    source_after: str = Field(max_length=MAX_SOURCE_BYTES)
    stdin: str = Field(default="", max_length=MAX_EVIDENCE_STDIN_BYTES)
    timeout_seconds: float = Field(
        default=DEFAULT_TIMEOUT_SECONDS, ge=1.0, le=10.0
    )
    confirm: bool = Field(
        default=False,
        description="Must be true: execution is never implicit.",
    )


class SandboxRunResponse(BaseModel):
    """One observed isolated run."""

    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool


class EvidenceScorecardResponse(BaseModel):
    """Evidence-backed repair scorecard."""

    overall: str
    syntax_valid: bool
    reproduction_passed: bool
    no_regression: bool
    claim: str


class EvidenceResponse(BaseModel):
    """Before/after reproduction result."""

    available: bool
    message: str
    before: SandboxRunResponse | None
    after: SandboxRunResponse | None
    regression_detected: bool
    scorecard: EvidenceScorecardResponse


class PatchPreviewRequest(BaseModel):
    """Exact before/after content for a project-scoped patch preview."""

    model_config = ConfigDict(extra="forbid")
    project_root: str = Field(min_length=1, max_length=1024)
    relative_path: str = Field(min_length=1, max_length=1024)
    before: str = Field(max_length=MAX_PATCH_BYTES)
    after: str = Field(max_length=MAX_PATCH_BYTES)


class PatchPreviewResponse(BaseModel):
    """Short-lived approval bound to exact file content."""

    approval_id: str
    relative_path: str
    before_sha256: str
    after_sha256: str
    expires_in_seconds: int


class PatchActionRequest(BaseModel):
    """Explicit confirmation for a prepared patch or rollback."""

    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=16, max_length=256)
    confirm: bool = False


class PatchActionResponse(BaseModel):
    """Observed file mutation result."""

    status: str
    relative_path: str
    rollback_id: str | None = None


class ModelInfoResponse(BaseModel):
    """Diagnostics and metadata for Nebius Token Factory and NVIDIA models."""

    provider: str
    model: str
    base_url: str
    enabled: bool
    configured: bool
    key_present: bool
    key_masked: str
    timeout_seconds: float
    max_retries: int


class AgentTimelineItem(BaseModel):
    """One event in the agent repair lifecycle."""

    state: str
    description: str
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class AgentRepairRequest(BaseModel):
    """Request to run full agentic analysis and patch proposal."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(default="", max_length=MAX_SOURCE_BYTES)
    traceback: str = Field(
        min_length=1,
        max_length=MAX_TRACEBACK_BYTES,
        description="The Python traceback or error to debug.",
    )
    filename: str = Field(default="<submitted>", min_length=1, max_length=512)
    project_root: str | None = Field(default=None, max_length=1024)
    relative_path: str | None = Field(default=None, max_length=1024)
    use_nebius: bool = Field(default=True)


class AgentRepairResultResponse(BaseModel):
    """Detailed repair diagnosis and unified patch."""

    available: bool
    provider: str
    model: str
    is_ai_generated: bool
    root_cause_title: str
    root_cause_explanation: str
    next_step: str
    confidence: str
    fix_description: str
    before_source: str
    after_source: str
    unified_diff: str
    syntax_valid: bool
    error_message: str | None = None


class AgentRepairResponse(BaseModel):
    """Complete response from the agentic repair orchestrator."""

    state: str
    repair: AgentRepairResultResponse | None
    patch_preview: PatchPreviewResponse | None
    timeline: list[AgentTimelineItem]
    error: str | None = None


class AgentApplyRequest(BaseModel):
    """Request to confirm and apply an agent-generated patch."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=16, max_length=256)
    confirm: bool = False
    run_sandbox_evidence: bool = False
    stdin: str = Field(default="", max_length=MAX_EVIDENCE_STDIN_BYTES)
    source_before: str = Field(default="", max_length=MAX_SOURCE_BYTES)
    source_after: str = Field(default="", max_length=MAX_SOURCE_BYTES)


class AgentApplyResponse(BaseModel):
    """Result of human-approved patch execution."""

    state: str
    patch_result: PatchActionResponse | None
    evidence: EvidenceResponse | None
    timeline: list[AgentTimelineItem]
    error: str | None = None

