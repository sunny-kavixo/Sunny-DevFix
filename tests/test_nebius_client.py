"""Unit tests for the Nebius Token Factory client."""

import httpx
import pytest

from sunny_devfix.providers.nebius import (
    NebiusAuthError,
    NebiusClient,
    NebiusConfigError,
    NebiusError,
    NebiusRateLimitError,
    NebiusResponseError,
    NebiusTimeoutError,
    redact_key,
)


def test_redact_key():
    assert redact_key(None) == "[NOT_SET]"
    assert redact_key("") == "[NOT_SET]"
    assert redact_key("short") == "[REDACTED]"
    assert redact_key("abcdefghijklmnop") == "[REDACTED]"


def test_client_configuration_defaults():
    client = NebiusClient(api_key="", enabled=False)
    assert not client.is_configured
    assert not client.is_enabled

    diag = client.get_diagnostics()
    assert diag["provider"] == "Nebius Token Factory"
    assert diag["model"] == "nvidia/Nemotron-3_5-Lightning"
    assert not diag["configured"]
    assert diag["key_masked"] == "[NOT_SET]"


def test_client_configured_with_key():
    client = NebiusClient(api_key="neb-1234567890abcdef", enabled=True)
    assert client.is_configured
    assert client.is_enabled

    diag = client.get_diagnostics()
    assert diag["configured"] is True
    assert diag["key_masked"] == "[REDACTED]"


def test_chat_completion_unconfigured_raises():
    client = NebiusClient(api_key="", enabled=False)
    with pytest.raises(NebiusConfigError, match="Nebius client is not configured"):
        client.chat_completion([{"role": "user", "content": "hello"}])


def test_chat_completion_payload_limit_enforced():
    client = NebiusClient(api_key="neb-valid-key-1234", enabled=True)
    giant_message = "x" * 35_000
    with pytest.raises(NebiusError, match="Payload character count .* exceeds limit"):
        client.chat_completion([{"role": "user", "content": giant_message}])


def test_chat_completion_success_mocked():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer neb-valid-key-1234"
        assert request.url == "https://api.tokenfactory.nebius.com/v1/chat/completions"
        content = {
            "id": "chatcmpl-test",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": '{"root_cause_title": "Test Defect", "root_cause_explanation": "Explanation here", "recommended_next_step": "Fix step", "confidence": "high", "fix_description": "Fixed bug", "repaired_source": "print(1)"}',
                    }
                }
            ],
        }
        return httpx.Response(200, json=content)

    transport = httpx.MockTransport(mock_handler)
    client = NebiusClient(api_key="neb-valid-key-1234", enabled=True, transport=transport)
    response = client.chat_completion([{"role": "user", "content": "analyze"}])
    assert response["id"] == "chatcmpl-test"
    assert len(response["choices"]) == 1


def test_chat_completion_auth_error_mocked():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized: Invalid API key")

    transport = httpx.MockTransport(mock_handler)
    client = NebiusClient(api_key="neb-invalid", enabled=True, transport=transport, max_retries=0)
    with pytest.raises(NebiusAuthError, match="authentication failed"):
        client.chat_completion([{"role": "user", "content": "analyze"}])


def test_chat_completion_rate_limit_mocked():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="Rate limit exceeded")

    transport = httpx.MockTransport(mock_handler)
    client = NebiusClient(api_key="neb-key", enabled=True, transport=transport, max_retries=1)
    with pytest.raises(NebiusRateLimitError, match="rate limit exceeded"):
        client.chat_completion([{"role": "user", "content": "analyze"}])


def test_chat_completion_timeout_mocked():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Request timed out")

    transport = httpx.MockTransport(mock_handler)
    client = NebiusClient(api_key="neb-key", enabled=True, transport=transport, max_retries=0, timeout_seconds=1.0)
    with pytest.raises(NebiusTimeoutError, match="timed out"):
        client.chat_completion([{"role": "user", "content": "analyze"}])
