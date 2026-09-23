from __future__ import annotations

import os
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SandboxLimits:
    cpus: float = 1.0
    memory: str = "512m"
    pids: int = 64
    timeout_seconds: int = 120
    max_output_bytes: int = 1_000_000


@dataclass(frozen=True)
class SandboxResult:
    command: tuple[str, ...]
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool
    output_truncated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_docker_command(
    *,
    container_name: str,
    image: str,
    workspace: Path,
    harness: Path,
    output: Path,
    inner_command: list[str],
    limits: SandboxLimits,
    readonly_mounts: tuple[tuple[Path, str], ...] = (),
) -> list[str]:
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--network",
        "none",
        "--user",
        "65534:65534",
        "--cpus",
        str(limits.cpus),
        "--memory",
        limits.memory,
        "--pids-limit",
        str(limits.pids),
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--env",
        "HOME=/tmp",
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        "--env",
        "OPENBLAS_NUM_THREADS=1",
        "--env",
        "OMP_NUM_THREADS=1",
        "--env",
        "MKL_NUM_THREADS=1",
        "--env",
        "PYTHONPATH=/workspace/src:/workspace",
        "--mount",
        f"type=bind,src={workspace.resolve()},dst=/workspace,readonly",
        "--mount",
        f"type=bind,src={harness.resolve()},dst=/harness,readonly",
        "--mount",
        f"type=bind,src={output.resolve()},dst=/artifacts",
    ]
    for source, destination in readonly_mounts:
        command.extend(
            [
                "--mount",
                f"type=bind,src={source.resolve()},dst={destination},readonly",
            ]
        )
    command.extend(
        [
        "--workdir",
        "/workspace",
        image,
        *inner_command,
        ]
    )
    return command


def _truncate(value: str, limit: int) -> tuple[str, bool]:
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return value, False
    suffix = b"\n...[output truncated by sandbox runner]\n"
    kept = encoded[: max(0, limit - len(suffix))] + suffix
    return kept.decode("utf-8", errors="replace"), True


def _remove_container(name: str) -> None:
    """Remove a timed-out container, tolerating Docker creation races."""

    for _attempt in range(10):
        removal = subprocess.run(
            ["docker", "rm", "-f", name],
            text=True,
            capture_output=True,
            check=False,
        )
        if removal.returncode == 0:
            return
        time.sleep(0.2)


def run_in_docker(
    *,
    image: str,
    workspace: Path,
    harness: Path,
    output: Path,
    inner_command: list[str],
    limits: SandboxLimits,
    readonly_mounts: tuple[tuple[Path, str], ...] = (),
) -> SandboxResult:
    """Run one command in a restricted, disposable Docker container.

    Host environment variables are intentionally not forwarded. In particular,
    API keys remain in the controller process outside the container.
    """

    output.mkdir(parents=True, exist_ok=True)
    # Docker Desktop bind mounts preserve host permissions. This directory only
    # contains disposable experiment output and must be writable by uid 65534.
    os.chmod(output, 0o777)
    name = f"perf-sandbox-{uuid.uuid4().hex[:12]}"
    command = build_docker_command(
        container_name=name,
        image=image,
        workspace=workspace,
        harness=harness,
        output=output,
        inner_command=inner_command,
        limits=limits,
        readonly_mounts=readonly_mounts,
    )
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=limits.timeout_seconds,
            check=False,
        )
        stdout, stdout_truncated = _truncate(
            completed.stdout, limits.max_output_bytes
        )
        stderr, stderr_truncated = _truncate(
            completed.stderr, limits.max_output_bytes
        )
        return SandboxResult(
            command=tuple(command),
            return_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            timed_out=False,
            output_truncated=stdout_truncated or stderr_truncated,
        )
    except subprocess.TimeoutExpired as exc:
        _remove_container(name)
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr or ""
        stdout, stdout_truncated = _truncate(stdout, limits.max_output_bytes)
        stderr, stderr_truncated = _truncate(stderr, limits.max_output_bytes)
        return SandboxResult(
            command=tuple(command),
            return_code=124,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
            output_truncated=stdout_truncated or stderr_truncated,
        )
