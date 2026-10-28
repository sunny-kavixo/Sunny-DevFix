"""Unit tests for the NVIDIA Nemotron repair provider."""

import httpx
import pytest

from sunny_devfix.providers.nebius import NebiusClient
from sunny_devfix.providers.nvidia_repair import (
    NvidiaRepairResult,
    extract_json_payload,
    run_nvidia_repair,
)


def test_extract_json_payload_clean():
    raw = '{"root_cause_title": "Title", "confidence": "high"}'
    parsed = extract_json_payload(raw)
    assert parsed["root_cause_title"] == "Title"


def test_extract_json_payload_with_markdown_fences():
    raw = """```json
{
  "root_cause_title": "Fenced Title",
  "confidence": "high"
}
```"""
    parsed = extract_json_payload(raw)
    assert parsed["root_cause_title"] == "Fenced Title"


def test_extract_json_payload_embedded_in_text():
    raw = """Here is the diagnosed fix:
{"root_cause_title": "Embedded Title", "confidence": "high"}
Hope this helps!"""
    parsed = extract_json_payload(raw)
    assert parsed["root_cause_title"] == "Embedded Title"


def test_nvidia_repair_fallback_when_unconfigured():
    client = NebiusClient(api_key="", enabled=False)
    source = "def add(a, b):\n    return a + c\n"
    traceback_text = """Traceback (most recent call last):
  File "calc.py", line 2, in add
    return a + c
NameError: name 'c' is not defined"""

    result: NvidiaRepairResult = run_nvidia_repair(
        source,
        traceback_text,
        filename="calc.py",
        client=client,
    )
    assert result.provider == "Local Deterministic Engine"
    assert not result.is_ai_generated
    assert "c" in result.root_cause_explanation or "Name" in result.root_cause_explanation


def test_nvidia_repair_mocked_success():
    mock_payload = {
        "root_cause_title": "Misspelled Variable Reference",
        "root_cause_explanation": "The variable 'c' was referenced instead of parameter 'b'.",
        "recommended_next_step": "Replace 'c' with 'b'.",
        "confidence": "high",
        "fix_description": "Use parameter 'b' in addition.",
        "repaired_source": "def add(a, b):\n    return a + b\n",
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": json_str}}
                ]
            },
        )

    import json
    json_str = json.dumps(mock_payload)

    transport = httpx.MockTransport(mock_handler)
    client = NebiusClient(api_key="neb-test-key", enabled=True, transport=transport)

    source = "def add(a, b):\n    return a + c\n"
    tb = """Traceback (most recent call last):
  File "calc.py", line 2, in add
    return a + c
NameError: name 'c' is not defined"""

    result = run_nvidia_repair(source, tb, filename="calc.py", client=client)
    assert result.available is True
    assert result.is_ai_generated is True
    assert result.provider == "Nebius Token Factory"
    assert result.root_cause_title == "Misspelled Variable Reference"
    assert "return a + b" in result.after_source
    assert result.syntax_valid is True
    assert "-    return a + c" in result.unified_diff
    assert "+    return a + b" in result.unified_diff


def test_nvidia_repair_invalid_syntax_falls_back():
    mock_payload = {
        "root_cause_title": "Broken Syntax Proposal",
        "root_cause_explanation": "This proposes broken syntax.",
        "recommended_next_step": "Do something",
        "confidence": "high",
        "fix_description": "Syntactically invalid fix",
        "repaired_source": "def broken(\n",  # SyntaxError: unexpected EOF
    }

    import json
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": json.dumps(mock_payload)}}]},
        )

    transport = httpx.MockTransport(mock_handler)
    client = NebiusClient(api_key="neb-test-key", enabled=True, transport=transport)

    source = "x = 1\n"
    tb = "NameError: name 'y' is not defined"

    result = run_nvidia_repair(source, tb, client=client, fallback_on_error=True)
    # Should fall back cleanly rather than crashing
    assert result.provider == "Local Deterministic Engine"
    assert result.is_ai_generated is False
