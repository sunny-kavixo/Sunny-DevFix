"""Nebius Token Factory client for NVIDIA open-weights model inference."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

import httpx

logger = logging.getLogger("sunny_devfix.providers.nebius")

DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1"
DEFAULT_MODEL = "nvidia/Nemotron-3_5-Lightning"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_RETRIES = 2
MAX_PAYLOAD_CHARS = 30_000

SUPPORTED_NVIDIA_MODELS: tuple[str, ...] = (
    "nvidia/Nemotron-3_5-Lightning",
)



class NebiusError(Exception):
    """Base exception for Nebius Token Factory operations."""


class NebiusConfigError(NebiusError):
    """Raised when the client is invoked without valid configuration."""


class NebiusAuthError(NebiusError):
    """Raised on authentication failure (e.g. invalid or revoked API key)."""


class NebiusRateLimitError(NebiusError):
    """Raised when rate limits or quotas are exceeded."""


class NebiusTimeoutError(NebiusError):
    """Raised when the request exceeds the configured timeout."""


class NebiusResponseError(NebiusError):
    """Raised when the model response is malformed or unparseable."""


def redact_key(key: str | None) -> str:
    """Report key presence without exposing a reusable key fingerprint."""
    if not key:
        return "[NOT_SET]"
    return "[REDACTED]"


_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"v1\.[A-Za-z0-9._\-]{8,}", re.IGNORECASE),
    re.compile(r"neb-[A-Za-z0-9._\-]{8,}", re.IGNORECASE),
    re.compile(r"[A-Za-z0-9_\-]{32,}"),
)


def sanitize_error_detail(detail: str | None, max_length: int = 160) -> str:
    """Sanitize error messages from upstream providers to prevent secret leakage and noisy logs."""
    if not detail:
        return ""
    clean = str(detail).strip()
    for pattern in _SECRET_PATTERNS:
        clean = pattern.sub("[REDACTED_SECRET]", clean)
    clean = re.sub(r"\s+", " ", clean)
    if len(clean) > max_length:
        clean = clean[:max_length].rstrip() + "..."
    return clean


class NebiusClient:
    """Client for Nebius Token Factory hosting NVIDIA models."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        enabled: bool | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("NEBIUS_API_KEY", "").strip()
        self.base_url = (
            base_url
            if base_url is not None
            else os.getenv("DEVFIX_NEBIUS_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        )
        self.model = (
            model
            if model is not None
            else os.getenv("DEVFIX_NEBIUS_MODEL", DEFAULT_MODEL).strip()
        )
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else float(os.getenv("DEVFIX_NEBIUS_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
        )
        self.max_retries = (
            max_retries
            if max_retries is not None
            else int(os.getenv("DEVFIX_NEBIUS_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
        )

        if enabled is not None:
            self._enabled = enabled
        else:
            env_enabled = os.getenv("DEVFIX_NEBIUS_ENABLED", "").lower()
            if env_enabled in {"true", "1", "yes"}:
                self._enabled = True
            elif env_enabled in {"false", "0", "no"}:
                self._enabled = False
            else:
                self._enabled = bool(self.api_key)

        self._transport = transport

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def is_configured(self) -> bool:
        return bool(self._enabled and self.api_key)

    def get_diagnostics(self) -> dict[str, Any]:
        """Return non-sensitive runtime diagnostics for status checks."""
        return {
            "provider": "Nebius Token Factory",
            "model": self.model,
            "base_url": self.base_url,
            "enabled": self._enabled,
            "configured": bool(self.api_key),
            "key_present": bool(self.api_key),
            "key_masked": redact_key(self.api_key),
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "supported_models": list(SUPPORTED_NVIDIA_MODELS),
        }

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a guarded chat completion request against Nebius Token Factory."""
        if not self.is_configured:
            raise NebiusConfigError(
                "Nebius client is not configured. Provide NEBIUS_API_KEY and set DEVFIX_NEBIUS_ENABLED=true."
            )

        # Enforce character bound on payload to prevent memory or token abuse
        total_chars = sum(len(m.get("content", "")) for m in messages)
        if total_chars > MAX_PAYLOAD_CHARS:
            raise NebiusError(f"Payload character count ({total_chars}) exceeds limit ({MAX_PAYLOAD_CHARS}).")

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Sunny-DevFix-Agent/0.2.1 (Nebius-NVIDIA-Hackathon)",
        }

        request_body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format is not None:
            request_body["response_format"] = response_format

        attempts = 0
        last_error: Exception | None = None

        while attempts <= self.max_retries:
            attempts += 1
            try:
                with httpx.Client(
                    timeout=self.timeout_seconds,
                    transport=self._transport,
                ) as client:
                    response = client.post(endpoint, json=request_body, headers=headers)

                if response.status_code == 200:
                    try:
                        return response.json()
                    except Exception as parse_exc:
                        raise NebiusResponseError(f"Failed to decode response JSON: {parse_exc}") from parse_exc

                clean_detail = sanitize_error_detail(response.text)
                if response.status_code in {401, 403}:
                    raise NebiusAuthError(
                        f"Nebius Token Factory authentication failed (HTTP {response.status_code}): {clean_detail}"
                    )

                if response.status_code == 429:
                    if attempts <= self.max_retries:
                        sleep_time = 0.5 * (2 ** (attempts - 1))
                        time.sleep(sleep_time)
                        continue
                    raise NebiusRateLimitError(
                        f"Nebius Token Factory rate limit exceeded (HTTP 429): {clean_detail}"
                    )

                if 500 <= response.status_code < 600:
                    if attempts <= self.max_retries:
                        sleep_time = 0.5 * (2 ** (attempts - 1))
                        time.sleep(sleep_time)
                        continue
                    raise NebiusResponseError(
                        f"Nebius server error (HTTP {response.status_code}): {clean_detail}"
                    )

                raise NebiusResponseError(
                    f"Unexpected Nebius HTTP status {response.status_code}: {clean_detail}"
                )

            except httpx.TimeoutException as exc:
                last_error = exc
                if attempts <= self.max_retries:
                    time.sleep(0.5 * (2 ** (attempts - 1)))
                    continue
                clean_exc = sanitize_error_detail(str(exc))
                raise NebiusTimeoutError(
                    f"Nebius Token Factory request timed out after {self.timeout_seconds}s: {clean_exc}"
                ) from exc
            except (httpx.ConnectError, httpx.NetworkError) as exc:
                last_error = exc
                if attempts <= self.max_retries:
                    time.sleep(0.5 * (2 ** (attempts - 1)))
                    continue
                clean_exc = sanitize_error_detail(str(exc))
                raise NebiusResponseError(f"Network error contacting Nebius: {clean_exc}") from exc

        if last_error:
            raise NebiusResponseError(f"Nebius request failed after {attempts} attempts: {last_error}") from last_error
        raise NebiusResponseError("Nebius request failed with unknown error.")
