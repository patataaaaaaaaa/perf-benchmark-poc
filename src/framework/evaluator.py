from __future__ import annotations

import json
import os
import signal
import statistics
import subprocess
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import psutil
import pyperf
from pyperf._compare import is_significant_benchs

from src.framework.sandbox import SandboxLimits, run_in_docker


@dataclass(frozen=True)
class ResourceMetrics:
    wall_seconds: float
    user_cpu_seconds: float
    system_cpu_seconds: float
    cpu_to_wall_ratio: float | None
    peak_rss_bytes: int
    read_bytes: int | None
    write_bytes: int | None
    read_count: int | None
    write_count: int | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    return_code: int | None
    stdout: str
    stderr: str
    metrics: ResourceMetrics
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.return_code == 0 and not self.timed_out

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "metrics": self.metrics.to_dict(),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class BenchmarkStats:
    name: str
    value_count: int
    mean_seconds: float
    median_seconds: float
    min_seconds: float
    robust_rsd_percent: float | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PerformanceResult:
    command_result: CommandResult
    result_path: str
    primary_benchmark: str | None
    benchmarks: dict[str, BenchmarkStats]

    @property
    def primary(self) -> BenchmarkStats | None:
        if not self.benchmarks:
            return None
        if self.primary_benchmark and self.primary_benchmark in self.benchmarks:
            return self.benchmarks[self.primary_benchmark]
        return next(iter(self.benchmarks.values()))

    @property
    def benchmark_name(self) -> str | None:
        return self.primary.name if self.primary else None

    @property
    def value_count(self) -> int:
        return self.primary.value_count if self.primary else 0

    @property
    def mean_seconds(self) -> float | None:
        return self.primary.mean_seconds if self.primary else None

    @property
    def median_seconds(self) -> float | None:
        return self.primary.median_seconds if self.primary else None

    @property
    def robust_rsd_percent(self) -> float | None:
        return self.primary.robust_rsd_percent if self.primary else None

    @property
    def passed(self) -> bool:
        return self.command_result.passed and self.primary is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "command": self.command_result.to_dict(),
            "result_path": self.result_path,
            "primary_benchmark": self.primary_benchmark,
            "benchmarks": {
                name: stats.to_dict() for name, stats in self.benchmarks.items()
            },
            "passed": self.passed,
        }


@dataclass(frozen=True)
class PerformanceComparison:
    benchmark: str
    speedup_percent: float
    baseline_median_seconds: float
    candidate_median_seconds: float
    significant: bool
    t_score: float | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MemoryComparison:
    metric: str
    reduction_percent: float
    baseline_bytes: int
    candidate_bytes: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ResourceResult:
    command_result: CommandResult
    result_path: str
    tracemalloc_peak_bytes: int | None
    workload: dict[str, object] | None

    @property
    def passed(self) -> bool:
        return self.command_result.passed and self.tracemalloc_peak_bytes is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "command": self.command_result.to_dict(),
            "result_path": self.result_path,
            "tracemalloc_peak_bytes": self.tracemalloc_peak_bytes,
            "workload": self.workload,
            "passed": self.passed,
        }


def _empty_metrics(wall_seconds: float = 0.0) -> ResourceMetrics:
    return ResourceMetrics(
        wall_seconds=wall_seconds,
        user_cpu_seconds=0.0,
        system_cpu_seconds=0.0,
        cpu_to_wall_ratio=None,
        peak_rss_bytes=0,
        read_bytes=None,
        write_bytes=None,
        read_count=None,
        write_count=None,
    )


def _sample_process_tree(
    root: psutil.Process,
    cpu: dict[int, tuple[float, float]],
    io: dict[int, tuple[int, int, int, int]],
) -> int:
    peak_current_rss = 0
    try:
        processes = [root, *root.children(recursive=True)]
    except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
        processes = []
    for process in processes:
        try:
            times = process.cpu_times()
            previous = cpu.get(process.pid, (0.0, 0.0))
            cpu[process.pid] = (
                max(previous[0], float(times.user)),
                max(previous[1], float(times.system)),
            )
            peak_current_rss += int(process.memory_info().rss)
            try:
                counters = process.io_counters()
            except (psutil.AccessDenied, AttributeError, NotImplementedError):
                continue
            previous_io = io.get(process.pid, (0, 0, 0, 0))
            io[process.pid] = (
                max(previous_io[0], int(counters.read_bytes)),
                max(previous_io[1], int(counters.write_bytes)),
                max(previous_io[2], int(counters.read_count)),
                max(previous_io[3], int(counters.write_count)),
            )
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            ProcessLookupError,
            PermissionError,
        ):
            continue
    return peak_current_rss


def run_command(
    command: tuple[str, ...] | list[str], cwd: Path, timeout_seconds: int
) -> CommandResult:
    environment = os.environ.copy()
    started = time.perf_counter()
    cpu: dict[int, tuple[float, float]] = {}
    io: dict[int, tuple[int, int, int, int]] = {}
    peak_rss = 0
    timed_out = False
    with tempfile.TemporaryFile(mode="w+") as stdout_file, tempfile.TemporaryFile(
        mode="w+"
    ) as stderr_file:
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=environment,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
            start_new_session=True,
        )
        root = psutil.Process(process.pid)
        deadline = started + timeout_seconds
        while process.poll() is None:
            peak_rss = max(peak_rss, _sample_process_tree(root, cpu, io))
            if time.perf_counter() >= deadline:
                timed_out = True
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    process.kill()
                break
            time.sleep(0.02)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        peak_rss = max(peak_rss, _sample_process_tree(root, cpu, io))
        wall = time.perf_counter() - started
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read()
        stderr = stderr_file.read()

    user_cpu = sum(values[0] for values in cpu.values())
    system_cpu = sum(values[1] for values in cpu.values())
    io_supported = bool(io)
    metrics = ResourceMetrics(
        wall_seconds=wall,
        user_cpu_seconds=user_cpu,
        system_cpu_seconds=system_cpu,
        cpu_to_wall_ratio=(user_cpu + system_cpu) / wall if wall else None,
        peak_rss_bytes=peak_rss,
        read_bytes=sum(value[0] for value in io.values()) if io_supported else None,
        write_bytes=sum(value[1] for value in io.values()) if io_supported else None,
        read_count=sum(value[2] for value in io.values()) if io_supported else None,
        write_count=sum(value[3] for value in io.values()) if io_supported else None,
    )
    if timed_out:
        stderr += f"\nTimed out after {timeout_seconds} seconds."
    return CommandResult(
        command=list(command),
        return_code=None if timed_out else process.returncode,
        stdout=stdout,
        stderr=stderr,
        metrics=metrics,
        timed_out=timed_out,
    )


def _robust_rsd_percent(values: list[float]) -> float | None:
    if not values:
        return None
    median = statistics.median(values)
    if median == 0:
        return None
    deviations = [abs(value - median) for value in values]
    mad = statistics.median(deviations)
    return 100.0 * 1.4826 * mad / median


class Evaluator:
    def __init__(
        self,
        timeout_seconds: int,
        primary_benchmark: str | None = None,
        docker_image: str | None = None,
        project_root: Path | None = None,
        sandbox_limits: SandboxLimits | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.primary_benchmark = primary_benchmark
        self.docker_image = docker_image
        self.project_root = project_root
        self.sandbox_limits = sandbox_limits

    def run(
        self,
        command: tuple[str, ...] | list[str],
        repository: Path,
        output_dir: Path,
    ) -> CommandResult:
        if self.docker_image is None:
            return run_command(command, repository, self.timeout_seconds)
        if self.project_root is None or self.sandbox_limits is None:
            raise RuntimeError("Docker evaluator is missing project_root or limits")

        output_dir.mkdir(parents=True, exist_ok=True)
        mappings: list[tuple[Path, str]] = [
            (repository.resolve(), "/workspace"),
            ((self.project_root / "subjects").resolve(), "/subjects"),
            (output_dir.resolve(), "/artifacts"),
        ]
        mounts: list[tuple[Path, str]] = [
            ((self.project_root / "subjects").resolve(), "/subjects")
        ]
        translated: list[str] = []
        for index, raw in enumerate(command):
            value = str(raw)
            if index == 0:
                translated.append("python")
                continue
            path = Path(value)
            replacement: str | None = None
            if path.is_absolute():
                resolved = path.resolve()
                for host_root, container_root in mappings:
                    try:
                        relative = resolved.relative_to(host_root)
                    except ValueError:
                        continue
                    replacement = str(Path(container_root) / relative)
                    break
                if replacement is None and resolved.exists():
                    mount_root = resolved.parent
                    container_root = f"/input_{len(mounts)}"
                    mounts.append((mount_root, container_root))
                    mappings.append((mount_root, container_root))
                    replacement = str(Path(container_root) / resolved.name)
            translated.append(replacement if replacement is not None else value)

        metrics_name = f"command_metrics_{uuid.uuid4().hex}.json"
        inner_command = [
            "python",
            "/opt/framework/run_sandbox_command.py",
            "--metrics",
            f"/artifacts/{metrics_name}",
            "--",
            *translated,
        ]
        started = time.perf_counter()
        result = run_in_docker(
            image=self.docker_image,
            workspace=repository,
            harness=self.project_root / "scripts",
            output=output_dir,
            inner_command=inner_command,
            limits=self.sandbox_limits,
            readonly_mounts=tuple(mounts),
        )
        metrics_path = output_dir / metrics_name
        payload: dict[str, Any] = {}
        if metrics_path.is_file():
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics = ResourceMetrics(
            wall_seconds=float(payload.get("wall_seconds", time.perf_counter() - started)),
            user_cpu_seconds=float(payload.get("user_cpu_seconds", 0.0)),
            system_cpu_seconds=float(payload.get("system_cpu_seconds", 0.0)),
            cpu_to_wall_ratio=(
                float(payload["cpu_to_wall_ratio"])
                if payload.get("cpu_to_wall_ratio") is not None
                else None
            ),
            peak_rss_bytes=int(payload.get("peak_rss_bytes", 0)),
            read_bytes=(int(payload["read_bytes"]) if payload.get("read_bytes") is not None else None),
            write_bytes=(int(payload["write_bytes"]) if payload.get("write_bytes") is not None else None),
            read_count=(int(payload["read_count"]) if payload.get("read_count") is not None else None),
            write_count=(int(payload["write_count"]) if payload.get("write_count") is not None else None),
        )
        return CommandResult(
            command=list(result.command),
            return_code=None if result.timed_out else result.return_code,
            stdout=result.stdout,
            stderr=result.stderr,
            metrics=metrics,
            timed_out=result.timed_out,
        )

    def functional_test(
        self, repository: Path, command: tuple[str, ...], output_dir: Path
    ) -> CommandResult:
        return self.run(command, repository, output_dir)

    def performance_test(
        self,
        repository: Path,
        command_template: tuple[str, ...],
        result_path: Path,
    ) -> PerformanceResult:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        if result_path.exists():
            result_path.unlink()
        command = tuple(
            value.replace("{output}", str(result_path))
            for value in command_template
        )
        result = self.run(command, repository, result_path.parent)
        if not result.passed or not result_path.is_file():
            return PerformanceResult(result, str(result_path), self.primary_benchmark, {})

        suite = pyperf.BenchmarkSuite.load(str(result_path))
        benchmarks: dict[str, BenchmarkStats] = {}
        for benchmark in suite.get_benchmarks():
            values = list(benchmark.get_values())
            benchmarks[benchmark.get_name()] = BenchmarkStats(
                name=benchmark.get_name(),
                value_count=len(values),
                mean_seconds=benchmark.mean(),
                median_seconds=statistics.median(values),
                min_seconds=min(values),
                robust_rsd_percent=_robust_rsd_percent(values),
            )
        return PerformanceResult(
            result, str(result_path), self.primary_benchmark, benchmarks
        )

    def resource_test(
        self,
        repository: Path,
        command_template: tuple[str, ...],
        result_path: Path,
    ) -> ResourceResult:
        result_path.parent.mkdir(parents=True, exist_ok=True)
        if result_path.exists():
            result_path.unlink()
        command = tuple(
            value.replace("{output}", str(result_path))
            for value in command_template
        )
        result = self.run(command, repository, result_path.parent)
        payload: dict[str, object] = {}
        if result.passed and result_path.is_file():
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        peak = payload.get("tracemalloc_peak_bytes")
        workload = payload.get("workload")
        return ResourceResult(
            command_result=result,
            result_path=str(result_path),
            tracemalloc_peak_bytes=int(peak) if peak is not None else None,
            workload=workload if isinstance(workload, dict) else None,
        )


def compare_performance(
    baseline: PerformanceResult, candidate: PerformanceResult
) -> PerformanceComparison:
    baseline_primary = baseline.primary
    candidate_primary = candidate.primary
    if baseline_primary is None or candidate_primary is None:
        raise ValueError("Both results must contain the primary benchmark")
    if baseline_primary.name != candidate_primary.name:
        raise ValueError("Primary benchmark names differ")
    baseline_suite = pyperf.BenchmarkSuite.load(baseline.result_path)
    candidate_suite = pyperf.BenchmarkSuite.load(candidate.result_path)
    baseline_benchmark = baseline_suite.get_benchmark(baseline_primary.name)
    candidate_benchmark = candidate_suite.get_benchmark(candidate_primary.name)
    significant, t_score = is_significant_benchs(
        baseline_benchmark, candidate_benchmark
    )
    speedup = 100.0 * (
        baseline_primary.median_seconds - candidate_primary.median_seconds
    ) / baseline_primary.median_seconds
    return PerformanceComparison(
        benchmark=baseline_primary.name,
        speedup_percent=speedup,
        baseline_median_seconds=baseline_primary.median_seconds,
        candidate_median_seconds=candidate_primary.median_seconds,
        significant=bool(significant),
        t_score=float(t_score) if t_score is not None else None,
    )


def compare_memory(
    baseline: ResourceResult, candidate: ResourceResult
) -> MemoryComparison:
    baseline_bytes = baseline.tracemalloc_peak_bytes
    candidate_bytes = candidate.tracemalloc_peak_bytes
    if baseline_bytes is None or candidate_bytes is None:
        raise ValueError("Both resource results must contain tracemalloc peak bytes")
    if baseline_bytes <= 0:
        raise ValueError("Baseline tracemalloc peak must be positive")
    reduction = 100.0 * (baseline_bytes - candidate_bytes) / baseline_bytes
    return MemoryComparison(
        metric="tracemalloc_peak_bytes",
        reduction_percent=reduction,
        baseline_bytes=baseline_bytes,
        candidate_bytes=candidate_bytes,
    )


def speedup_percent(
    baseline: PerformanceResult, candidate: PerformanceResult
) -> float:
    if baseline.mean_seconds is None or candidate.mean_seconds is None:
        raise ValueError("Both baseline and candidate must contain a mean")
    return 100.0 * (
        baseline.mean_seconds - candidate.mean_seconds
    ) / baseline.mean_seconds
