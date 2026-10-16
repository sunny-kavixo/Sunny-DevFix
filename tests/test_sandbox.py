import subprocess
import asyncio

import httpx

from sunny_devfix.app import app

from sunny_devfix import sandbox


def test_evidence_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("DEVFIX_SANDBOX_ENABLED", raising=False)

    result = sandbox.run_evidence("raise RuntimeError()\n", "print('ok')\n")

    assert result.available is False
    assert result.before is None
    assert result.scorecard.overall == "unavailable"
    assert result.scorecard.reproduction_passed is False


def test_evidence_requires_explicit_confirmation_at_the_api() -> None:
    async def make_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.post(
                "/api/evidence",
                json={
                    "source_before": "raise RuntimeError()\n",
                    "source_after": "print('ok')\n",
                },
            )

    response = asyncio.run(make_request())

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert "confirmation" in response.json()["message"].lower()


def test_evidence_uses_hardened_docker_command_and_verifies_repair(monkeypatch) -> None:
    monkeypatch.setenv("DEVFIX_SANDBOX_ENABLED", "true")
    monkeypatch.setattr(sandbox.shutil, "which", lambda name: "/usr/bin/docker")
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[1:4] == ["image", "inspect", "sunny-devfix:local"]:
            return subprocess.CompletedProcess(command, 0, b"{}", b"")
        if len(calls) == 2:
            return subprocess.CompletedProcess(command, 1, b"", b"RuntimeError\n")
        return subprocess.CompletedProcess(command, 0, b"fixed\n", b"")

    monkeypatch.setattr(sandbox.subprocess, "run", fake_run)
    result = sandbox.run_evidence(
        "raise RuntimeError('broken')\n",
        "print('fixed')\n",
    )

    assert result.available is True
    assert result.scorecard.overall == "verified"
    assert result.before is not None and result.before.status == "failed"
    assert result.after is not None and result.after.status == "passed"
    run_command = calls[1]
    for flag in (
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--memory",
        "128m",
        "--user",
        "65532:65532",
    ):
        assert flag in run_command
    assert "raise RuntimeError('broken')" not in run_command
    assert run_command[0:2] == ["/usr/bin/docker", "run"]
