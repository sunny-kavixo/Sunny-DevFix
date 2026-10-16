from sunny_devfix.analysis.insights import build_insights
from sunny_devfix.analysis.source_analysis import analyze_source
from sunny_devfix.analysis.traceback_parser import parse_traceback


def _analysis(source: str, traceback: str):
    parsed = parse_traceback(traceback)
    return build_insights(source, parsed, analyze_source(source, parsed))


def test_name_error_gets_a_conservative_spelling_fix() -> None:
    source = "def greet(user_name):\n    return 'hello ' + username\n"
    result = _analysis(
        source,
        'Traceback (most recent call last):\n'
        '  File "app.py", line 2, in greet\n'
        "    return 'hello ' + username\n"
        "NameError: name 'username' is not defined\n",
    )

    assert result.root_cause.code == "NameError"
    assert result.root_cause.confidence == "high"
    assert result.suggestion.available is True
    assert result.suggestion.confidence == "high"
    assert "user_name" in result.suggestion.comparison.after
    assert result.suggestion.comparison.before_valid_syntax is True
    assert result.suggestion.comparison.after_valid_syntax is True
    assert result.suggestion.comparison.unified_diff.startswith("--- before.py")


def test_missing_colon_gets_a_syntax_validating_fix() -> None:
    source = "def greet(name)\n    return name\n"
    result = _analysis(
        source,
        '  File "app.py", line 1\n'
        "    def greet(name)\n"
        "SyntaxError: expected ':'\n",
    )

    assert result.root_cause.code == "SyntaxError"
    assert result.suggestion.available is True
    assert result.suggestion.comparison.after.startswith("def greet(name):")
    assert result.suggestion.comparison.after_valid_syntax is True


def test_ambiguous_name_error_is_explained_without_a_patch() -> None:
    source = "def run(user_name, user_name_):\n    return username\n"
    result = _analysis(
        source,
        'Traceback (most recent call last):\n'
        '  File "app.py", line 2, in run\n'
        "    return username\n"
        "NameError: name 'username' is not defined\n",
    )

    assert result.suggestion.available is False
    assert result.suggestion.comparison.unified_diff == ""
    assert "single" in (result.suggestion.limitation or "")


def test_common_runtime_error_gets_explanation_but_no_invented_fix() -> None:
    result = _analysis(
        "total = 1 + '1'\n",
        'Traceback (most recent call last):\n'
        '  File "app.py", line 1, in <module>\n'
        "    total = 1 + '1'\n"
        "TypeError: unsupported operand type(s)\n",
    )

    assert result.root_cause.code == "TypeError"
    assert result.root_cause.title
    assert result.suggestion.available is False
    assert "several valid fixes" in result.suggestion.description


def test_unsupported_error_family_reports_low_confidence_limitation() -> None:
    result = _analysis(
        "raise CustomProblem('stop')\n",
        'Traceback (most recent call last):\n'
        '  File "app.py", line 1, in <module>\n'
        "    raise CustomProblem('stop')\n"
        "errors.CustomProblem: stop\n",
    )

    assert result.root_cause.confidence == "low"
    assert result.suggestion.available is False
