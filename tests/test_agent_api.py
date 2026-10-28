"""Integration tests for agent API endpoints."""

import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from sunny_devfix.app import app

client = TestClient(app)


def test_model_info_endpoint():
    response = client.get("/api/model-info")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "Nebius Token Factory"
    assert "nvidia" in data["model"].lower() or "nemotron" in data["model"].lower()
    assert "configured" in data
    assert "key_masked" in data


def test_agent_repair_endpoint_fallback():
    payload = {
        "source": "def calculate(val):\n    return val + missing_name\n",
        "traceback": """Traceback (most recent call last):
  File "calc.py", line 2, in calculate
    return val + missing_name
NameError: name 'missing_name' is not defined""",
        "filename": "calc.py",
        "use_nebius": False,
    }
    response = client.post("/api/agent/repair", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["state"] in {"AWAITING_APPROVAL", "FAILED"}
    assert "timeline" in data
    assert len(data["timeline"]) > 0


def test_agent_apply_without_confirm_returns_error():
    payload = {
        "token": "tok_some_preview_token_12345",
        "confirm": False,
    }
    response = client.post("/api/agent/apply", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "FAILED"
    assert "Explicit user confirmation is mandatory" in data["error"]


def test_agent_rollback_without_confirm_returns_422():
    payload = {
        "token": "tok_some_rollback_token_12345",
        "confirm": False,
    }
    response = client.post("/api/agent/rollback", json=payload)
    assert response.status_code == 422
    assert "Explicit user confirmation is mandatory" in response.json()["detail"]
