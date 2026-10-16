from sunny_devfix.analysis.guardian import diagnose_source


def test_guardian_finds_undefined_name_and_offers_a_minimal_fix() -> None:
    result = diagnose_source(
        "def greet(user_name):\n    return 'hello ' + username\n"
    )

    assert result.valid_syntax is True
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "undefined-name"
    assert diagnostic.line_number == 2
    assert diagnostic.severity == "error"
    assert diagnostic.fix is not None
    assert diagnostic.fix.available is True
    assert "user_name" in diagnostic.fix.comparison.after


def test_guardian_reports_literal_division_by_zero_without_inventing_a_fix() -> None:
    result = diagnose_source("answer = 10 / 0\n")

    assert result.valid_syntax is True
    assert result.diagnostics[0].code == "division-by-zero"
    assert result.diagnostics[0].severity == "warning"
    assert result.diagnostics[0].fix is None


def test_guardian_does_not_warn_for_builtins_or_imported_names() -> None:
    result = diagnose_source(
        "import math\n"
        "value = math.sqrt(4)\n"
        "print(value)\n"
    )

    assert result.diagnostics == ()


def test_guardian_returns_syntax_diagnostic_for_incomplete_source() -> None:
    result = diagnose_source("def greet(name)\n    return name\n")

    assert result.valid_syntax is False
    assert result.diagnostics[0].code == "syntax-error"
    assert result.diagnostics[0].line_number == 1
    assert result.diagnostics[0].fix is not None
    assert result.diagnostics[0].fix.available is True
