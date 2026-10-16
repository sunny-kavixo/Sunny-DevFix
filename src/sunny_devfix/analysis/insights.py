"""Conservative explanations and source-only fix suggestions."""

from __future__ import annotations

import ast
import re
from difflib import SequenceMatcher

from sunny_devfix.analysis.diff import build_unified_diff
from sunny_devfix.analysis.models import (
    AnalysisInsights,
    CodeComparison,
    FixSuggestion,
    RootCauseExplanation,
    SourceAnalysis,
    TracebackInfo,
)
from sunny_devfix.analysis.source_analysis import analyze_source

_NAME_ERROR_RE = re.compile(
    r"name\s+['\"](?P<name>[A-Za-z_]\w*)['\"]\s+is not defined"
)
_HEADER_RE = re.compile(
    r"^\s*(?:def|class|if|elif|else|for|while|try|except|finally|with|match|case)\b"
)

_ROOT_CAUSES: dict[str, tuple[str, str, str, str]] = {
    "NameError": (
        "A name is missing in this scope",
        "Python reached a variable, function, or class name that is not defined where this line runs.",
        "Check the spelling first, then confirm the name is defined before this line executes.",
        "high",
    ),
    "TypeError": (
        "A value has the wrong type for this operation",
        "An operator or function received a kind of value it does not know how to use.",
        "Inspect the values on the highlighted line and compare their actual types with the operation.",
        "high",
    ),
    "ValueError": (
        "A value has the right shape but an unusable value",
        "Python accepted the value's general type, but its contents are outside what the operation allows.",
        "Inspect the input at the highlighted line and check its format or allowed range.",
        "high",
    ),
    "IndexError": (
        "A sequence position is outside its range",
        "The code asked a list, tuple, or string for a position that is not available.",
        "Check the sequence length and whether the index can reach its last valid position.",
        "high",
    ),
    "KeyError": (
        "A dictionary key is missing",
        "The lookup requested a key that is not present in the dictionary at that moment.",
        "Confirm the key exists, or choose an intentional fallback such as dict.get().",
        "high",
    ),
    "AttributeError": (
        "An object does not have that attribute",
        "The value before the dot is not the object the code expected, or the attribute name is misspelled.",
        "Inspect the value before the dot and check for None or a spelling mismatch.",
        "high",
    ),
    "SyntaxError": (
        "Python cannot build the program structure",
        "Python could not parse the source because punctuation, indentation, or a block delimiter is incomplete.",
        "Start at the highlighted line and check punctuation, indentation, and matching delimiters.",
        "high",
    ),
    "IndentationError": (
        "A block is indented inconsistently",
        "Python found a line whose indentation does not match the block structure around it.",
        "Use consistent spaces and align the line with the block it belongs to.",
        "high",
    ),
    "ZeroDivisionError": (
        "The denominator is zero",
        "The code tried to divide or take a remainder using zero as the denominator.",
        "Trace where the denominator comes from and handle the zero case deliberately.",
        "high",
    ),
    "FileNotFoundError": (
        "The requested file was not found",
        "Python could not find the path it was asked to open in the current environment.",
        "Check the path, working directory, filename, and whether the file exists before opening it.",
        "high",
    ),
    "ModuleNotFoundError": (
        "A module is unavailable in this environment",
        "Python could not find the module named in the import statement.",
        "Check the module name and environment separately; Sunny DevFix will not install packages automatically.",
        "high",
    ),
    "ImportError": (
        "An import could not be completed",
        "Python found the import path but could not load the requested name or dependency.",
        "Check the exported name, package version, and import path before changing code.",
        "medium",
    ),
}


def build_insights(
    source: str,
    traceback_info: TracebackInfo,
    source_analysis: SourceAnalysis,
) -> AnalysisInsights:
    """Build an explanation and conservative fix proposal from parsed data."""

    root_cause = _root_cause_for(traceback_info.exception_type)
    suggestion = _suggest_fix(source, traceback_info, source_analysis)
    return AnalysisInsights(root_cause=root_cause, suggestion=suggestion)


def _root_cause_for(exception_type: str) -> RootCauseExplanation:
    short_name = exception_type.rsplit(".", 1)[-1]
    title, explanation, next_step, confidence = _ROOT_CAUSES.get(
        short_name,
        (
            "Python stopped at this exception",
            "The traceback identifies where Python stopped, but this error family needs more program context for a reliable automatic explanation.",
            "Start with the deepest frame and inspect the values flowing into that line.",
            "low",
        ),
    )
    return RootCauseExplanation(
        code=short_name,
        title=title,
        explanation=explanation,
        next_step=next_step,
        confidence=confidence,
    )


def _suggest_fix(
    source: str,
    traceback_info: TracebackInfo,
    source_analysis: SourceAnalysis,
) -> FixSuggestion:
    short_name = traceback_info.exception_type.rsplit(".", 1)[-1]
    if short_name == "NameError":
        return _suggest_name_error(source, traceback_info, source_analysis)
    if short_name in {"SyntaxError", "IndentationError"}:
        return _suggest_syntax_fix(source, traceback_info, source_analysis)
    return _unavailable(
        source,
        source_analysis,
        "This error often has several valid fixes, so no automatic patch is proposed.",
    )


def _suggest_name_error(
    source: str,
    traceback_info: TracebackInfo,
    source_analysis: SourceAnalysis,
) -> FixSuggestion:
    match = _NAME_ERROR_RE.search(traceback_info.message)
    if match is None:
        return _unavailable(
            source,
            source_analysis,
            "The missing name could not be read reliably from the traceback message.",
        )
    if source_analysis.target_line is None:
        return _unavailable(
            source,
            source_analysis,
            "The traceback does not map to a line in the supplied source.",
        )

    try:
        tree = ast.parse(source, filename="<submitted>")
    except (SyntaxError, ValueError, TypeError):
        return _unavailable(
            source,
            source_analysis,
            "The source is not syntactically valid, so a name replacement would be unsafe.",
        )

    missing_name = match.group("name")
    candidates = _defined_names(tree)
    candidate = _best_name_candidate(missing_name, candidates)
    if candidate is None:
        return _unavailable(
            source,
            source_analysis,
            "No single in-scope name is a confident spelling match for the missing name.",
        )

    lines = source.splitlines(keepends=True)
    target_index = source_analysis.target_line - 1
    if target_index >= len(lines):
        return _unavailable(
            source,
            source_analysis,
            "The reported line is outside the supplied source.",
        )
    replacement = re.sub(
        rf"\b{re.escape(missing_name)}\b",
        candidate,
        lines[target_index],
        count=1,
    )
    if replacement == lines[target_index]:
        return _unavailable(
            source,
            source_analysis,
            "The missing name is not present on the reported source line.",
        )

    after = "".join(lines[:target_index] + [replacement] + lines[target_index + 1 :])
    after_analysis = analyze_source(after)
    if not after_analysis.valid_syntax:
        return _unavailable(
            source,
            source_analysis,
            "The proposed spelling change did not preserve valid Python syntax.",
        )
    comparison = _comparison(source, after, source_analysis.valid_syntax, after_analysis.valid_syntax)
    return FixSuggestion(
        available=True,
        title=f"Use the in-scope name '{candidate}'",
        description=(
            f"The traceback names '{missing_name}', but '{candidate}' is the only "
            "nearby defined name with a confident spelling match."
        ),
        confidence="high",
        comparison=comparison,
    )


def _suggest_syntax_fix(
    source: str,
    traceback_info: TracebackInfo,
    source_analysis: SourceAnalysis,
) -> FixSuggestion:
    diagnostic = source_analysis.syntax_error
    target_line = source_analysis.target_line
    if diagnostic is None or target_line is None:
        return _unavailable(
            source,
            source_analysis,
            "The syntax error does not map to a supplied source line.",
        )
    if "expected ':'" not in diagnostic.message:
        return _unavailable(
            source,
            source_analysis,
            "This syntax error has multiple possible repairs, so no automatic patch is proposed.",
        )

    lines = source.splitlines(keepends=True)
    target_index = target_line - 1
    line = lines[target_index] if target_index < len(lines) else ""
    stripped = line.strip()
    if not _HEADER_RE.match(line) or not stripped or stripped.endswith(":"):
        return _unavailable(
            source,
            source_analysis,
            "The reported line is not an unambiguous Python block header.",
        )

    newline = "\n" if line.endswith("\n") else ""
    content = line[:-1] if newline else line
    after = "".join(lines[:target_index] + [f"{content}:{newline}"] + lines[target_index + 1 :])
    after_analysis = analyze_source(after)
    if not after_analysis.valid_syntax:
        return _unavailable(
            source,
            source_analysis,
            "Adding a colon did not produce valid Python syntax, so the patch was withheld.",
        )
    comparison = _comparison(source, after, source_analysis.valid_syntax, after_analysis.valid_syntax)
    return FixSuggestion(
        available=True,
        title="Add the missing block colon",
        description="Python reported an expected ':' and the highlighted line is an unambiguous block header.",
        confidence="high",
        comparison=comparison,
    )


def _defined_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".", 1)[0])
    return names


def _best_name_candidate(missing_name: str, candidates: set[str]) -> str | None:
    scores = sorted(
        (
            _name_similarity(missing_name, candidate),
            candidate,
        )
        for candidate in candidates
        if candidate != missing_name
    )
    scores.reverse()
    if not scores or scores[0][0] < 0.72:
        return None
    if len(scores) > 1 and scores[0][0] - scores[1][0] < 0.08:
        return None
    return scores[0][1]


def _name_similarity(left: str, right: str) -> float:
    direct = SequenceMatcher(None, left, right).ratio()
    collapsed = SequenceMatcher(None, left.replace("_", ""), right.replace("_", "")).ratio()
    return max(direct, collapsed)


def _comparison(
    before: str,
    after: str,
    before_valid_syntax: bool,
    after_valid_syntax: bool,
) -> CodeComparison:
    return CodeComparison(
        before=before,
        after=after,
        unified_diff=build_unified_diff(before, after),
        changed=before != after,
        before_valid_syntax=before_valid_syntax,
        after_valid_syntax=after_valid_syntax,
    )


def _unavailable(
    source: str,
    source_analysis: SourceAnalysis,
    limitation: str,
) -> FixSuggestion:
    comparison = _comparison(
        source,
        source,
        source_analysis.valid_syntax,
        source_analysis.valid_syntax,
    )
    return FixSuggestion(
        available=False,
        title="No automatic fix proposed",
        description=limitation,
        confidence="none",
        comparison=comparison,
        limitation=limitation,
    )
