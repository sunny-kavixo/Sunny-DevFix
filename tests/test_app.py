import asyncio

import httpx

from sunny_devfix.app import app


def test_health_endpoint_reports_running_version() -> None:
    response = asyncio.run(_get_health())

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.2.0"}


async def _get_health() -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.get("/api/health")
