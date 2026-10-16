from sunny_devfix.analysis.diff import build_unified_diff


def test_build_unified_diff_is_copyable_and_names_both_versions() -> None:
    diff = build_unified_diff("answer = 41\n", "answer = 42\n")

    assert diff.startswith("--- before.py\n+++ after.py\n")
    assert "-answer = 41\n" in diff
    assert "+answer = 42\n" in diff


def test_build_unified_diff_returns_empty_for_identical_source() -> None:
    assert build_unified_diff("print('same')\n", "print('same')\n") == ""


def test_build_unified_diff_handles_source_without_a_final_newline() -> None:
    diff = build_unified_diff("value = 1", "value = 2")

    assert "-value = 1" in diff
    assert "+value = 2" in diff
