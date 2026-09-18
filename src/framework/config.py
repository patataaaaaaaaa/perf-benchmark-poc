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
class FrameworkConfig:
    task_id: str
    repository: Path | None
    repository_url: str | None
    repository_cache: Path
    baseline_commit: str | None
    human_fix_commit: str | None
    target_file: Path
    target_symbol: str
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
    primary_benchmark: str | None
    experiment_runs: int
    max_iterations: int
    no_improvement_limit: int
    min_speedup_percent: float
    require_significance: bool
    timeout_seconds: int
    temperature: float
    model: str
    artifacts_root: Path

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
        target_file = _safe_relative_path(raw["target_file"], "target_file")
        editable_values = raw.get("editable_files", [str(target_file)])
        context_values = raw.get("context_files", [])
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
            target_file=target_file,
            target_symbol=str(raw["target_symbol"]),
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
            min_speedup_percent=float(raw.get("min_speedup_percent", 3.0)),
            require_significance=bool(raw.get("require_significance", True)),
            timeout_seconds=int(raw.get("timeout_seconds", 600)),
            temperature=float(raw.get("temperature", 0)),
            model=str(raw.get("model", "deepseek-v4-pro")),
            artifacts_root=resolve(
                str(raw.get("artifacts_root", "artifacts/framework_runs"))
            ),
        )
        config.validate()
        return config

    @property
    def source_path(self) -> Path:
        if self.repository is None:
            raise ValueError("source_path is only available for local repositories")
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
            "target_file": str(self.target_file),
            "target_symbol": self.target_symbol,
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
            "primary_benchmark": self.primary_benchmark,
            "experiment_runs": self.experiment_runs,
            "max_iterations": self.max_iterations,
            "min_speedup_percent": self.min_speedup_percent,
            "require_significance": self.require_significance,
            "model": self.model,
        }

    def validate(self) -> None:
        if bool(self.repository) == bool(self.repository_url):
            raise ValueError("Configure exactly one of repository or repository_url")
        if self.repository is not None and not self.repository.is_dir():
            raise ValueError(f"Repository does not exist: {self.repository}")
        if self.repository is not None and not self.source_path.is_file():
            raise ValueError(f"Target file does not exist: {self.source_path}")
        if self.repository_url and not self.baseline_commit:
            raise ValueError("Remote repositories require baseline_commit")
        if self.target_file not in self.editable_files:
            raise ValueError("target_file must be included in editable_files")
        if not self.editable_files:
            raise ValueError("editable_files must not be empty")
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
        if self.experiment_runs < 1 or self.max_iterations < 1:
            raise ValueError("experiment_runs and max_iterations must be at least 1")
        if self.no_improvement_limit < 1:
            raise ValueError("no_improvement_limit must be at least 1")
        if self.min_speedup_percent < 0:
            raise ValueError("min_speedup_percent must not be negative")
