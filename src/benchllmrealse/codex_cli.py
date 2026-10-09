from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Sequence


class BenchLLMConfigurationError(ValueError):
    """Raised when a benchmark task or workspace is unsafe or incomplete."""


def _split_paths(value: Any, *, field: str) -> tuple[str, ...]:
    if isinstance(value, str):
        paths = tuple(shlex.split(value))
    elif isinstance(value, list):
        paths = tuple(str(item) for item in value)
    else:
        raise BenchLLMConfigurationError(
            f"PerfOpt field {field!r} must be a string or list"
        )
    if not paths:
        raise BenchLLMConfigurationError(f"PerfOpt field {field!r} is empty")
    for path in paths:
        candidate = PurePosixPath(path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise BenchLLMConfigurationError(
                f"PerfOpt field {field!r} contains an unsafe path: {path!r}"
            )
    return paths


def _repository_relative_paths(
    paths: Sequence[str], repository_name: str
) -> tuple[str, ...]:
    """Normalize dataset paths for a workspace rooted at the target repository."""
    normalized: list[str] = []
    for path in paths:
        parts = PurePosixPath(path).parts
        if parts and parts[0] == repository_name:
            parts = parts[1:]
        if not parts:
            raise BenchLLMConfigurationError(
                f"Task path must identify a file inside {repository_name}: {path!r}"
            )
        normalized.append(str(PurePosixPath(*parts)))
    return tuple(normalized)


@dataclass(frozen=True)
class BenchLLMPerfOptTask:
    benchmark_root: Path
    repository_name: str
    commit_id: str
    fix_commit: str
    prompt_number: int
    prompt_path: Path
    metadata_path: Path
    source_paths: tuple[str, ...]
    unit_test_paths: tuple[str, ...]
    prompt: str

    @classmethod
    def load(
        cls,
        benchmark_root: Path,
        repository_name: str,
        commit_id: str,
        prompt_number: int = 1,
    ) -> "BenchLLMPerfOptTask":
        benchmark_root = benchmark_root.resolve()
        if not repository_name or Path(repository_name).name != repository_name:
            raise BenchLLMConfigurationError("repository_name must be one directory name")
        if not commit_id or Path(commit_id).name != commit_id:
            raise BenchLLMConfigurationError("commit_id must not contain path separators")
        if prompt_number < 1:
            raise BenchLLMConfigurationError("prompt_number must be at least 1")

        metadata_path = (
            benchmark_root
            / "Dataset"
            / "PerfOpt"
            / repository_name
            / f"{commit_id}.json"
        )
        prompt_path = (
            benchmark_root
            / "Prompts"
            / repository_name
            / commit_id
            / f"prompt{prompt_number}.txt"
        )
        if not metadata_path.is_file():
            raise FileNotFoundError(f"PerfOpt task metadata not found: {metadata_path}")
        if not prompt_path.is_file():
            raise FileNotFoundError(f"PerfOpt prompt not found: {prompt_path}")

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        fix_commit = str(metadata.get("commit_hash") or commit_id)
        if not fix_commit.startswith(commit_id):
            raise BenchLLMConfigurationError(
                f"PerfOpt commit_hash {fix_commit!r} does not match task id {commit_id!r}"
            )
        source_paths = _split_paths(metadata.get("source_code"), field="source_code")
        unit_test_paths = _split_paths(metadata.get("unittest"), field="unittest")
        return cls(
            benchmark_root=benchmark_root,
            repository_name=repository_name,
            commit_id=commit_id,
            fix_commit=fix_commit,
            prompt_number=prompt_number,
            prompt_path=prompt_path,
            metadata_path=metadata_path,
            source_paths=_repository_relative_paths(source_paths, repository_name),
            unit_test_paths=_repository_relative_paths(unit_test_paths, repository_name),
            prompt=prompt_path.read_text(encoding="utf-8"),
        )


@dataclass(frozen=True)
class CodexCLIConfig:
    model: str
    executable: str = "codex"
    profile: str | None = None
    reasoning_effort: str | None = None
    timeout_seconds: int = 1200
    command_timeout_seconds: int = 1200

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise BenchLLMConfigurationError(
                "An exact model name is required for reproducible experiments"
            )
        if self.timeout_seconds < 1 or self.command_timeout_seconds < 1:
            raise BenchLLMConfigurationError("Timeouts must be positive")


@dataclass(frozen=True)
class ExternalCommandResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    elapsed_seconds: float
    stdout_file: str
    stderr_file: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class CodexRunResult:
    outcome: str
    returncode: int | None
    elapsed_seconds: float
    model: str
    profile: str | None
    codex_version: str | None
    baseline_commit: str
    changed_files: tuple[str, ...]
    forbidden_changes: tuple[str, ...]
    usage: dict[str, int | None]
    verification: ExternalCommandResult | None = None
    benchmark: ExternalCommandResult | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.outcome in {"agent_completed", "verified", "succeeded"}


def build_agent_prompt(task_prompt: str, allowed_paths: Sequence[str]) -> str:
    allowed = "\n".join(f"- {path}" for path in allowed_paths)
    return f"""You are the coding agent under evaluation in a Java performance benchmark.

Work directly in the current repository. Inspect the repository as needed, preserve observable
behavior, and optimize the performance issue described by the benchmark task below.

Experiment rules:
- You may modify only these source files:
{allowed}
- Do not modify tests, benchmark harnesses, build configuration, or evaluation scripts.
- Do not commit changes.
- You may run existing build and test commands to validate your work.
- The task text was originally written for a single-turn patch generator. Ignore any request in it
  to return JSON, search/replace blocks, or a textual diff. Edit the files in the workspace instead.
- Finish with a concise summary; the external harness, not you, decides whether the patch passes.

<benchmark_task>
{task_prompt}
</benchmark_task>
"""


def _run_git(workspace: Path, args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise BenchLLMConfigurationError(
            f"git {' '.join(args)} failed in {workspace}: {detail}"
        )
    return result.stdout


def _changed_files(workspace: Path) -> tuple[str, ...]:
    tracked = _run_git(workspace, ["diff", "--name-only", "-z", "HEAD"])
    untracked = _run_git(
        workspace, ["ls-files", "--others", "--exclude-standard", "-z"]
    )
    paths = {value for value in (tracked + untracked).split("\0") if value}
    return tuple(sorted(paths))


def _extract_usage(jsonl: str) -> dict[str, int | None]:
    keys = (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_tokens",
        "total_tokens",
    )
    usage: dict[str, int | None] = {key: None for key in keys}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in usage and isinstance(item, int):
                    usage[key] = item
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for line in jsonl.splitlines():
        try:
            visit(json.loads(line))
        except json.JSONDecodeError:
            continue
    if usage["total_tokens"] is None:
        components = [usage["input_tokens"], usage["output_tokens"]]
        if all(isinstance(value, int) for value in components):
            usage["total_tokens"] = sum(value or 0 for value in components)
    return usage


def _decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


class CodexCLIRunner:
    def __init__(self, config: CodexCLIConfig) -> None:
        self.config = config

    def _resolved_executable(self) -> str:
        candidate = shutil.which(self.config.executable)
        if candidate is None:
            raise FileNotFoundError(
                f"Codex CLI executable not found: {self.config.executable}"
            )
        return candidate

    def _version(self, executable: str) -> str | None:
        result = subprocess.run(
            [executable, "--version"], text=True, capture_output=True, check=False
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip() or result.stderr.strip() or None

    def command(self, workspace: Path, last_message_path: Path) -> list[str]:
        command = [
            self._resolved_executable(),
            "exec",
            "--json",
            "--color",
            "never",
            "--ephemeral",
            "--cd",
            str(workspace),
            "--sandbox",
            "workspace-write",
            "--config",
            'approval_policy="never"',
            "--model",
            self.config.model,
            "--output-last-message",
            str(last_message_path),
        ]
        if self.config.profile:
            command.extend(["--profile", self.config.profile])
        if self.config.reasoning_effort:
            command.extend(
                [
                    "--config",
                    f'model_reasoning_effort="{self.config.reasoning_effort}"',
                ]
            )
        command.append("-")
        return command

    def _run_external_command(
        self,
        *,
        name: str,
        command: Sequence[str],
        workspace: Path,
        artifacts_dir: Path,
    ) -> ExternalCommandResult:
        if not command:
            raise BenchLLMConfigurationError(f"{name} command is empty")
        expanded_command = tuple(
            part.replace("{workspace}", str(workspace)).replace(
                "{artifacts}", str(artifacts_dir)
            )
            for part in command
        )
        started = time.monotonic()
        try:
            result = subprocess.run(
                list(expanded_command),
                cwd=workspace,
                text=True,
                capture_output=True,
                timeout=self.config.command_timeout_seconds,
                check=False,
                env={
                    **os.environ,
                    "BENCHLLM_WORKSPACE": str(workspace),
                    "BENCHLLM_ARTIFACTS_DIR": str(artifacts_dir),
                },
            )
            returncode = result.returncode
            stdout = result.stdout
            stderr = result.stderr
        except subprocess.TimeoutExpired as exc:
            returncode = 124
            stdout = _decode_timeout_output(exc.stdout)
            stderr = _decode_timeout_output(exc.stderr)
            stderr += (
                f"\n{name} command timed out after "
                f"{self.config.command_timeout_seconds} seconds\n"
            )
        elapsed = time.monotonic() - started
        stdout_path = artifacts_dir / f"{name}.stdout.log"
        stderr_path = artifacts_dir / f"{name}.stderr.log"
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        return ExternalCommandResult(
            name=name,
            command=expanded_command,
            returncode=returncode,
            elapsed_seconds=elapsed,
            stdout_file=stdout_path.name,
            stderr_file=stderr_path.name,
        )

    def preflight(
        self,
        *,
        workspace: Path,
        allowed_paths: Sequence[str],
        artifacts_dir: Path,
        expected_baseline_ref: str | None = None,
    ) -> dict[str, Any]:
        workspace = workspace.resolve()
        artifacts_dir = artifacts_dir.resolve()
        if not workspace.is_dir():
            raise FileNotFoundError(f"Workspace not found: {workspace}")
        if not (workspace / ".git").exists():
            raise BenchLLMConfigurationError(
                f"Workspace must be an isolated Git checkout: {workspace}"
            )
        if not allowed_paths:
            raise BenchLLMConfigurationError("At least one allowed source path is required")
        normalized_allowed = _split_paths(list(allowed_paths), field="allowed_paths")
        try:
            artifacts_dir.relative_to(workspace)
        except ValueError:
            pass
        else:
            raise BenchLLMConfigurationError(
                "Artifacts directory must be outside the agent workspace"
            )
        dirty = _changed_files(workspace)
        if dirty:
            raise BenchLLMConfigurationError(
                "Workspace must be clean before the agent starts; changed files: "
                + ", ".join(dirty)
            )
        missing_sources = tuple(
            path for path in normalized_allowed if not (workspace / path).is_file()
        )
        if missing_sources:
            raise BenchLLMConfigurationError(
                "Task source files are missing from the workspace: "
                + ", ".join(missing_sources)
            )
        baseline_commit = _run_git(workspace, ["rev-parse", "HEAD"]).strip()
        expected_baseline_commit: str | None = None
        if expected_baseline_ref:
            expected_baseline_commit = _run_git(
                workspace, ["rev-parse", f"{expected_baseline_ref}^{{commit}}"]
            ).strip()
            if baseline_commit != expected_baseline_commit:
                raise BenchLLMConfigurationError(
                    "Workspace HEAD does not match the required buggy revision: "
                    f"HEAD={baseline_commit}, expected={expected_baseline_commit} "
                    f"from {expected_baseline_ref}"
                )
        executable = self._resolved_executable()
        return {
            "workspace": workspace,
            "artifacts_dir": artifacts_dir,
            "allowed_paths": normalized_allowed,
            "baseline_commit": baseline_commit,
            "expected_baseline_commit": expected_baseline_commit,
            "executable": executable,
            "codex_version": self._version(executable),
        }

    @staticmethod
    def _write_result(artifacts_dir: Path, result: CodexRunResult) -> None:
        payload = asdict(result)
        (artifacts_dir / "result.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def run(
        self,
        *,
        workspace: Path,
        task_prompt: str,
        allowed_paths: Sequence[str],
        artifacts_dir: Path,
        verification_command: Sequence[str] | None = None,
        benchmark_command: Sequence[str] | None = None,
        expected_baseline_ref: str | None = None,
    ) -> CodexRunResult:
        if benchmark_command and not verification_command:
            raise BenchLLMConfigurationError(
                "A benchmark command requires an authoritative verification command"
            )
        checked = self.preflight(
            workspace=workspace,
            allowed_paths=allowed_paths,
            artifacts_dir=artifacts_dir,
            expected_baseline_ref=expected_baseline_ref,
        )
        workspace = checked["workspace"]
        artifacts_dir = checked["artifacts_dir"]
        normalized_allowed = checked["allowed_paths"]
        baseline_commit = checked["baseline_commit"]
        artifacts_dir.mkdir(parents=True, exist_ok=False)
        prompt = build_agent_prompt(task_prompt, normalized_allowed)
        (artifacts_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        last_message_path = artifacts_dir / "last_message.txt"
        events_path = artifacts_dir / "codex_events.jsonl"
        stderr_path = artifacts_dir / "codex_stderr.log"
        diff_path = artifacts_dir / "agent.patch"
        command = self.command(workspace, last_message_path)
        version = checked["codex_version"]

        started = time.monotonic()
        timed_out = False
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=self.config.timeout_seconds,
                check=False,
            )
            returncode: int | None = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = None
            stdout = _decode_timeout_output(exc.stdout)
            stderr = _decode_timeout_output(exc.stderr)
            stderr += (
                f"\nCodex timed out after {self.config.timeout_seconds} seconds\n"
            )
        elapsed = time.monotonic() - started
        events_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")

        changed = _changed_files(workspace)
        allowed_set = set(normalized_allowed)
        forbidden = tuple(path for path in changed if path not in allowed_set)
        diff = _run_git(workspace, ["diff", "--binary", "HEAD", "--"])
        diff_path.write_text(diff, encoding="utf-8")
        usage = _extract_usage(stdout)

        if timed_out:
            outcome = "timeout"
            error = f"Codex exceeded {self.config.timeout_seconds} seconds"
        elif returncode != 0:
            outcome = "codex_error"
            error = stderr.strip() or f"Codex exited with {returncode}"
        elif forbidden:
            outcome = "policy_violation"
            error = "Agent modified files outside the task source allowlist"
        elif not changed:
            outcome = "no_changes"
            error = "Agent completed without changing any source file"
        else:
            outcome = "agent_completed"
            error = None

        verification: ExternalCommandResult | None = None
        benchmark: ExternalCommandResult | None = None
        if outcome == "agent_completed" and verification_command:
            verification = self._run_external_command(
                name="verification",
                command=verification_command,
                workspace=workspace,
                artifacts_dir=artifacts_dir,
            )
            if not verification.passed:
                outcome = "verification_failed"
                error = "The authoritative build/test command failed"
            else:
                outcome = "verified"

        if outcome == "verified" and benchmark_command:
            benchmark = self._run_external_command(
                name="benchmark",
                command=benchmark_command,
                workspace=workspace,
                artifacts_dir=artifacts_dir,
            )
            if benchmark.passed:
                outcome = "succeeded"
            else:
                outcome = "benchmark_failed"
                error = "The authoritative benchmark command failed"

        result = CodexRunResult(
            outcome=outcome,
            returncode=returncode,
            elapsed_seconds=elapsed,
            model=self.config.model,
            profile=self.config.profile,
            codex_version=version,
            baseline_commit=baseline_commit,
            changed_files=changed,
            forbidden_changes=forbidden,
            usage=usage,
            verification=verification,
            benchmark=benchmark,
            error=error,
        )
        self._write_result(artifacts_dir, result)
        return result
