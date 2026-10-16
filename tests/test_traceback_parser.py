import pytest

from sunny_devfix.analysis.models import InputLimitError, TracebackParseError
from sunny_devfix.analysis.traceback_parser import parse_traceback


NAME_ERROR_TRACEBACK = '''Traceback (most recent call last):
  File "/workspace/app.py", line 6, in <module>
    greet(user_name)
  File "/workspace/app.py", line 2, in greet
    return "Hello, " + username
NameError: name 'username' is not defined
'''


def test_parse_traceback_extracts_exception_and_deepest_frame() -> None:
    result = parse_traceback(NAME_ERROR_TRACEBACK)

    assert result.exception_type == "NameError"
    assert result.message == "name 'username' is not defined"
    assert len(result.frames) == 2
    assert result.deepest_frame is not None
    assert result.deepest_frame.filename == "/workspace/app.py"
    assert result.deepest_frame.line_number == 2
    assert result.deepest_frame.function == "greet"
    assert result.deepest_frame.source_line == 'return "Hello, " + username'


def test_parse_traceback_normalizes_windows_newlines_and_supports_syntax_errors() -> None:
    result = parse_traceback(
        '  File "C:\\work\\main.py", line 1\r\n'
        '    if True print("broken")\r\n'
        'SyntaxError: invalid syntax\r\n'
    )

    assert result.raw.endswith("SyntaxError: invalid syntax\n")
    assert result.exception_type == "SyntaxError"
    assert result.deepest_frame is not None
    assert result.deepest_frame.filename == "C:\\work\\main.py"
    assert result.deepest_frame.line_number == 1


def test_parse_traceback_accepts_qualified_custom_exception_names() -> None:
    result = parse_traceback(
        'Traceback (most recent call last):\n'
        '  File "service.py", line 3, in run\n'
        '    raise errors.BadState("offline")\n'
        'errors.BadState: offline\n'
    )

    assert result.exception_type == "errors.BadState"
    assert result.message == "offline"


def test_parse_traceback_rejects_empty_or_unrecognized_text() -> None:
    with pytest.raises(TracebackParseError, match="empty"):
        parse_traceback("\n")

    with pytest.raises(TracebackParseError, match="No recognizable"):
        parse_traceback("this is only a log message")


def test_parse_traceback_rejects_oversized_input() -> None:
    with pytest.raises(InputLimitError, match="20-byte"):
        parse_traceback("RuntimeError: too large", max_bytes=20)
