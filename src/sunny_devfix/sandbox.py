"""Run explicit repair evidence inside a disposable Docker container."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass

MAX_EVIDENCE_SOURCE_BYTES = 20_000
MAX_EVIDENCE_STDIN_BYTES = 4_000
DEFAULT_TIMEOUT_SECONDS = 4.0
DEFAULT_IMAGE = "sunny-devfix:local"
MAX_OUTPUT_CHARS = 4_000

_WRAPPER = (
    "import io,json,sys;"
    "p=json.loads(sys.stdin.read());"
    "sys.stdin=io.StringIO(p.get('stdin',''));"
    "scope={'__name__':'__main__'};"
    "exec(compile(p['source'],'<submitted>','exec'),scope,scope)"
)


@dataclass(frozen=True)
class SandboxRun:
    """Observed result from one isolated container run."""

    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False


@dataclass(frozen=True)
class EvidenceScorecard:
    """Evidence-backed status for a proposed correction."""

    overall: str
    syntax_valid: bool
    reproduction_passed: bool
    no_regression: bool
    claim: str


@dataclass(frozen=True)
class EvidenceResult:
    """Before/after reproduction result and its explicit limitations."""

    available: bool
    message: str
    before: SandboxRun | None
    after: SandboxRun | None
    regression_detected: bool
    scorecard: EvidenceScorecard


def sandbox_status(image: str = DEFAULT_IMAGE) -> tuple[bool, str]:
    """Check whether explicit Docker evidence can run without executing code."""

    if os.getenv("DEVFIX_SANDBOX_ENABLED", "false").lower() != "true":
        return False, "Docker evidence is disabled by default."
    docker = shutil.which("docker")
    if docker is None:
        return False, "Docker CLI is not available to the local engine."

    try:
        result = subprocess.run(
            [docker, "image", "inspect", image],
            capture_output=True,
            check=False,
            timeout=3,
            env=_docker_environment(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"Docker image check failed: {exc.__class__.__name__}."
    if result.returncode != 0:
        return False, f"Sandbox image '{image}' is not available locally."
    return True, f"Sandbox ready with image '{image}'."


def run_evidence(
    before: str,
    after: str,
    *,
    stdin: str = "",
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    image: str = DEFAULT_IMAGE,
) -> EvidenceResult:
    """Run before and after source only after explicit sandbox configuration."""

    if _byte_length(before) > MAX_EVIDENCE_SOURCE_BYTES:
        return _unavailable("The before source exceeds the evidence size limit.")
    if _byte_length(after) > MAX_EVIDENCE_SOURCE_BYTES:
        return _unavailable("The after source exceeds the evidence size limit.")
    if _byte_length(stdin) > MAX_EVIDENCE_STDIN_BYTES:
        return _unavailable("The reproduction input exceeds the evidence size limit.")

    configured, status_message = sandbox_status(image)
    if not configured:
        return _unavailable(status_message)

    before_run = _run_source(before, stdin, timeout_seconds, image)
    after_run = _run_source(after, stdin, timeout_seconds, image)
    regression = before_run.status == "passed" and after_run.status != "passed"
    after_passed = after_run.status == "passed"
    before_failed = before_run.status not in {"passed", "unavailable"}

    if regression:
        overall = "regressed"
        claim = "The proposed correction introduced a failing reproduction."
    elif before_failed and after_passed:
        overall = "verified"
        claim = "The correction changed this reproduction from failing to passing."
    elif after_passed:
        overall = "passed"
        claim = "The after version passed, but the before version was not failing."
    else:
        overall = "not-repaired"
        claim = "The after version did not pass this reproduction."

    scorecard = EvidenceScorecard(
        overall=overall,
        syntax_valid=after_run.status != "syntax-error",
        reproduction_passed=after_passed,
        no_regression=not regression,
        claim=claim,
    )
    return EvidenceResult(
        available=True,
        message=(
            "Both versions ran in disposable Docker containers with no network, "
            "no host mounts, a read-only filesystem, and resource limits."
        ),
        before=before_run,
        after=after_run,
        regression_detected=regression,
        scorecard=scorecard,
    )


def confirmation_required_result() -> EvidenceResult:
    """Return a non-executing response when the user did not confirm a run."""

    return _unavailable(
        "Explicit confirmation is required before any Docker reproduction runs."
    )


def _run_source(
    source: str,
    stdin: str,
    timeout_seconds: float,
    image: str,
) -> SandboxRun:
    docker = shutil.which("docker")
    if docker is None:
        return SandboxRun("unavailable", None, "", "Docker CLI unavailable.", 0)

    payload = json.dumps({"source": source, "stdin": stdin}).encode("utf-8")
    command = [
        docker,
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "64",
        "--memory",
        "128m",
        "--cpus",
        "0.5",
        "--ulimit",
        "nofile=64:64",
        "--ulimit",
        "fsize=1048576",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=16m",
        "--user",
        "65532:65532",
        "--workdir",
        "/tmp",
        "-i",
        image,
        "python",
        "-I",
        "-c",
        _WRAPPER,
    ]
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            input=payload,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            env=_docker_environment(),
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        return SandboxRun(
            status="timed-out",
            exit_code=None,
            stdout=_bounded_text(exc.stdout),
            stderr=_bounded_text(exc.stderr),
            duration_ms=duration_ms,
            timed_out=True,
        )
    except OSError as exc:
        return SandboxRun("unavailable", None, "", str(exc), 0)

    duration_ms = int((time.monotonic() - started) * 1000)
    stdout = _bounded_text(result.stdout)
    stderr = _bounded_text(result.stderr)
    status = "passed" if result.returncode == 0 else "failed"
    if "SyntaxError" in stderr or "IndentationError" in stderr:
        status = "syntax-error"
    return SandboxRun(
        status=status,
        exit_code=result.returncode,
        stdout=stdout,
        stderr=stderr,
        duration_ms=duration_ms,
    )


def _bounded_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if len(value) <= MAX_OUTPUT_CHARS:
        return value
    return f"{value[:MAX_OUTPUT_CHARS]}\n… output truncated …"


def _byte_length(value: str) -> int:
    return len(value.encode("utf-8"))


def _docker_environment() -> dict[str, str]:
    """Keep host secrets out of the Docker CLI environment."""

    path = os.getenv("PATH", "")
    return {"PATH": path}


def _unavailable(message: str) -> EvidenceResult:
    scorecard = EvidenceScorecard(
        overall="unavailable",
        syntax_valid=False,
        reproduction_passed=False,
        no_regression=True,
        claim="No functional claim was made because the sandbox did not run.",
    )
    return EvidenceResult(
        available=False,
        message=message,
        before=None,
        after=None,
        regression_detected=False,
        scorecard=scorecard,
    )
