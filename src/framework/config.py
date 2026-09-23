from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _safe_relative_path(value: object, field: str) -> Path:
    result = Path(str(value))
    if result.is_absolute() or ".." in result.parts:
        raise ValueError(f"{field} must be a safe path relative to the repository")
    return result


@dataclass(frozen=True)
class HotspotDiscoveryConfig:
    harness: Path
    command: tuple[str, ...]
    classification_command: tuple[str, ...] | None
    classification_sizes: tuple[int, ...]
    image: str
    limit: int
    cpus: float
    memory: str
    pids: int
    timeout_seconds: int
    max_output_bytes: int
    validation_expected_symbol: str | None

    def manifest_dict(self) -> dict[str, Any]:
        return {
            "harness": str(self.harness),
            "command": list(self.command),
            "classification_command": (
                list(self.classification_command)
                if self.classification_command is not None
                else None
            ),
            "classification_sizes": list(self.classification_sizes),
            "image": self.image,
            "limit": self.limit,
            "cpus": self.cpus,
            "memory": self.memory,
            "pids": self.pids,
            "timeout_seconds": self.timeout_seconds,
            "max_output_bytes": self.max_output_bytes,
            "validation_expected_symbol": self.validation_expected_symbol,
        }


@dataclass(frozen=True)
class ExecutionSandboxConfig:
    image: str
    cpus: float
    memory: str
    pids: int
    timeout_seconds: int
    max_output_bytes: int

    def manifest_dict(self) -> dict[str, Any]:
        return {
            "image": self.image,
            "cpus": self.cpus,
            "memory": self.memory,
            "pids": self.pids,
            "timeout_seconds": self.timeout_seconds,
            "max_output_bytes": self.max_output_bytes,
        }


@dataclass(frozen=True)
class ProfilerCallbackConfig:
    module: Path
    limit: int
    frames: int

    def manifest_dict(self) -> dict[str, Any]:
        return {
            "module": str(self.module),
            "limit": self.limit,
            "frames": self.frames,
        }


@dataclass(frozen=True)
class FrameworkConfig:
    task_id: str
    repository: Path | None
    repository_url: str | None
    repository_cache: Path
    baseline_commit: str | None
    human_fix_commit: str | None
    target_mode: str
    target_file: Path | None
    target_symbol: str | None
    hotspot_discovery: HotspotDiscoveryConfig | None
    execution_sandbox: ExecutionSandboxConfig | None
    profiler_callback: ProfilerCallbackConfig | None
    editable_files: tuple[Path, ...]
    context_files: tuple[Path, ...]
    targeted_test_command: tuple[str, ...]
    full_test_command: tuple[str, ...]
    invariant_test_command: tuple[str, ...] | None
    benchmark_command: tuple[str, ...]
    benchmark_mode: str
    benchmark_generation_max_repairs: int
    benchmark_fast_mode: bool
    resource_command: tuple[str, ...] | None
    original_workload_command: tuple[str, ...] | None
    primary_benchmark: str | None
    experiment_runs: int
    max_iterations: int
    no_improvement_limit: int
    optimization_objective: str
    min_speedup_percent: float
    min_workload_speedup_percent: float
    min_memory_reduction_percent: float
    max_runtime_regression_percent: float
    require_significance: bool
    timeout_seconds: int
    temperature: float
    model: str
    artifacts_root: Path
    keep_workspaces: bool

    @classmethod
    def load(cls, path: Path, project_root: Path) -> "FrameworkConfig":
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

        def resolve(value: str) -> Path:
            result = Path(value)
            return result if result.is_absolute() else project_root / result

        def expand_command(values: list[object] | None) -> tuple[str, ...] | None:
            if values is None:
                return None
            replacements = {
                "{project_root}": str(project_root),
                "{python}": str(project_root / ".venv" / "bin" / "python"),
            }
            expanded: list[str] = []
            for value in values:
                item = str(value)
                for old, new in replacements.items():
                    item = item.replace(old, new)
                expanded.append(item)
            return tuple(expanded)

        repository_value = raw.get("repository")
        repository = resolve(str(repository_value)) if repository_value else None
        repository_url = (
            str(raw["repository_url"]).strip()
            if raw.get("repository_url")
            else None
        )
        target_mode = str(raw.get("target_mode", "manual"))
        target_file = (
            _safe_relative_path(raw["target_file"], "target_file")
            if raw.get("target_file")
            else None
        )
        editable_default = [str(target_file)] if target_file is not None else []
        editable_values = raw.get("editable_files", editable_default)
        context_values = raw.get("context_files", [])
        hotspot_raw = raw.get("hotspot_discovery") or {}
        hotspot_discovery = None
        if hotspot_raw:
            hotspot_discovery = HotspotDiscoveryConfig(
                harness=resolve(str(hotspot_raw["harness"])),
                command=tuple(
                    str(value) for value in hotspot_raw.get("command", [])
                ),
                classification_command=(
                    tuple(
                        str(value)
                        for value in hotspot_raw["classification_command"]
                    )
                    if hotspot_raw.get("classification_command")
                    else None
                ),
                classification_sizes=tuple(
                    int(value)
                    for value in hotspot_raw.get("classification_sizes", [])
                ),
                image=str(hotspot_raw.get("image", "python:3.11-slim")),
                limit=int(hotspot_raw.get("limit", 5)),
                cpus=float(hotspot_raw.get("cpus", 1.0)),
                memory=str(hotspot_raw.get("memory", "512m")),
                pids=int(hotspot_raw.get("pids", 64)),
                timeout_seconds=int(hotspot_raw.get("timeout_seconds", 120)),
                max_output_bytes=int(hotspot_raw.get("max_output_bytes", 1_000_000)),
                validation_expected_symbol=(
                    str(hotspot_raw["validation_expected_symbol"])
                    if hotspot_raw.get("validation_expected_symbol")
                    else None
                ),
            )
        execution_raw = raw.get("execution_sandbox") or {}
        execution_sandbox = None
        if execution_raw and bool(execution_raw.get("enabled", True)):
            execution_sandbox = ExecutionSandboxConfig(
                image=str(
                    execution_raw.get(
                        "image", "perf-benchmark-sandbox:py311-v1"
                    )
                ),
                cpus=float(execution_raw.get("cpus", 1.0)),
                memory=str(execution_raw.get("memory", "1g")),
                pids=int(execution_raw.get("pids", 128)),
                timeout_seconds=int(
                    execution_raw.get("timeout_seconds", raw.get("timeout_seconds", 600))
                ),
                max_output_bytes=int(
                    execution_raw.get("max_output_bytes", 2_000_000)
                ),
            )
        callback_raw = raw.get("profiler_callback") or {}
        profiler_callback = None
        if callback_raw:
            profiler_callback = ProfilerCallbackConfig(
                module=resolve(str(callback_raw["module"])),
                limit=int(callback_raw.get("limit", 5)),
                frames=int(callback_raw.get("frames", 10)),
            )
        legacy_test = raw.get("test_command")
        targeted_test = expand_command(raw.get("targeted_test_command", legacy_test))
        full_test = expand_command(raw.get("full_test_command", legacy_test))
        benchmark_mode = str(raw.get("benchmark_mode", "fixed"))
        benchmark = expand_command(raw.get("benchmark_command")) or ()
        if targeted_test is None or full_test is None:
            raise ValueError(
                "targeted_test_command and full_test_command must be configured"
            )

        config = cls(
            task_id=str(raw["task_id"]),
            repository=repository,
            repository_url=repository_url,
            repository_cache=resolve(
                str(raw.get("repository_cache", ".cache/repositories"))
            ),
            baseline_commit=(
                str(raw["baseline_commit"]).strip()
                if raw.get("baseline_commit")
                else None
            ),
            human_fix_commit=(
                str(raw["human_fix_commit"]).strip()
                if raw.get("human_fix_commit")
                else None
            ),
            target_mode=target_mode,
            target_file=target_file,
            target_symbol=(
                str(raw["target_symbol"]) if raw.get("target_symbol") else None
            ),
            hotspot_discovery=hotspot_discovery,
            execution_sandbox=execution_sandbox,
            profiler_callback=profiler_callback,
            editable_files=tuple(
                _safe_relative_path(value, "editable_files")
                for value in editable_values
            ),
            context_files=tuple(
                _safe_relative_path(value, "context_files")
                for value in context_values
            ),
            targeted_test_command=targeted_test,
            full_test_command=full_test,
            invariant_test_command=expand_command(raw.get("invariant_test_command")),
            benchmark_command=benchmark,
            benchmark_mode=benchmark_mode,
            benchmark_generation_max_repairs=int(
                raw.get("benchmark_generation_max_repairs", 3)
            ),
            benchmark_fast_mode=bool(raw.get("benchmark_fast_mode", False)),
            resource_command=expand_command(raw.get("resource_command")),
            original_workload_command=expand_command(
                raw.get("original_workload_command")
            ),
            primary_benchmark=(
                str(raw["primary_benchmark"])
                if raw.get("primary_benchmark")
                else None
            ),
            experiment_runs=int(raw.get("experiment_runs", 1)),
            max_iterations=int(raw.get("max_iterations", 3)),
            no_improvement_limit=int(
                raw.get("no_improvement_limit", raw.get("max_iterations", 3))
            ),
            optimization_objective=str(
                raw.get("optimization_objective", "runtime")
            ),
            min_speedup_percent=float(raw.get("min_speedup_percent", 3.0)),
            min_workload_speedup_percent=float(
                raw.get(
                    "min_workload_speedup_percent",
                    raw.get("min_speedup_percent", 3.0),
                )
            ),
            min_memory_reduction_percent=float(
                raw.get("min_memory_reduction_percent", 10.0)
            ),
            max_runtime_regression_percent=float(
                raw.get("max_runtime_regression_percent", 10.0)
            ),
            require_significance=bool(raw.get("require_significance", True)),
            timeout_seconds=int(raw.get("timeout_seconds", 600)),
            temperature=float(raw.get("temperature", 0)),
            model=str(raw.get("model", "deepseek-v4-pro")),
            artifacts_root=resolve(
                str(raw.get("artifacts_root", "artifacts/framework_runs"))
            ),
            keep_workspaces=bool(raw.get("keep_workspaces", False)),
        )
        config.validate()
        return config

    @property
    def source_path(self) -> Path:
        if self.repository is None:
            raise ValueError("source_path is only available for local repositories")
        if self.target_file is None:
            raise ValueError("source_path is unavailable before target discovery")
        return self.repository / self.target_file

    @property
    def is_remote(self) -> bool:
        return self.repository_url is not None

    def manifest_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repository": str(self.repository) if self.repository else None,
            "repository_url": self.repository_url,
            "baseline_commit": self.baseline_commit,
            "human_fix_commit": self.human_fix_commit,
            "target_mode": self.target_mode,
            "target_file": str(self.target_file) if self.target_file else None,
            "target_symbol": self.target_symbol,
            "hotspot_discovery": (
                self.hotspot_discovery.manifest_dict()
                if self.hotspot_discovery
                else None
            ),
            "execution_sandbox": (
                self.execution_sandbox.manifest_dict()
                if self.execution_sandbox
                else None
            ),
            "profiler_callback": (
                self.profiler_callback.manifest_dict()
                if self.profiler_callback
                else None
            ),
            "editable_files": [str(path) for path in self.editable_files],
            "context_files": [str(path) for path in self.context_files],
            "targeted_test_command": list(self.targeted_test_command),
            "full_test_command": list(self.full_test_command),
            "invariant_test_command": (
                list(self.invariant_test_command)
                if self.invariant_test_command
                else None
            ),
            "benchmark_command": list(self.benchmark_command),
            "benchmark_mode": self.benchmark_mode,
            "benchmark_generation_max_repairs": self.benchmark_generation_max_repairs,
            "benchmark_fast_mode": self.benchmark_fast_mode,
            "resource_command": (
                list(self.resource_command) if self.resource_command else None
            ),
            "original_workload_command": (
                list(self.original_workload_command)
                if self.original_workload_command
                else None
            ),
            "primary_benchmark": self.primary_benchmark,
            "experiment_runs": self.experiment_runs,
            "max_iterations": self.max_iterations,
            "optimization_objective": self.optimization_objective,
            "min_speedup_percent": self.min_speedup_percent,
            "min_workload_speedup_percent": self.min_workload_speedup_percent,
            "min_memory_reduction_percent": self.min_memory_reduction_percent,
            "max_runtime_regression_percent": self.max_runtime_regression_percent,
            "require_significance": self.require_significance,
            "model": self.model,
            "keep_workspaces": self.keep_workspaces,
        }

    def validate(self) -> None:
        if bool(self.repository) == bool(self.repository_url):
            raise ValueError("Configure exactly one of repository or repository_url")
        if self.repository is not None and not self.repository.is_dir():
            raise ValueError(f"Repository does not exist: {self.repository}")
        if (
            self.repository is not None
            and self.target_file is not None
            and not self.source_path.is_file()
        ):
            raise ValueError(f"Target file does not exist: {self.source_path}")
        if self.repository_url and not self.baseline_commit:
            raise ValueError("Remote repositories require baseline_commit")
        if self.target_mode not in {"manual", "auto"}:
            raise ValueError("target_mode must be manual or auto")
        if self.target_mode == "manual":
            if self.target_file is None or not self.target_symbol:
                raise ValueError("manual target mode requires target_file and target_symbol")
            if self.target_file not in self.editable_files:
                raise ValueError("target_file must be included in editable_files")
            if not self.editable_files:
                raise ValueError("editable_files must not be empty")
        else:
            if self.target_file is not None or self.target_symbol:
                raise ValueError(
                    "auto target mode must not preconfigure target_file or target_symbol"
                )
            if self.editable_files:
                raise ValueError(
                    "auto target mode derives editable_files from the selected hotspot"
                )
            if self.hotspot_discovery is None:
                raise ValueError("auto target mode requires hotspot_discovery")
            if not self.hotspot_discovery.harness.is_dir():
                raise ValueError(
                    f"Hotspot harness does not exist: {self.hotspot_discovery.harness}"
                )
            if (
                not self.hotspot_discovery.command
                and self.hotspot_discovery.classification_command is None
            ):
                raise ValueError(
                    "hotspot_discovery requires command or classification_command"
                )
            if self.hotspot_discovery.limit < 1:
                raise ValueError("hotspot_discovery.limit must be at least 1")
            if self.hotspot_discovery.classification_command is not None:
                if len(self.hotspot_discovery.classification_sizes) < 2:
                    raise ValueError(
                        "routed hotspot discovery requires at least two "
                        "classification_sizes"
                    )
                if not any(
                    "{size}" in value
                    for value in self.hotspot_discovery.classification_command
                ):
                    raise ValueError(
                        "classification_command must contain a {size} placeholder"
                    )
                if not any(
                    "{output}" in value
                    for value in self.hotspot_discovery.classification_command
                ):
                    raise ValueError(
                        "classification_command must contain an {output} placeholder"
                    )
                if self.profiler_callback is None:
                    raise ValueError(
                        "routed hotspot discovery requires profiler_callback"
                    )
        if self.profiler_callback is not None:
            if not self.profiler_callback.module.is_file():
                raise ValueError(
                    "Profiler callback module does not exist: "
                    f"{self.profiler_callback.module}"
                )
            if self.profiler_callback.limit < 1:
                raise ValueError("profiler_callback.limit must be positive")
            if self.profiler_callback.frames < 1:
                raise ValueError("profiler_callback.frames must be positive")
            if self.execution_sandbox is None:
                raise ValueError(
                    "profiler_callback requires execution_sandbox to be enabled"
                )
        if not self.targeted_test_command or not self.full_test_command:
            raise ValueError("test commands must not be empty")
        if self.benchmark_mode not in {"fixed", "generated"}:
            raise ValueError("benchmark_mode must be fixed or generated")
        if self.benchmark_mode == "fixed" and not any(
            "{output}" in value for value in self.benchmark_command
        ):
            raise ValueError("benchmark_command must contain an {output} placeholder")
        if self.benchmark_generation_max_repairs < 0:
            raise ValueError("benchmark_generation_max_repairs must not be negative")
        if self.resource_command and not any(
            "{output}" in value for value in self.resource_command
        ):
            raise ValueError("resource_command must contain an {output} placeholder")
        if self.original_workload_command and not any(
            "{output}" in value for value in self.original_workload_command
        ):
            raise ValueError(
                "original_workload_command must contain an {output} placeholder"
            )
        if self.experiment_runs < 1 or self.max_iterations < 1:
            raise ValueError("experiment_runs and max_iterations must be at least 1")
        if self.no_improvement_limit < 1:
            raise ValueError("no_improvement_limit must be at least 1")
        if self.optimization_objective not in {"runtime", "memory"}:
            raise ValueError(
                "optimization_objective must be either runtime or memory"
            )
        if self.min_speedup_percent < 0:
            raise ValueError("min_speedup_percent must not be negative")
        if self.min_workload_speedup_percent < 0:
            raise ValueError("min_workload_speedup_percent must not be negative")
        if self.min_memory_reduction_percent < 0:
            raise ValueError("min_memory_reduction_percent must not be negative")
        if self.max_runtime_regression_percent < 0:
            raise ValueError("max_runtime_regression_percent must not be negative")
        if (
            self.optimization_objective == "memory"
            and self.benchmark_mode == "fixed"
            and not self.resource_command
        ):
            raise ValueError(
                "memory optimization requires resource_command with tracemalloc output"
            )
