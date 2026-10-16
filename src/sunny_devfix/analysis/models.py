"""Value objects shared by the deterministic analysis modules."""

from dataclasses import dataclass


class AnalysisInputError(ValueError):
    """Base error for invalid or oversized analysis input."""


class InputLimitError(AnalysisInputError):
    """Raised when bounded analysis input exceeds its configured limit."""


class TracebackParseError(AnalysisInputError):
    """Raised when a traceback has no recognizable exception line."""


@dataclass(frozen=True)
class TracebackFrame:
    """One Python traceback frame."""

    filename: str
    line_number: int
    function: str
    source_line: str | None = None


@dataclass(frozen=True)
class TracebackInfo:
    """Normalized information extracted from a traceback."""

    exception_type: str
    message: str
    frames: tuple[TracebackFrame, ...]
    raw: str

    @property
    def deepest_frame(self) -> TracebackFrame | None:
        """Return the last frame, which is usually the failing user frame."""

        return self.frames[-1] if self.frames else None


@dataclass(frozen=True)
class SyntaxDiagnostic:
    """A syntax or parsing diagnostic for submitted source."""

    message: str
    line_number: int | None = None
    column: int | None = None
    source_line: str | None = None


@dataclass(frozen=True)
class SourceLine:
    """A source line included in the focused context window."""

    line_number: int
    text: str
    is_target: bool = False


@dataclass(frozen=True)
class SourceAnalysis:
    """Result of syntax validation and traceback-to-source mapping."""

    valid_syntax: bool
    line_count: int
    target_line: int | None
    context: tuple[SourceLine, ...]
    syntax_error: SyntaxDiagnostic | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class RootCauseExplanation:
    """Beginner-friendly explanation for a recognized exception family."""

    code: str
    title: str
    explanation: str
    next_step: str
    confidence: str


@dataclass(frozen=True)
class CodeComparison:
    """Non-executing before/after source comparison."""

    before: str
    after: str
    unified_diff: str
    changed: bool
    before_valid_syntax: bool
    after_valid_syntax: bool


@dataclass(frozen=True)
class FixSuggestion:
    """A conservative proposed fix or an explicit limitation."""

    available: bool
    title: str
    description: str
    confidence: str
    comparison: CodeComparison
    limitation: str | None = None


@dataclass(frozen=True)
class AnalysisInsights:
    """Root-cause explanation and fix suggestion for one analysis."""

    root_cause: RootCauseExplanation
    suggestion: FixSuggestion
