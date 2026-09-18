from __future__ import annotations

import ast
import os
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from src.target.loader import TargetSpec


TargetHit = Literal["true", "false", "unknown"]


@dataclass(frozen=True)
class ValidationResult:
    stage: str
    passed: bool
    command: list[str]
    return_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @property
    def command_text(self) -> str:
        return shlex.join(self.command)


@dataclass(frozen=True)
class CandidateValidation:
    syntax: ValidationResult
    import_check: ValidationResult | None
    runtime: ValidationResult | None
    stability: ValidationResult | None
    target_hit: TargetHit

    @property
    def executable(self) -> bool:
        checks = (self.syntax, self.import_check, self.runtime)
        return all(check is not None and check.passed for check in checks) and (
            self.target_hit != "false"
        )

    @property
    def successful(self) -> bool:
        return self.executable and (
            self.stability is not None and self.stability.passed
        )

    def first_failure(self) -> ValidationResult:
        # Correctness failures take precedence over measurement stability.
        # A runnable benchmark that misses the requested target must be repaired
        # for target coverage, even when pyperf also reports noisy measurements.
        for result in (self.syntax, self.import_check, self.runtime):
            if result is not None and not result.passed:
                return result
        if self.target_hit == "false":
            return ValidationResult(
                stage="target_hit",
                passed=False,
                command=[],
                return_code=None,
                stdout="",
                stderr=(
                    "Static analysis found no reference to or invocation of the "
                    "specified target function."
                ),
            )
        if self.stability is not None and not self.stability.passed:
            return self.stability
        raise RuntimeError("No validation failure is available")

    def to_dict(self) -> dict[str, object]:
        return {
            "syntax": self.syntax.to_dict(),
            "import": self.import_check.to_dict() if self.import_check else None,
            "runtime": self.runtime.to_dict() if self.runtime else None,
            "stability": self.stability.to_dict() if self.stability else None,
            "target_hit": self.target_hit,
            "executable": self.executable,
            "successful": self.successful,
        }


def _run_command(
    stage: str,
    command: list[str],
    cwd: Path,
    timeout_seconds: int,
) -> ValidationResult:
    environment = os.environ.copy()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return ValidationResult(
            stage=stage,
            passed=completed.returncode == 0,
            command=command,
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        return ValidationResult(
            stage=stage,
            passed=False,
            command=command,
            return_code=None,
            stdout=_decode_timeout_output(exc.stdout),
            stderr=_decode_timeout_output(exc.stderr)
            + f"\nCommand timed out after {timeout_seconds} seconds.",
            timed_out=True,
        )


def _decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def syntax_check(
    benchmark_path: Path, cwd: Path, timeout_seconds: int
) -> ValidationResult:
    return _run_command(
        "syntax",
        [sys.executable, "-m", "py_compile", str(benchmark_path)],
        cwd,
        timeout_seconds,
    )


_IMPORT_CHECK_SCRIPT = r"""
import ast
import sys

path = sys.argv[1]
tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
nodes = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
module = ast.Module(body=nodes, type_ignores=[])
exec(compile(module, path, "exec"), {"__name__": "__benchmark_import_check__"})
""".strip()


def import_check(
    benchmark_path: Path, cwd: Path, timeout_seconds: int
) -> ValidationResult:
    return _run_command(
        "import",
        [sys.executable, "-c", _IMPORT_CHECK_SCRIPT, str(benchmark_path)],
        cwd,
        timeout_seconds,
    )


def runtime_check(
    benchmark_path: Path,
    result_path: Path,
    cwd: Path,
    timeout_seconds: int,
    fast_mode: bool,
) -> ValidationResult:
    command = [sys.executable, str(benchmark_path)]
    if fast_mode:
        command.append("--fast")
    command.extend(["-o", str(result_path)])
    result = _run_command("runtime", command, cwd, timeout_seconds)
    if result.passed and not result_path.is_file():
        return ValidationResult(
            stage="runtime",
            passed=False,
            command=command,
            return_code=result.return_code,
            stdout=result.stdout,
            stderr=result.stderr + "\nBenchmark exited successfully but produced no result JSON.",
        )
    return result


def stability_check(
    result_path: Path, cwd: Path, timeout_seconds: int
) -> ValidationResult:
    result = _run_command(
        "stability",
        [sys.executable, "-m", "pyperf", "check", str(result_path)],
        cwd,
        timeout_seconds,
    )
    combined = f"{result.stdout}\n{result.stderr}".lower()
    unstable = "may be unstable" in combined or "warning:" in combined
    return ValidationResult(
        stage=result.stage,
        passed=result.passed and not unstable,
        command=result.command,
        return_code=result.return_code,
        stdout=result.stdout,
        stderr=result.stderr,
        timed_out=result.timed_out,
    )


def _reference_names(tree: ast.AST, spec: TargetSpec) -> tuple[set[str], set[str]]:
    direct_names: set[str] = set()
    module_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == spec.module or (
                node.module and spec.qualified_name.startswith(f"{node.module}.")
            ):
                for alias in node.names:
                    if alias.name == spec.target:
                        direct_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == spec.module or spec.module.startswith(f"{alias.name}."):
                    module_aliases.add(alias.asname or alias.name.split(".")[0])
    return direct_names, module_aliases


def _is_target_reference(
    node: ast.AST, direct_names: set[str], module_aliases: set[str], target: str
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in direct_names
    if isinstance(node, ast.Attribute) and node.attr == target:
        root = node.value
        while isinstance(root, ast.Attribute):
            root = root.value
        return isinstance(root, ast.Name) and root.id in module_aliases
    return False


def check_target_hit(benchmark_code: str, spec: TargetSpec) -> TargetHit:
    try:
        tree = ast.parse(benchmark_code)
    except SyntaxError:
        return "unknown"

    direct_names, module_aliases = _reference_names(tree, spec)
    # An import of the target is evidence that the benchmark intends to use it,
    # but not enough to prove the timed path invokes it.
    referenced = bool(direct_names or module_aliases)
    for node in ast.walk(tree):
        if _is_target_reference(node, direct_names, module_aliases, spec.target):
            referenced = True
        if isinstance(node, ast.Call) and _is_target_reference(
            node.func, direct_names, module_aliases, spec.target
        ):
            return "true"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"bench_func", "bench_async_func"}:
                if any(
                    _is_target_reference(arg, direct_names, module_aliases, spec.target)
                    for arg in node.args
                ):
                    return "true"

    return "unknown" if referenced else "false"


def validate_candidate(
    benchmark_path: Path,
    result_path: Path,
    spec: TargetSpec,
    cwd: Path,
    timeout_seconds: int,
    fast_mode: bool,
) -> CandidateValidation:
    code = benchmark_path.read_text(encoding="utf-8")
    target_hit = check_target_hit(code, spec)
    syntax = syntax_check(benchmark_path, cwd, timeout_seconds)
    if not syntax.passed:
        return CandidateValidation(syntax, None, None, None, target_hit)

    imported = import_check(benchmark_path, cwd, timeout_seconds)
    if not imported.passed:
        return CandidateValidation(syntax, imported, None, None, target_hit)

    runtime = runtime_check(
        benchmark_path,
        result_path,
        cwd,
        timeout_seconds,
        fast_mode,
    )
    if not runtime.passed:
        return CandidateValidation(syntax, imported, runtime, None, target_hit)

    stability = stability_check(result_path, cwd, timeout_seconds)
    return CandidateValidation(syntax, imported, runtime, stability, target_hit)
