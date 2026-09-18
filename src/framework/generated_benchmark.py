from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.framework.evaluator import CommandResult, run_command


@dataclass(frozen=True)
class GeneratedBenchmarkValidation:
    passed: bool
    stage: str
    primary_benchmark: str | None
    workload: dict[str, Any] | None
    commands: dict[str, CommandResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "stage": self.stage,
            "primary_benchmark": self.primary_benchmark,
            "workload": self.workload,
            "commands": {name: result.to_dict() for name, result in self.commands.items()},
        }

    def failure_evidence(self) -> dict[str, Any]:
        result = self.commands.get(self.stage)
        return {
            "stage": self.stage,
            "command": result.command if result else [],
            "return_code": result.return_code if result else None,
            "stdout": result.stdout if result else "",
            "stderr": result.stderr if result else "",
        }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_generated_benchmark(
    *,
    benchmark_path: Path,
    result_path: Path,
    workspace: Path,
    python: str,
    target_symbol: str,
    project_root: Path,
    timeout_seconds: int,
    fast_mode: bool,
) -> GeneratedBenchmarkValidation:
    commands: dict[str, CommandResult] = {}
    commands["syntax"] = run_command(
        (python, "-m", "py_compile", str(benchmark_path)), workspace, timeout_seconds
    )
    if not commands["syntax"].passed:
        return GeneratedBenchmarkValidation(False, "syntax", None, None, commands)

    commands["contract"] = run_command(
        (
            python,
            str(project_root / "scripts" / "validate_generated_benchmark.py"),
            str(benchmark_path),
            target_symbol,
        ),
        workspace,
        timeout_seconds,
    )
    if not commands["contract"].passed:
        return GeneratedBenchmarkValidation(False, "contract", None, None, commands)
    try:
        workload = json.loads(commands["contract"].stdout.strip().splitlines()[-1])
        primary = str(workload["primary_benchmark"])
    except (ValueError, KeyError, IndexError) as exc:
        commands["contract"] = CommandResult(
            command=commands["contract"].command,
            return_code=1,
            stdout=commands["contract"].stdout,
            stderr=commands["contract"].stderr + f"\nInvalid contract JSON: {exc}",
            metrics=commands["contract"].metrics,
        )
        return GeneratedBenchmarkValidation(False, "contract", None, None, commands)

    runtime_command = [python, str(benchmark_path)]
    if fast_mode:
        runtime_command.append("--fast")
    runtime_command.extend(["-o", str(result_path)])
    commands["runtime"] = run_command(runtime_command, workspace, timeout_seconds)
    if not commands["runtime"].passed or not result_path.is_file():
        return GeneratedBenchmarkValidation(False, "runtime", primary, workload, commands)
    return GeneratedBenchmarkValidation(True, "complete", primary, workload, commands)
