import asyncio

import httpx

from sunny_devfix.app import app


async def _request(
    method: str, path: str, **kwargs: object
) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.request(method, path, **kwargs)


def request(method: str, path: str, **kwargs: object) -> httpx.Response:
    return asyncio.run(_request(method, path, **kwargs))


def test_root_and_static_assets_are_served() -> None:
    page = request("GET", "/")
    stylesheet = request("GET", "/static/style.css")

    assert page.status_code == 200
    assert "Sunny DevFix" in page.text
    assert "suggestion-card" in page.text
    assert "copy-diff" in page.text
    assert "before-code" in page.text
    assert "guardian-panel" in page.text
    assert "verify-evidence" in page.text
    assert stylesheet.status_code == 200
    assert "--mint" in stylesheet.text


def test_analyze_endpoint_returns_structured_result_without_execution() -> None:
    response = request(
        "POST",
        "/api/analyze",
        json={
            "source": "def greet(user_name):\n    return 'hello ' + username\n",
            "traceback": (
                "Traceback (most recent call last):\n"
                '  File "app.py", line 2, in greet\n'
                "    return 'hello ' + username\n"
                "NameError: name 'username' is not defined\n"
            ),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["exception_type"] == "NameError"
    assert body["deepest_frame"]["line_number"] == 2
    assert body["source_analysis"]["target_line"] == 2
    assert body["source_analysis"]["context"][1]["is_target"] is True
    assert body["root_cause"]["code"] == "NameError"
    assert body["suggestion"]["available"] is True
    assert body["suggestion"]["comparison"]["after_valid_syntax"] is True
    assert body["suggestion"]["comparison"]["unified_diff"].startswith(
        "--- before.py"
    )
    assert body["safety"] == {
        "executed": False,
        "message": (
            "Analysis only: the submitted source was parsed, never imported "
            "or executed."
        ),
    }


def test_analyze_endpoint_rejects_traceback_without_exception() -> None:
    response = request(
        "POST",
        "/api/analyze",
        json={"source": "print('hello')", "traceback": "only a log line"},
    )

    assert response.status_code == 422
    assert "No recognizable Python exception" in response.json()["detail"]


def test_analyze_endpoint_rejects_unknown_request_fields() -> None:
    response = request(
        "POST",
        "/api/analyze",
        json={
            "source": "print('hello')",
            "traceback": "RuntimeError: stopped",
            "execute": True,
        },
    )

    assert response.status_code == 422


def test_analyze_endpoint_reports_limitation_for_ambiguous_runtime_fix() -> None:
    response = request(
        "POST",
        "/api/analyze",
        json={
            "source": "def run(user_name, user_name_):\n    return username\n",
            "traceback": (
                "Traceback (most recent call last):\n"
                '  File "app.py", line 2, in run\n'
                "    return username\n"
                "NameError: name 'username' is not defined\n"
            ),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["suggestion"]["available"] is False
    assert body["suggestion"]["comparison"]["unified_diff"] == ""
    assert body["suggestion"]["limitation"]


def test_analyze_endpoint_rejects_oversized_source_before_analysis() -> None:
    response = request(
        "POST",
        "/api/analyze",
        json={
            "source": "x" * 20_001,
            "traceback": "RuntimeError: stopped",
        },
    )

    assert response.status_code == 422


def test_analyze_endpoint_never_executes_a_host_file_write_payload(tmp_path) -> None:
    marker = tmp_path / "must-not-be-created.txt"
    source = (
        f"open({str(marker)!r}, 'w').write('host code executed')\n"
        "missing_name\n"
    )
    response = request(
        "POST",
        "/api/analyze",
        json={
            "source": source,
            "traceback": (
                "Traceback (most recent call last):\n"
                '  File "payload.py", line 2, in <module>\n'
                "    missing_name\n"
                "NameError: name 'missing_name' is not defined\n"
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["safety"]["executed"] is False
    assert marker.exists() is False


def test_guardian_endpoint_returns_line_level_diagnostics_and_fix() -> None:
    response = request(
        "POST",
        "/api/guardian",
        json={
            "source": "def greet(user_name):\n    return 'hello ' + username\n",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid_syntax"] is True
    assert body["diagnostics"][0]["line_number"] == 2
    assert body["diagnostics"][0]["severity"] == "error"
    assert body["diagnostics"][0]["fix"]["available"] is True


def test_guardian_endpoint_handles_empty_source_without_false_alarm() -> None:
    response = request("POST", "/api/guardian", json={"source": ""})

    assert response.status_code == 200
    assert response.json() == {
        "valid_syntax": True,
        "line_count": 0,
        "diagnostics": [],
    }


def test_evidence_endpoint_never_runs_by_default() -> None:
    response = request(
        "POST",
        "/api/evidence",
        json={
            "source_before": "open('/tmp/host-marker', 'w').write('x')\n",
            "source_after": "print('safe')\n",
            "confirm": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["before"] is None
    assert body["after"] is None
    assert body["scorecard"]["overall"] == "unavailable"
