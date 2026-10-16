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
    assert stylesheet.status_code == 200
    assert "--mint" in stylesheet.text


def test_analyze_endpoint_returns_structured_result_without_execution() -> None:
    response = request(
        "POST",
        "/api/analyze",
        json={
            "source": "def greet(name):\n    return 'hello ' + username\n",
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
