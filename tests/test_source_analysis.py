import pytest

from sunny_devfix.analysis.models import InputLimitError
from sunny_devfix.analysis.source_analysis import analyze_source
from sunny_devfix.analysis.traceback_parser import parse_traceback


def test_analyze_source_maps_deepest_traceback_frame_and_context() -> None:
    source = "def greet(name):\n    return 'hello ' + username\n"
    traceback_info = parse_traceback(
        'Traceback (most recent call last):\n'
        '  File "app.py", line 2, in greet\n'
        "    return 'hello ' + username\n"
        "NameError: name 'username' is not defined\n"
    )

    result = analyze_source(source, traceback_info, context_radius=1)

    assert result.valid_syntax is True
    assert result.line_count == 2
    assert result.target_line == 2
    assert [(line.line_number, line.is_target) for line in result.context] == [
        (1, False),
        (2, True),
    ]
    assert result.syntax_error is None
    assert result.warnings == ()


def test_analyze_source_reports_syntax_error_location_without_traceback() -> None:
    result = analyze_source("def greet(name)\n    return name\n")

    assert result.valid_syntax is False
    assert result.syntax_error is not None
    assert result.syntax_error.line_number == 1
    assert result.target_line == 1
    assert result.context[0].is_target is True


def test_analyze_source_handles_a_traceback_line_outside_supplied_source() -> None:
    traceback_info = parse_traceback(
        'Traceback (most recent call last):\n'
        '  File "app.py", line 12, in run\n'
        '    return missing\n'
        "NameError: name 'missing' is not defined\n"
    )

    result = analyze_source("def broken(\n", traceback_info)

    assert result.valid_syntax is False
    assert result.target_line is None
    assert result.context == ()
    assert result.warnings == (
        "Traceback line 12 is outside the supplied source (1 lines).",
    )


def test_analyze_source_handles_empty_source_without_inventing_a_location() -> None:
    result = analyze_source("")

    assert result.valid_syntax is True
    assert result.line_count == 0
    assert result.target_line is None
    assert result.context == ()
    assert result.warnings == ()


def test_analyze_source_rejects_oversized_input() -> None:
    with pytest.raises(InputLimitError, match="10-byte"):
        analyze_source("x = 123456\n", max_bytes=10)
