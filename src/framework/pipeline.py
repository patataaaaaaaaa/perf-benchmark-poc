from __future__ import annotations

import csv
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil
import pyperf

from src.benchmark.analyzer import write_json
from src.framework.agents import FrameworkAgents
from src.framework.config import FrameworkConfig
from src.framework.generated_benchmark import (
    GeneratedBenchmarkValidation,
    sha256_file,
    validate_generated_benchmark,
)
from src.framework.hotspots import (
    module_name_from_path,
    parse_cprofile,
    select_top_hotspot,
)
from src.framework.memory_hotspots import parse_tracemalloc_snapshot
from src.framework.evaluator import (
    Evaluator,
    MemoryComparison,
    PerformanceComparison,
    PerformanceResult,
    ResourceResult,
    compare_memory,
    compare_performance,
)
from src.framework.patching import (
    apply_safe_patch,
    assert_hashes_unchanged,
    canonicalize_hunk_locations,
    extract_matching_context,
    extract_symbol_context,
    file_hashes,
    patch_stats,
    repository_diff,
    restore_patch,
)
from src.framework.repository import RepositoryManager
from src.framework.sandbox import SandboxLimits, run_in_docker
from src.framework.task_classification import (
    PerformanceSample,
    classify_performance_task,
)
from src.framework.profiler_routing import (
    require_objective_profiler,
    route_from_task_classification,
    select_target_profiler,
)


LOGGER = logging.getLogger("performance_framework")


def _performance_summary(result: PerformanceResult) -> dict[str, Any]:
    return {
        "primary_benchmark": result.primary_benchmark,
        "benchmarks": {
            name: stats.to_dict() for name, stats in result.benchmarks.items()
        },
        "measurement_process": result.command_result.metrics.to_dict(),
    }


def classify_baseline_evidence(
    baseline_resources: ResourceResult | None,
    baseline_workload: PerformanceResult | None,
) -> dict[str, Any]:
    """Classify baseline evidence without changing the optimization route."""

    source: str | None = None
    payload: dict[str, Any] | None = None
    if baseline_workload is not None and baseline_workload.passed:
        source = "original_workload"
        payload = baseline_workload.to_dict()
    elif baseline_resources is not None and baseline_resources.passed:
        source = "target_microbenchmark"
        payload = baseline_resources.to_dict()

    if source is None or payload is None:
        return {
            "status": "UNAVAILABLE",
            "mode": "observe_only",
            "routing_applied": False,
            "reason": "No successful baseline resource observation was available",
        }

    sample = PerformanceSample.from_mapping(payload)
    classification = classify_performance_task([sample])
    return {
        "status": "COMPLETE",
        "mode": "observe_only",
        "routing_applied": False,
        "sample_source": source,
        "classification": classification.to_dict(),
        "limitations": [
            "A single scale cannot establish a memory growth trend.",
            "The classification may create an observation-only profiler plan, but the pipeline does not execute that plan or change optimization decisions yet.",
        ],
    }


def decide_candidate(
    functional_passed: bool,
    performance_passed: bool,
    improvement_percent: float | None,
    minimum_percent: float,
    *,
    significant: bool = True,
    require_significance: bool = False,
    workload_passed: bool | None = None,
    workload_improvement_percent: float | None = None,
    minimum_workload_percent: float | None = None,
    workload_significant: bool = True,
    optimization_objective: str = "runtime",
    memory_passed: bool | None = None,
    memory_reduction_percent: float | None = None,
    minimum_memory_reduction_percent: float = 0.0,
    max_runtime_regression_percent: float = 0.0,
) -> str:
    if not functional_passed:
        return "REJECT_FUNCTIONAL"
    if not performance_passed or improvement_percent is None:
        return "REJECT_PERFORMANCE"
    if optimization_objective == "memory":
        if not memory_passed or memory_reduction_percent is None:
            return "REJECT_MEMORY_MEASUREMENT"
        if memory_reduction_percent < minimum_memory_reduction_percent:
            return "REJECT_MEMORY"
        if improvement_percent < -max_runtime_regression_percent:
            return "REJECT_RUNTIME_REGRESSION"
        if workload_passed is not None:
            if not workload_passed or workload_improvement_percent is None:
                return "REJECT_WORKLOAD"
            if workload_improvement_percent < -max_runtime_regression_percent:
                return "REJECT_WORKLOAD_RUNTIME_REGRESSION"
        return "ACCEPT"
    if optimization_objective != "runtime":
        raise ValueError(f"Unsupported optimization objective: {optimization_objective}")
    if require_significance and not significant:
        return "REJECT_NOT_SIGNIFICANT"
    if improvement_percent < minimum_percent:
        return "REJECT_PERFORMANCE"
    if workload_passed is not None:
        if not workload_passed or workload_improvement_percent is None:
            return "REJECT_WORKLOAD"
        if require_significance and not workload_significant:
            return "REJECT_WORKLOAD_NOT_SIGNIFICANT"
        workload_threshold = (
            minimum_percent
            if minimum_workload_percent is None
            else minimum_workload_percent
        )
        if workload_improvement_percent < workload_threshold:
            return "REJECT_WORKLOAD"
    return "ACCEPT"


def _git_value(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def _environment() -> dict[str, Any]:
    affinity = None
    if hasattr(os, "sched_getaffinity"):
        try:
            affinity = sorted(os.sched_getaffinity(0))
        except OSError:
            affinity = None
    try:
        cpu_frequency = psutil.cpu_freq()
    except (OSError, SystemError, PermissionError):
        cpu_frequency = None
    try:
        memory_total = psutil.virtual_memory().total
    except (OSError, SystemError, PermissionError):
        memory_total = None

    def read_optional(path: str) -> str | None:
        try:
            return Path(path).read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            return None

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": sys.version,
        "python_executable": sys.executable,
        "pyperf_version": pyperf.__version__,
        "psutil_version": psutil.__version__,
        "logical_cpu_count": os.cpu_count(),
        "cpu_affinity": affinity,
        "cpu_frequency_mhz": (
            {
                "current": cpu_frequency.current,
                "min": cpu_frequency.min,
                "max": cpu_frequency.max,
            }
            if cpu_frequency
            else None
        ),
        "memory_total_bytes": memory_total,
        "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
        "linux_scaling_governor": read_optional(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        ),
        "linux_no_turbo": read_optional(
            "/sys/devices/system/cpu/intel_pstate/no_turbo"
        ),
    }


def _usage_sum(usages: list[dict[str, int | None]]) -> dict[str, int]:
    keys = (
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cached_tokens",
        "reasoning_tokens",
    )
    return {key: sum(int(item.get(key) or 0) for item in usages) for key in keys}


def _estimated_cost_cny(usage: dict[str, int]) -> tuple[float | None, str]:
    names = {
        "input": "DEEPSEEK_INPUT_PRICE_CNY_PER_M",
        "cached": "DEEPSEEK_CACHED_INPUT_PRICE_CNY_PER_M",
        "output": "DEEPSEEK_OUTPUT_PRICE_CNY_PER_M",
    }
    try:
        input_price = float(os.environ[names["input"]])
        output_price = float(os.environ[names["output"]])
        cached_price = float(os.environ.get(names["cached"], input_price))
    except (KeyError, ValueError):
        return (
            None,
            "Set current DeepSeek CNY-per-million-token prices in the optional environment variables; token usage is preserved.",
        )
    cached = usage.get("cached_tokens", 0)
    uncached_input = max(0, usage.get("input_tokens", 0) - cached)
    cost = (
        uncached_input * input_price
        + cached * cached_price
        + usage.get("output_tokens", 0) * output_price
    ) / 1_000_000
    return cost, "Calculated from configured token prices; reasoning tokens are included in output tokens."


def _metric_value(
    resources: dict[str, Any] | None, key: str, default: str = "不可用"
) -> str:
    if not resources:
        return default
    if key == "tracemalloc_peak_bytes":
        value = resources.get(key)
    else:
        value = resources.get("command", {}).get("metrics", {}).get(key)
    return default if value is None else str(value)


def _render_report(summary: dict[str, Any], manifest: dict[str, Any]) -> str:
    human = summary.get("human_fix_comparison") or {}
    best = summary.get("best_deepseek_comparison") or {}
    human_memory = summary.get("human_fix_memory_comparison") or {}
    best_memory = summary.get("best_deepseek_memory_comparison") or {}
    human_workload = summary.get("human_fix_original_workload_comparison") or {}
    best_workload = summary.get("best_deepseek_original_workload_comparison") or {}
    task_classification = summary.get("task_classification") or {}
    profiler_routing = summary.get("profiler_routing") or {}
    profiler_evidence = summary.get("profiler_evidence") or {}
    classification = task_classification.get("classification") or {}
    target_discovery = manifest.get("target_discovery") or {}
    target_classification = target_discovery.get("task_classification") or {}
    target_routing = target_discovery.get("profiler_routing") or {}
    target_selection = target_discovery.get("selection") or {}
    mode = (
        "本机快速预跑"
        if (
            "--fast" in manifest["config"]["benchmark_command"]
            or manifest["config"].get("benchmark_fast_mode")
        )
        else "服务器正式测量"
    )
    lines = [
        f"# `{summary['task_id']}` 实验报告",
        "",
        f"- 模式：{mode}",
        f"- Baseline：`{manifest['resolved_commits']['baseline']}`",
        f"- Human Fix：`{manifest['resolved_commits']['human_fix']}`",
        f"- 模型：`{manifest['actual_model']}`",
        f"- Benchmark 来源：`{manifest['config'].get('benchmark_mode', 'fixed')}`",
        f"- 优化目标：`{manifest['config'].get('optimization_objective', 'runtime')}`",
        f"- 候选数：{summary['candidate_count']}",
        f"- 功能正确候选：{summary['functional_candidate_count']}（{summary['functional_success_rate']:.1%}）",
        f"- 被闭环接受候选：{summary['accepted_candidate_count']}（{summary['accepted_candidate_rate']:.1%}）",
        "",
    ]
    if target_discovery:
        lines.extend(
            [
                "## 自动入口目标选择",
                "",
                f"- 多规模分类：`{target_classification.get('task_type', 'unavailable')}`",
                "- 自动执行 profiler：`"
                + ", ".join(target_routing.get("executed_profilers", []))
                + "`",
                f"- 用于选择目标：`{target_selection.get('profiler', 'unavailable')}`",
                f"- 自动目标函数：`{target_selection.get('target_symbol', 'unavailable')}`",
                f"- 自动目标文件：`{target_selection.get('target_file', 'unavailable')}`",
                "- 该分类与路由发生在调用 DeepSeek 之前，并实际决定模型可修改的目标。",
                "",
            ]
        )
    lines.extend(
        [
        "## 优化阶段资源分类（观察模式）",
        "",
        f"- 分类：`{classification.get('task_type', 'unavailable')}`",
        f"- 证据强度：`{classification.get('confidence', 'unavailable')}`",
        f"- 样本来源：`{task_classification.get('sample_source', 'unavailable')}`",
        "- 当前分类用于生成 profiler 采集计划，但不改变补丁生成或接受/拒绝决策。",
        "",
        "## 优化阶段 Profiler 补充证据",
        "",
        "- 选择：`"
        + ", ".join(
            item.get("name", "unknown")
            for item in profiler_routing.get("selected_profilers", [])
        )
        + "`",
        f"- 原因：{profiler_routing.get('reason', 'unavailable')}",
        f"- 执行状态：`{profiler_evidence.get('status', 'unavailable')}`",
        "- 已执行：`"
        + ", ".join(
            item.get("name", "unknown")
            for item in profiler_evidence.get("executed", [])
        )
        + "`",
        "- 专项证据可进入模型上下文，但仍不改变接受/拒绝规则。",
        "",
        "## 运行时间结果",
        "",
        "| 对象 | 相对 Baseline 加速 | 显著 |",
        "|---|---:|---:|",
        f"| 官方 Human Fix | {human.get('speedup_percent', 0):.2f}% | {human.get('significant')} |",
        f"| 最佳 DeepSeek Run | {best.get('speedup_percent', 0):.2f}% | {best.get('significant')} |",
        "",
        "## 内存结果",
        "",
        "| 对象 | tracemalloc 峰值下降 | Baseline(bytes) | Candidate(bytes) |",
        "|---|---:|---:|---:|",
        f"| 官方 Human Fix | {human_memory.get('reduction_percent', 0):.2f}% | {human_memory.get('baseline_bytes', '不可用')} | {human_memory.get('candidate_bytes', '不可用')} |",
        f"| 最佳 DeepSeek Run | {best_memory.get('reduction_percent', 0):.2f}% | {best_memory.get('baseline_bytes', '不可用')} | {best_memory.get('candidate_bytes', '不可用')} |",
        "",
        "## 原始 workload 端到端结果",
        "",
        "| 对象 | 相对 Baseline 加速 | 显著 |",
        "|---|---:|---:|",
        f"| 官方 Human Fix | {human_workload.get('speedup_percent', 0):.2f}% | {human_workload.get('significant')} |",
        f"| 最佳 DeepSeek Run | {best_workload.get('speedup_percent', 0):.2f}% | {best_workload.get('significant')} |",
        "",
        (
            "内存任务要求功能正确、峰值内存达到最低下降幅度，并且目标 benchmark 与原始 workload 的运行时间不超过退化护栏。"
            if manifest["config"].get("optimization_objective") == "memory"
            else "候选必须同时满足功能正确、目标函数 benchmark 提升和原始 workload 提升，才会被接受。"
        ),
        "",
        "## CPU、内存与 I/O（独立展示）",
        "",
        "| 版本 | User CPU(s) | System CPU(s) | Peak RSS(bytes) | tracemalloc peak(bytes) | Read(bytes) | Write(bytes) |",
        "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for label, resources in (
        ("Baseline", summary.get("baseline_resources")),
        ("Human Fix", summary.get("human_fix_resources")),
    ):
        lines.append(
            "| "
            + " | ".join(
                [
                    label,
                    _metric_value(resources, "user_cpu_seconds"),
                    _metric_value(resources, "system_cpu_seconds"),
                    _metric_value(resources, "peak_rss_bytes"),
                    _metric_value(resources, "tracemalloc_peak_bytes"),
                    _metric_value(resources, "read_bytes"),
                    _metric_value(resources, "write_bytes"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "各类资源指标分开记录；未被配置为优化目标的指标不直接参与接受决策。",
            "",
            "## 三个独立 Run",
            "",
            "| Run | 轮数 | 接受轮次 | 最佳加速 | 内存下降 | 模型调用 | Tokens |",
            "|---:|---:|---|---:|---:|---:|---:|",
        ]
    )
    for index, run in enumerate(summary["run_summaries"], 1):
        lines.append(
            f"| {index} | {run['iterations_run']} | {run['accepted_iterations']} | "
            f"{run['overall_comparison']['speedup_percent']:.2f}% | "
            f"{(run.get('overall_memory_comparison') or {}).get('reduction_percent', 0):.2f}% | "
            f"{run['model_calls']} | {run['usage']['total_tokens']} |"
        )
    lines.extend(
        [
            "",
            "## 成本与解释边界",
            "",
            f"- 总模型调用：{summary['model_calls']}",
            f"- 总 Tokens：{summary['usage']['total_tokens']}",
            f"- 估算费用（人民币）：{summary['estimated_cost_cny']}",
            f"- 费用说明：{summary['estimated_cost_note']}",
            "- `--fast` 结果只用于验证框架，不用于正式性能结论。",
            "- 具体候选及拒绝原因见 `candidates.csv` 和各轮 `evaluation.json`。",
            "",
        ]
    )
    return "\n".join(lines)


class OptimizationFramework:
    def __init__(
        self,
        project_root: Path,
        config: FrameworkConfig,
        agents: FrameworkAgents,
        evaluator: Evaluator,
        model_name: str,
    ) -> None:
        self.project_root = project_root
        self.config = config
        self.agents = agents
        self.evaluator = evaluator
        self.model_name = model_name
        self.repositories = RepositoryManager(config)
        self.generated_benchmark_path: Path | None = None
        self.generated_benchmark_sha256: str | None = None
        self.benchmark_usages: list[dict[str, int | None]] = []
        self.benchmark_summary: dict[str, Any] | None = None
        self.hotspot_summary: dict[str, Any] | None = None
        self.profiler_evidence: dict[str, Any] | None = None

    def _discover_target(self, experiment_dir: Path) -> None:
        settings = self.config.hotspot_discovery
        if settings is None:
            raise RuntimeError("Automatic target mode has no hotspot configuration")

        if settings.classification_command is not None:
            self._discover_target_with_routed_profiler(experiment_dir)
            return

        destination = experiment_dir / "target_discovery"
        workspace = destination / "workspace"
        sandbox_output = destination / "sandbox_output"
        destination.mkdir(parents=True, exist_ok=True)
        resolved = self.repositories.checkout(workspace, self.config.baseline_commit)
        limits = SandboxLimits(
            cpus=settings.cpus,
            memory=settings.memory,
            pids=settings.pids,
            timeout_seconds=settings.timeout_seconds,
            max_output_bytes=settings.max_output_bytes,
        )
        LOGGER.info("[Target Discovery] profile workload in Docker sandbox")
        result = run_in_docker(
            image=settings.image,
            workspace=workspace,
            harness=settings.harness,
            output=sandbox_output,
            inner_command=list(settings.command),
            limits=limits,
        )
        write_json(destination / "sandbox.json", result.to_dict())
        (destination / "stdout.txt").write_text(result.stdout, encoding="utf-8")
        (destination / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        if result.timed_out:
            raise RuntimeError("Automatic target discovery timed out")
        if result.return_code != 0:
            raise RuntimeError(
                "Automatic target discovery failed with exit code "
                f"{result.return_code}; see {destination / 'stderr.txt'}"
            )
        produced = sandbox_output / "profile.prof"
        if not produced.is_file():
            raise RuntimeError("Target discovery did not produce profile.prof")
        profile_path = destination / "profile.prof"
        shutil.copy2(produced, profile_path)
        report = parse_cprofile(
            profile_path,
            workspace,
            limit=settings.limit,
            recorded_repository=Path("/workspace"),
        )
        target_file, target_symbol = select_top_hotspot(
            report,
            expected_symbol=settings.validation_expected_symbol,
        )
        if not (workspace / target_file).is_file():
            raise RuntimeError(f"Selected hotspot file does not exist: {target_file}")
        report["baseline_commit"] = resolved
        report["selection"] = {
            "strategy": "top_self_time",
            "target_file": str(target_file),
            "target_symbol": target_symbol,
            "validation_expected_symbol": settings.validation_expected_symbol,
            "expected_symbol_used_for_selection": False,
        }
        write_json(destination / "hotspots.json", report)
        self.hotspot_summary = report
        self.config = replace(
            self.config,
            target_file=target_file,
            target_symbol=target_symbol,
            editable_files=(target_file,),
        )
        self.repositories = RepositoryManager(self.config)
        shutil.rmtree(workspace)
        LOGGER.info("[Target Discovery] selected %s", target_symbol)

    def _discover_target_with_routed_profiler(self, experiment_dir: Path) -> None:
        """Classify a workload before selecting and executing its profiler."""

        settings = self.config.hotspot_discovery
        callback = self.config.profiler_callback
        if settings is None or settings.classification_command is None:
            raise RuntimeError("Routed target discovery is not configured")
        if callback is None:
            raise RuntimeError("Routed target discovery requires profiler_callback")

        destination = experiment_dir / "target_discovery"
        workspace = destination / "workspace"
        samples_dir = destination / "classification_samples"
        profiler_dir = destination / "routed_profiler"
        destination.mkdir(parents=True, exist_ok=True)
        samples_dir.mkdir(parents=True, exist_ok=True)
        profiler_dir.mkdir(parents=True, exist_ok=True)
        resolved = self.repositories.checkout(workspace, self.config.baseline_commit)

        samples: list[PerformanceSample] = []
        sample_payloads: list[dict[str, Any]] = []
        LOGGER.info("[Target Discovery] classify workload from multiple input sizes")
        for size in settings.classification_sizes:
            result_path = samples_dir / f"size_{size}.json"
            command = tuple(
                value.replace("{size}", str(size))
                for value in settings.classification_command
            )
            result = self.evaluator.resource_test(workspace, command, result_path)
            payload = result.to_dict()
            payload["classification_size"] = size
            sample_payloads.append(payload)
            write_json(samples_dir / f"size_{size}_result.json", payload)
            if not result.passed:
                raise RuntimeError(
                    f"Workload classification sample {size} failed: "
                    f"{result.command_result.stderr}"
                )
            samples.append(PerformanceSample.from_mapping(payload))

        classification = classify_performance_task(samples).to_dict()
        classification_payload = {
            "status": "COMPLETE",
            "sample_source": "pre_target_workload_scaling",
            "classification": classification,
            "samples": sample_payloads,
        }
        write_json(destination / "task_classification.json", classification_payload)
        routing = route_from_task_classification(classification_payload)
        write_json(destination / "profiler_routing.json", routing)
        selected = {
            str(item.get("name"))
            for item in routing.get("selected_profilers", [])
            if isinstance(item, dict)
        }
        location_profilers = selected & {"cprofile", "tracemalloc"}
        if not location_profilers:
            raise RuntimeError(
                "Automatic classification did not select a location-aware profiler"
            )

        command = [
            self.config.targeted_test_command[0],
            str(self.project_root / "scripts" / "run_profile_callback.py"),
            "--module",
            str(callback.module),
            "--metadata-output",
            str(profiler_dir / "callback.json"),
            "--frames",
            str(callback.frames),
        ]
        cpu_profile = profiler_dir / "cpu.prof"
        memory_snapshot = profiler_dir / "memory.snapshot"
        if "cprofile" in location_profilers:
            command.extend(["--cprofile-output", str(cpu_profile)])
        if "tracemalloc" in location_profilers:
            command.extend(["--tracemalloc-output", str(memory_snapshot)])

        LOGGER.info(
            "[Target Discovery] execute routed profiler(s): %s",
            ", ".join(sorted(location_profilers)),
        )
        result = self.evaluator.run(command, workspace, profiler_dir)
        write_json(profiler_dir / "command.json", result.to_dict())
        if not result.passed:
            raise RuntimeError("Routed profiler callback failed: " + result.stderr)

        recorded_root = (
            Path("/workspace")
            if self.evaluator.docker_image is not None
            else workspace
        )
        reports: dict[str, dict[str, Any]] = {}
        if "cprofile" in location_profilers:
            reports["cprofile"] = parse_cprofile(
                cpu_profile,
                workspace,
                limit=callback.limit,
                recorded_repository=recorded_root,
            )
        if "tracemalloc" in location_profilers:
            reports["tracemalloc"] = parse_tracemalloc_snapshot(
                memory_snapshot,
                workspace,
                limit=callback.limit,
                recorded_repository=recorded_root,
            )
        for name, profiler_report in reports.items():
            write_json(profiler_dir / f"{name}.json", profiler_report)

        selector, reason = select_target_profiler(
            classification,
            reports,
            optimization_objective=self.config.optimization_objective,
        )
        routing["execution_applied"] = True
        routing["optimization_decision_impact"] = True
        routing["executed_profilers"] = sorted(location_profilers)
        routing["target_selection_profiler"] = selector
        routing["mode"] = "target_selection"
        write_json(destination / "profiler_routing.json", routing)
        report = reports[selector]
        target_file, target_symbol = select_top_hotspot(
            report,
            expected_symbol=settings.validation_expected_symbol,
        )
        if not (workspace / target_file).is_file():
            raise RuntimeError(f"Selected hotspot file does not exist: {target_file}")
        report["baseline_commit"] = resolved
        report["task_classification"] = classification
        report["profiler_routing"] = routing
        report["selection"] = {
            "strategy": "routed_profiler_top_1",
            "profiler": selector,
            "reason": reason,
            "target_file": str(target_file),
            "target_symbol": target_symbol,
            "validation_expected_symbol": settings.validation_expected_symbol,
            "expected_symbol_used_for_selection": False,
        }
        write_json(destination / "hotspots.json", report)
        self.hotspot_summary = report
        self.config = replace(
            self.config,
            target_file=target_file,
            target_symbol=target_symbol,
            editable_files=(target_file,),
        )
        self.repositories = RepositoryManager(self.config)
        shutil.rmtree(workspace)
        LOGGER.info("[Target Discovery] selected %s via %s", target_symbol, selector)

    @staticmethod
    def _write_agent_trace(destination: Path, prefix: str, output: Any) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        (destination / f"{prefix}_system_prompt.txt").write_text(
            output.system_prompt, encoding="utf-8"
        )
        (destination / f"{prefix}_prompt.txt").write_text(
            output.prompt, encoding="utf-8"
        )
        (destination / f"{prefix}_response.txt").write_text(
            output.content, encoding="utf-8"
        )
        write_json(
            destination / f"{prefix}_usage.json",
            {"actual_model": output.actual_model, "usage": output.usage},
        )

    def _functional_gate(
        self,
        workspace: Path,
        destination: Path,
        protected_hashes: dict[str, str],
    ) -> tuple[bool, dict[str, Any]]:
        destination.mkdir(parents=True, exist_ok=True)
        if self.config.target_file is None or not self.config.target_symbol:
            raise RuntimeError("Optimization target has not been resolved")
        python = self.config.targeted_test_command[0]
        stages: dict[str, Any] = {}
        commands: list[tuple[str, tuple[str, ...]]] = [
            (
                "syntax",
                (
                    python,
                    "-c",
                    "import pathlib,sys; p=pathlib.Path(sys.argv[1]); "
                    "compile(p.read_text(encoding='utf-8'), str(p), 'exec')",
                    str(self.config.target_file),
                ),
            ),
        ]
        if "." in self.config.target_symbol:
            module = module_name_from_path(self.config.target_file)
            prefix = module + "."
            attribute_path = (
                self.config.target_symbol[len(prefix) :]
                if self.config.target_symbol.startswith(prefix)
                else self.config.target_symbol.rsplit(".", 1)[-1]
            )
            import_check = (
                "import functools,importlib; "
                f"obj=importlib.import_module({module!r}); "
                f"functools.reduce(getattr, {attribute_path!r}.split('.'), obj)"
            )
            commands.append(
                ("import", (python, "-c", import_check))
            )
        commands.extend(
            [
                ("targeted_tests", self.config.targeted_test_command),
                ("full_tests", self.config.full_test_command),
            ]
        )
        if self.config.invariant_test_command:
            commands.append(("invariants_and_target_hit", self.config.invariant_test_command))

        passed = True
        for name, command in commands:
            if not passed:
                stages[name] = {"skipped": True}
                continue
            result = self.evaluator.functional_test(
                workspace, command, destination / f"{name}_sandbox"
            )
            stages[name] = result.to_dict()
            write_json(destination / f"{name}.json", result.to_dict())
            passed = result.passed
        try:
            assert_hashes_unchanged(workspace, protected_hashes)
            stages["protected_files"] = {"passed": True}
        except Exception as exc:
            stages["protected_files"] = {"passed": False, "error": str(exc)}
            passed = False
        write_json(destination / "summary.json", {"passed": passed, "stages": stages})
        return passed, stages

    def _contexts(self, workspace: Path) -> tuple[str, str]:
        if self.config.target_file is None or not self.config.target_symbol:
            raise RuntimeError("Optimization target has not been resolved")
        source = (workspace / self.config.target_file).read_text(encoding="utf-8")
        source_context = extract_symbol_context(source, self.config.target_symbol)
        needle = self.config.target_symbol.rsplit(".", 1)[-1]
        excerpts: list[str] = []
        for relative in self.config.context_files:
            text = (workspace / relative).read_text(encoding="utf-8")
            excerpt = extract_matching_context(text, needle)
            if excerpt:
                excerpts.append(f"# {relative}\n{excerpt}")
        if self.hotspot_summary:
            selection = self.hotspot_summary.get("selection") or {}
            profiler_context = {
                "ranking_metric": self.hotspot_summary.get("ranking_metric"),
                "total_profiled_self_time_seconds": self.hotspot_summary.get(
                    "total_profiled_self_time_seconds"
                ),
                "hotspots": self.hotspot_summary.get("hotspots", []),
                # The model needs the selected target, but the controlled
                # experiment's expected answer is validation-only evidence.
                "selection": {
                    "strategy": selection.get("strategy"),
                    "target_file": selection.get("target_file"),
                    "target_symbol": selection.get("target_symbol"),
                },
            }
            excerpts.append(
                "# Profiler evidence (read-only)\n"
                + json.dumps(profiler_context, ensure_ascii=False, indent=2)
            )
        if self.profiler_evidence:
            model_context = self.profiler_evidence.get("model_context") or {}
            excerpts.append(
                "# Routed profiler evidence (read-only)\n"
                + json.dumps(model_context, ensure_ascii=False, indent=2)
            )
        return source_context, "\n\n".join(excerpts)

    def _collect_profiler_evidence(
        self,
        experiment_dir: Path,
        workspace: Path,
        routing: dict[str, Any],
        baseline_resources: ResourceResult | None,
        baseline_workload: PerformanceResult | None,
    ) -> dict[str, Any]:
        """Execute the observation route where a safe callback is available."""

        destination = experiment_dir / "profiler_observation"
        destination.mkdir(parents=True, exist_ok=True)
        selections = {
            str(item.get("name"))
            for item in routing.get("selected_profilers", [])
            if isinstance(item, dict)
        }
        evidence: dict[str, Any] = {
            "status": "UNAVAILABLE" if not selections else "COMPLETE",
            "mode": "observe_only",
            "selected_profilers": sorted(selections),
            "executed": [],
            "skipped": [],
            "execution_applied": False,
            "optimization_decision_impact": False,
            "reports": {},
        }

        # Reuse target-discovery evidence only under its actual profiler name.
        # Routed discovery may have selected a tracemalloc report, so treating
        # every hotspot summary as cProfile would silently mislabel evidence.
        needs_callback = set(selections)
        profile_format = (
            str(self.hotspot_summary.get("profile_format"))
            if self.hotspot_summary
            else ""
        )
        reusable_profiler = {
            "cProfile": "cprofile",
            "tracemalloc_snapshot": "tracemalloc",
        }.get(profile_format)
        if reusable_profiler in needs_callback and self.hotspot_summary:
            evidence["reports"][reusable_profiler] = self.hotspot_summary
            evidence["executed"].append(
                {"name": reusable_profiler, "source": "target_discovery_reuse"}
            )
            needs_callback.remove(reusable_profiler)

        # Existing baseline measurement is sufficient for process-level totals,
        # though it does not identify a file or call site.
        if "process_io" in needs_callback and self.config.profiler_callback is None:
            source_result: PerformanceResult | ResourceResult | None = (
                baseline_workload
                if baseline_workload is not None and baseline_workload.passed
                else baseline_resources
            )
            if source_result is not None and source_result.passed:
                evidence["reports"]["process_io"] = (
                    source_result.command_result.metrics.to_dict()
                )
                evidence["executed"].append(
                    {"name": "process_io", "source": "baseline_metrics_reuse"}
                )
                needs_callback.remove("process_io")

        callback = self.config.profiler_callback
        if needs_callback and callback is None:
            for name in sorted(needs_callback):
                evidence["skipped"].append(
                    {"name": name, "reason": "profiler_callback is not configured"}
                )
        elif needs_callback and callback is not None:
            command = [
                self.config.targeted_test_command[0],
                str(self.project_root / "scripts" / "run_profile_callback.py"),
                "--module",
                str(callback.module),
                "--metadata-output",
                str(destination / "callback.json"),
                "--frames",
                str(callback.frames),
            ]
            cpu_profile = destination / "cpu.prof"
            memory_snapshot = destination / "memory.snapshot"
            if "cprofile" in needs_callback:
                command.extend(["--cprofile-output", str(cpu_profile)])
            if "tracemalloc" in needs_callback:
                command.extend(["--tracemalloc-output", str(memory_snapshot)])
            if "process_io" in needs_callback:
                command.append("--resource-only")

            result = self.evaluator.run(command, workspace, destination)
            write_json(destination / "command.json", result.to_dict())
            if not result.passed:
                for name in sorted(needs_callback):
                    evidence["skipped"].append(
                        {"name": name, "reason": "profile callback execution failed"}
                    )
                evidence["callback_error"] = result.stderr
            else:
                recorded_root = (
                    Path("/workspace")
                    if self.evaluator.docker_image is not None
                    else workspace
                )
                if "cprofile" in needs_callback:
                    report = parse_cprofile(
                        cpu_profile,
                        workspace,
                        limit=callback.limit,
                        recorded_repository=recorded_root,
                    )
                    evidence["reports"]["cprofile"] = report
                    evidence["executed"].append(
                        {"name": "cprofile", "source": "profile_callback"}
                    )
                if "tracemalloc" in needs_callback:
                    report = parse_tracemalloc_snapshot(
                        memory_snapshot,
                        workspace,
                        limit=callback.limit,
                        recorded_repository=recorded_root,
                    )
                    evidence["reports"]["tracemalloc"] = report
                    evidence["executed"].append(
                        {"name": "tracemalloc", "source": "profile_callback"}
                    )
                if "process_io" in needs_callback:
                    evidence["reports"]["process_io"] = result.metrics.to_dict()
                    evidence["executed"].append(
                        {"name": "process_io", "source": "profile_callback"}
                    )
                metadata_path = destination / "callback.json"
                if metadata_path.is_file():
                    evidence["callback"] = json.loads(
                        metadata_path.read_text(encoding="utf-8")
                    )

        evidence["execution_applied"] = bool(evidence["executed"])
        if evidence["skipped"] and evidence["executed"]:
            evidence["status"] = "PARTIAL"
        elif evidence["skipped"]:
            evidence["status"] = "SKIPPED"
        model_reports = dict(evidence["reports"])
        cpu_report = model_reports.get("cprofile")
        if isinstance(cpu_report, dict):
            selection = cpu_report.get("selection") or {}
            model_reports["cprofile"] = {
                "ranking_metric": cpu_report.get("ranking_metric"),
                "total_profiled_self_time_seconds": cpu_report.get(
                    "total_profiled_self_time_seconds"
                ),
                "hotspots": cpu_report.get("hotspots", []),
                "selection": {
                    "strategy": selection.get("strategy"),
                    "target_file": selection.get("target_file"),
                    "target_symbol": selection.get("target_symbol"),
                },
            }
        evidence["model_context"] = {
            "task_type": routing.get("task_type"),
            "reports": model_reports,
            "callback_measurement": evidence.get("callback"),
            "limitations": [
                "Profiler routing is observation-only.",
                "Process I/O totals do not identify a file or Python call site.",
                "A tracemalloc snapshot attributes allocations still alive at capture time; use the callback peak for temporary-allocation pressure.",
            ],
        }
        write_json(destination / "profiler_evidence.json", evidence)
        self.profiler_evidence = evidence
        return evidence

    def _prepare_generated_benchmark(
        self, experiment_dir: Path, workspace: Path
    ) -> None:
        generation_dir = experiment_dir / "benchmark_generation"
        source_context, tests_context = self._contexts(workspace)
        code = ""
        validation: GeneratedBenchmarkValidation | None = None
        for attempt in range(self.config.benchmark_generation_max_repairs + 1):
            attempt_dir = generation_dir / f"attempt_{attempt:02d}"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            LOGGER.info(
                "[Benchmark Generate] attempt %d / %d",
                attempt,
                self.config.benchmark_generation_max_repairs,
            )
            if attempt == 0:
                output, code = self.agents.generate_benchmark(
                    target_symbol=self.config.target_symbol,
                    source_context=source_context,
                    tests_context=tests_context,
                )
                prefix = "generation"
            else:
                assert validation is not None
                output, code = self.agents.repair_benchmark(
                    target_symbol=self.config.target_symbol,
                    source_context=source_context,
                    tests_context=tests_context,
                    benchmark_code=code,
                    failure=validation.failure_evidence(),
                )
                prefix = "repair"
            self.benchmark_usages.append(output.usage)
            self._write_agent_trace(attempt_dir, prefix, output)
            candidate_path = attempt_dir / "benchmark.py"
            candidate_path.write_text(code, encoding="utf-8")
            validation = validate_generated_benchmark(
                benchmark_path=candidate_path,
                result_path=attempt_dir / "pyperf.json",
                workspace=workspace,
                python=self.config.targeted_test_command[0],
                target_symbol=self.config.target_symbol,
                project_root=self.project_root,
                timeout_seconds=self.config.timeout_seconds,
                fast_mode=self.config.benchmark_fast_mode,
                command_runner=self.evaluator.run,
            )
            write_json(attempt_dir / "validation.json", validation.to_dict())
            LOGGER.info(
                "[Benchmark Validate:%s] %s",
                validation.stage,
                "PASS" if validation.passed else "FAIL",
            )
            if validation.passed:
                benchmark_dir = experiment_dir / "benchmark"
                benchmark_dir.mkdir(parents=True, exist_ok=True)
                frozen = benchmark_dir / "benchmark.py"
                frozen.write_text(code, encoding="utf-8")
                self.generated_benchmark_path = frozen
                self.generated_benchmark_sha256 = sha256_file(frozen)
                assert validation.primary_benchmark is not None
                self.evaluator.primary_benchmark = validation.primary_benchmark
                self.benchmark_summary = {
                    "mode": "generated",
                    "attempts": attempt + 1,
                    "repair_attempts": attempt,
                    "sha256": self.generated_benchmark_sha256,
                    "primary_benchmark": validation.primary_benchmark,
                    "workload": validation.workload,
                    "validation": validation.to_dict(),
                }
                write_json(benchmark_dir / "freeze.json", self.benchmark_summary)
                return
        assert validation is not None
        raise RuntimeError(
            "Generated benchmark did not pass validation: "
            + str(validation.failure_evidence())
        )

    def _benchmark_command(self) -> tuple[str, ...]:
        if self.config.benchmark_mode == "fixed":
            return self.config.benchmark_command
        if self.generated_benchmark_path is None:
            raise RuntimeError("Generated benchmark has not been prepared")
        command = [
            self.config.targeted_test_command[0],
            str(self.generated_benchmark_path),
        ]
        if self.config.benchmark_fast_mode:
            command.append("--fast")
        command.extend(["-o", "{output}"])
        return tuple(command)

    def _resource_command(self) -> tuple[str, ...] | None:
        if self.config.benchmark_mode == "fixed":
            return self.config.resource_command
        if self.generated_benchmark_path is None or not self.evaluator.primary_benchmark:
            return None
        return (
            self.config.targeted_test_command[0],
            str(self.project_root / "scripts" / "measure_generated_benchmark.py"),
            "--benchmark",
            str(self.generated_benchmark_path),
            "--primary",
            self.evaluator.primary_benchmark,
            "--output",
            "{output}",
        )

    def _measure_version(
        self, workspace: Path, destination: Path
    ) -> tuple[PerformanceResult, ResourceResult | None]:
        if self.generated_benchmark_path is not None:
            actual = sha256_file(self.generated_benchmark_path)
            if actual != self.generated_benchmark_sha256:
                raise RuntimeError("Frozen generated benchmark changed during the experiment")
        performance = self.evaluator.performance_test(
            workspace,
            self._benchmark_command(),
            destination / "pyperf.json",
        )
        write_json(destination / "performance.json", performance.to_dict())
        resources: ResourceResult | None = None
        resource_command = self._resource_command()
        if resource_command:
            resources = self.evaluator.resource_test(
                workspace,
                resource_command,
                destination / "resource_workload.json",
            )
            write_json(destination / "resources.json", resources.to_dict())
        return performance, resources

    def _measure_original_workload(
        self, workspace: Path, destination: Path
    ) -> PerformanceResult | None:
        command = self.config.original_workload_command
        if command is None:
            return None
        result = self.evaluator.performance_test(
            workspace,
            command,
            destination / "pyperf.json",
        )
        # The evaluator's default primary belongs to the target microbenchmark.
        # A configured original workload is an independent suite; when it has
        # one benchmark, record that benchmark as its own primary explicitly.
        if len(result.benchmarks) == 1:
            result = replace(
                result,
                primary_benchmark=next(iter(result.benchmarks)),
            )
        write_json(destination / "performance.json", result.to_dict())
        return result

    def _prepare_reference(
        self, experiment_dir: Path, name: str, ref: str | None
    ) -> tuple[
        Path,
        str,
        PerformanceResult,
        ResourceResult | None,
        PerformanceResult | None,
    ]:
        destination = experiment_dir / name
        workspace = destination / "workspace"
        resolved = self.repositories.checkout(workspace, ref)
        protected = file_hashes(workspace, self.config.context_files)
        passed, _ = self._functional_gate(workspace, destination / "tests", protected)
        if not passed:
            raise RuntimeError(f"{name} functional tests failed")
        if name == "baseline" and self.config.benchmark_mode == "generated":
            self._prepare_generated_benchmark(experiment_dir, workspace)
        performance, resources = self._measure_version(
            workspace, destination / "measurement"
        )
        if not performance.passed:
            raise RuntimeError(f"{name} benchmark failed")
        original_workload = self._measure_original_workload(
            workspace, destination / "original_workload"
        )
        if original_workload is not None and not original_workload.passed:
            raise RuntimeError(f"{name} original workload benchmark failed")
        write_json(
            destination / "version.json",
            {"requested_ref": ref, "resolved_commit": resolved},
        )
        return workspace, resolved, performance, resources, original_workload

    def _run_one(
        self,
        experiment_dir: Path,
        run_number: int,
        baseline_performance: PerformanceResult,
        baseline_resources: ResourceResult | None,
        baseline_workload: PerformanceResult | None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Path]:
        run_dir = experiment_dir / f"run_{run_number:02d}"
        workspace = run_dir / "workspace"
        resolved = self.repositories.checkout(workspace, self.config.baseline_commit)
        protected_hashes = file_hashes(workspace, self.config.context_files)
        current_performance = baseline_performance
        current_resources = baseline_resources
        current_workload = baseline_workload
        best_patch = ""
        memory: list[dict[str, Any]] = []
        rows: list[dict[str, Any]] = []
        usages: list[dict[str, int | None]] = []
        accepted_iterations: list[int] = []
        no_improvement_count = 0
        started = time.perf_counter()
        stop_reason = "MAX_ITERATIONS"

        for iteration in range(1, self.config.max_iterations + 1):
            iteration_dir = run_dir / f"iteration_{iteration:02d}"
            iteration_dir.mkdir(parents=True, exist_ok=True)
            source_context, tests_context = self._contexts(workspace)
            if self.generated_benchmark_path is not None:
                tests_context += (
                    "\n\n# Frozen generated benchmark (read-only)\n"
                    + self.generated_benchmark_path.read_text(encoding="utf-8")
                )
            baseline_context = _performance_summary(current_performance)
            baseline_context["optimization_objective"] = (
                self.config.optimization_objective
            )
            baseline_context["acceptance_thresholds"] = {
                "min_speedup_percent": self.config.min_speedup_percent,
                "min_memory_reduction_percent": (
                    self.config.min_memory_reduction_percent
                ),
                "max_runtime_regression_percent": (
                    self.config.max_runtime_regression_percent
                ),
            }
            if current_resources is not None:
                baseline_context["resource_measurement"] = (
                    current_resources.to_dict()
                )
            if current_workload is not None:
                baseline_context["original_workload"] = _performance_summary(
                    current_workload
                )

            LOGGER.info("[Run %d Iteration %d] analyze", run_number, iteration)
            analysis = self.agents.analyze(
                target_symbol=self.config.target_symbol,
                target_file=str(self.config.target_file),
                source_context=source_context,
                tests_context=tests_context,
                baseline=baseline_context,
                memory=memory[-2:],
            )
            usages.append(analysis.usage)
            self._write_agent_trace(iteration_dir, "analysis", analysis)
            (iteration_dir / "diagnosis.txt").write_text(
                analysis.content, encoding="utf-8"
            )
            write_json(
                iteration_dir / "analysis_usage.json",
                {"actual_model": analysis.actual_model, "usage": analysis.usage},
            )

            functional_passed = False
            candidate_performance: PerformanceResult | None = None
            candidate_resources: ResourceResult | None = None
            comparison: PerformanceComparison | None = None
            memory_comparison: MemoryComparison | None = None
            candidate_workload: PerformanceResult | None = None
            workload_comparison: PerformanceComparison | None = None
            patch_error: str | None = None
            patch = ""
            stats: dict[str, int] | None = None
            try:
                LOGGER.info("[Run %d Iteration %d] generate patch", run_number, iteration)
                patch_output, patch = self.agents.generate_patch(
                    target_symbol=self.config.target_symbol,
                    target_file=str(self.config.target_file),
                    source_context=source_context,
                    tests_context=tests_context,
                    diagnosis=analysis.content,
                    memory=memory[-2:],
                )
                usages.append(patch_output.usage)
                self._write_agent_trace(iteration_dir, "patch", patch_output)
                raw_patch = patch
                patch = canonicalize_hunk_locations(
                    workspace, raw_patch, self.config.editable_files
                )
                (iteration_dir / "patch_response.txt").write_text(
                    patch_output.content, encoding="utf-8"
                )
                (iteration_dir / "candidate.raw.patch").write_text(
                    raw_patch, encoding="utf-8"
                )
                (iteration_dir / "candidate.patch").write_text(patch, encoding="utf-8")
                write_json(
                    iteration_dir / "patch_usage.json",
                    {
                        "actual_model": patch_output.actual_model,
                        "usage": patch_output.usage,
                    },
                )
                stats = patch_stats(patch).to_dict()
                apply_safe_patch(workspace, patch, self.config.editable_files)
                functional_passed, _ = self._functional_gate(
                    workspace, iteration_dir / "tests", protected_hashes
                )
                if functional_passed:
                    candidate_performance, candidate_resources = self._measure_version(
                        workspace, iteration_dir / "measurement"
                    )
                    if candidate_performance.passed:
                        comparison = compare_performance(
                            current_performance, candidate_performance
                        )
                        if (
                            current_resources is not None
                            and current_resources.passed
                            and candidate_resources is not None
                            and candidate_resources.passed
                        ):
                            memory_comparison = compare_memory(
                                current_resources, candidate_resources
                            )
                        candidate_workload = self._measure_original_workload(
                            workspace, iteration_dir / "original_workload"
                        )
                        if (
                            current_workload is not None
                            and candidate_workload is not None
                            and candidate_workload.passed
                        ):
                            workload_comparison = compare_performance(
                                current_workload, candidate_workload
                            )
            except Exception as exc:
                patch_error = f"{type(exc).__name__}: {exc}"
                (iteration_dir / "patch_error.txt").write_text(
                    patch_error + "\n", encoding="utf-8"
                )

            decision = decide_candidate(
                functional_passed,
                bool(candidate_performance and candidate_performance.passed),
                comparison.speedup_percent if comparison else None,
                self.config.min_speedup_percent,
                significant=comparison.significant if comparison else False,
                require_significance=self.config.require_significance,
                workload_passed=(
                    bool(candidate_workload and candidate_workload.passed)
                    if current_workload is not None
                    else None
                ),
                workload_improvement_percent=(
                    workload_comparison.speedup_percent
                    if workload_comparison
                    else None
                ),
                minimum_workload_percent=self.config.min_workload_speedup_percent,
                workload_significant=(
                    workload_comparison.significant
                    if workload_comparison
                    else False
                ),
                optimization_objective=self.config.optimization_objective,
                memory_passed=(
                    bool(candidate_resources and candidate_resources.passed)
                    if self.config.optimization_objective == "memory"
                    else None
                ),
                memory_reduction_percent=(
                    memory_comparison.reduction_percent
                    if memory_comparison
                    else None
                ),
                minimum_memory_reduction_percent=(
                    self.config.min_memory_reduction_percent
                ),
                max_runtime_regression_percent=(
                    self.config.max_runtime_regression_percent
                ),
            )
            evaluation = {
                "run": run_number,
                "iteration": iteration,
                "decision": decision,
                "functional_passed": functional_passed,
                "comparison_vs_current_best": comparison.to_dict() if comparison else None,
                "memory_comparison_vs_current_best": (
                    memory_comparison.to_dict() if memory_comparison else None
                ),
                "original_workload_comparison_vs_current_best": (
                    workload_comparison.to_dict() if workload_comparison else None
                ),
                "minimum_speedup_percent": self.config.min_speedup_percent,
                "minimum_workload_speedup_percent": (
                    self.config.min_workload_speedup_percent
                ),
                "optimization_objective": self.config.optimization_objective,
                "minimum_memory_reduction_percent": (
                    self.config.min_memory_reduction_percent
                ),
                "max_runtime_regression_percent": (
                    self.config.max_runtime_regression_percent
                ),
                "require_significance": self.config.require_significance,
                "patch_error": patch_error,
                "patch_stats": stats,
                "candidate_performance": (
                    candidate_performance.to_dict() if candidate_performance else None
                ),
                "candidate_resources": (
                    candidate_resources.to_dict() if candidate_resources else None
                ),
                "candidate_original_workload": (
                    candidate_workload.to_dict() if candidate_workload else None
                ),
            }
            write_json(iteration_dir / "evaluation.json", evaluation)

            if decision == "ACCEPT":
                best_patch = repository_diff(workspace)
                current_performance = candidate_performance  # type: ignore[assignment]
                if candidate_resources is not None:
                    current_resources = candidate_resources
                if candidate_workload is not None:
                    current_workload = candidate_workload
                accepted_iterations.append(iteration)
                no_improvement_count = 0
            else:
                restore_patch(workspace, best_patch)
                no_improvement_count += 1

            LOGGER.info("[Run %d Iteration %d] reflect", run_number, iteration)
            reflection = self.agents.reflect(
                target_symbol=self.config.target_symbol,
                diagnosis=analysis.content,
                evaluation=evaluation,
            )
            usages.append(reflection.usage)
            self._write_agent_trace(iteration_dir, "reflection", reflection)
            (iteration_dir / "reflection.txt").write_text(
                reflection.content, encoding="utf-8"
            )
            write_json(
                iteration_dir / "reflection_usage.json",
                {"actual_model": reflection.actual_model, "usage": reflection.usage},
            )
            memory.append(
                {
                    "iteration": iteration,
                    "decision": decision,
                    "comparison": comparison.to_dict() if comparison else None,
                    "memory_comparison": (
                        memory_comparison.to_dict() if memory_comparison else None
                    ),
                    "original_workload_comparison": (
                        workload_comparison.to_dict()
                        if workload_comparison
                        else None
                    ),
                    "patch_error": patch_error,
                    "lesson": reflection.content,
                }
            )
            row = {
                "run": run_number,
                "iteration": iteration,
                "decision": decision,
                "functional_passed": functional_passed,
                "speedup_percent": comparison.speedup_percent if comparison else None,
                "memory_reduction_percent": (
                    memory_comparison.reduction_percent
                    if memory_comparison
                    else None
                ),
                "significant": comparison.significant if comparison else None,
                "workload_speedup_percent": (
                    workload_comparison.speedup_percent
                    if workload_comparison
                    else None
                ),
                "workload_significant": (
                    workload_comparison.significant
                    if workload_comparison
                    else None
                ),
                "workload_median_seconds": (
                    candidate_workload.median_seconds
                    if candidate_workload
                    else None
                ),
                "median_seconds": (
                    candidate_performance.median_seconds
                    if candidate_performance
                    else None
                ),
                "robust_rsd_percent": (
                    candidate_performance.robust_rsd_percent
                    if candidate_performance
                    else None
                ),
                "peak_rss_bytes": (
                    candidate_resources.command_result.metrics.peak_rss_bytes
                    if candidate_resources
                    else None
                ),
                "tracemalloc_peak_bytes": (
                    candidate_resources.tracemalloc_peak_bytes
                    if candidate_resources
                    else None
                ),
                "read_bytes": (
                    candidate_resources.command_result.metrics.read_bytes
                    if candidate_resources
                    else None
                ),
                "write_bytes": (
                    candidate_resources.command_result.metrics.write_bytes
                    if candidate_resources
                    else None
                ),
                "lines_added": stats["lines_added"] if stats else None,
                "lines_deleted": stats["lines_deleted"] if stats else None,
                "patch_error": patch_error,
            }
            rows.append(row)

            if no_improvement_count >= self.config.no_improvement_limit:
                stop_reason = "NO_IMPROVEMENT_LIMIT"
                break

        final_dir = run_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        (final_dir / "best.patch").write_text(best_patch, encoding="utf-8")
        final_performance, final_resources = self._measure_version(
            workspace, final_dir / "measurement"
        )
        final_workload = self._measure_original_workload(
            workspace, final_dir / "original_workload"
        )
        if best_patch:
            overall = compare_performance(baseline_performance, current_performance)
        else:
            primary = baseline_performance.primary
            assert primary is not None
            overall = PerformanceComparison(
                benchmark=primary.name,
                speedup_percent=0.0,
                baseline_median_seconds=primary.median_seconds,
                candidate_median_seconds=primary.median_seconds,
                significant=False,
                t_score=None,
            )
        overall_memory = (
            compare_memory(baseline_resources, current_resources)
            if baseline_resources is not None
            and baseline_resources.passed
            and current_resources is not None
            and current_resources.passed
            else None
        )
        summary = {
            "status": "COMPLETE",
            "run": run_number,
            "baseline_commit": resolved,
            "stop_reason": stop_reason,
            "iterations_run": len(memory),
            "accepted_iterations": accepted_iterations,
            "overall_comparison": overall.to_dict(),
            "overall_memory_comparison": (
                overall_memory.to_dict() if overall_memory else None
            ),
            "optimization_objective": getattr(
                self.config, "optimization_objective", "runtime"
            ),
            "best_patch_changed_source": bool(best_patch),
            "final_resources": final_resources.to_dict() if final_resources else None,
            "final_retest": final_performance.to_dict(),
            "final_original_workload": (
                final_workload.to_dict() if final_workload else None
            ),
            "overall_original_workload_comparison": (
                compare_performance(baseline_workload, current_workload).to_dict()
                if baseline_workload is not None and current_workload is not None
                else None
            ),
            "usage": _usage_sum(usages),
            "model_calls": len(usages),
            "elapsed_seconds": time.perf_counter() - started,
        }
        write_json(final_dir / "summary.json", summary)
        return summary, rows, workspace

    @staticmethod
    def _remove_experiment_workspaces(experiment_dir: Path) -> dict[str, Any]:
        candidates = [
            experiment_dir / "baseline" / "workspace",
            experiment_dir / "human_fix" / "workspace",
            *(path / "workspace" for path in sorted(experiment_dir.glob("run_[0-9][0-9]"))),
        ]
        removed: list[str] = []
        root = experiment_dir.resolve()
        for workspace in candidates:
            if not workspace.exists():
                continue
            resolved = workspace.resolve()
            if not resolved.is_relative_to(root) or workspace.name != "workspace":
                raise RuntimeError(f"Unsafe workspace cleanup target: {workspace}")
            shutil.rmtree(workspace)
            removed.append(str(workspace.relative_to(experiment_dir)))
        return {"policy": "remove", "removed": removed}

    def _write_release_candidate(
        self,
        experiment_dir: Path,
        best_run: dict[str, Any],
        baseline_commit: str,
    ) -> dict[str, Any]:
        destination = experiment_dir / "release_candidate"
        destination.mkdir(parents=True, exist_ok=True)
        run_number = int(best_run["run"])
        source_patch = experiment_dir / f"run_{run_number:02d}" / "final" / "best.patch"
        patch = source_patch.read_text(encoding="utf-8")
        patch_path = destination / "best.patch"
        patch_path.write_text(patch, encoding="utf-8")
        status = "READY_FOR_REVIEW" if patch.strip() else "NO_ACCEPTED_PATCH"
        manifest = {
            "status": status,
            "run": run_number,
            "baseline_commit": baseline_commit,
            "target_file": str(self.config.target_file),
            "target_symbol": self.config.target_symbol,
            "patch": "best.patch",
            "patch_sha256": sha256_file(patch_path),
            "accepted_iterations": best_run["accepted_iterations"],
            "optimization_objective": getattr(
                self.config, "optimization_objective", "runtime"
            ),
            "microbenchmark_comparison": best_run["overall_comparison"],
            "memory_comparison": best_run.get("overall_memory_comparison"),
            "original_workload_comparison": best_run.get(
                "overall_original_workload_comparison"
            ),
            "publication_policy": (
                "Review and explicitly promote this patch to a clean target branch; "
                "the framework never merges or pushes automatically."
            ),
        }
        write_json(destination / "manifest.json", manifest)
        return manifest

    def run(self) -> Path:
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        experiment_dir = self.config.artifacts_root / experiment_id
        experiment_dir.mkdir(parents=True, exist_ok=False)
        started = time.perf_counter()
        source_repository = self.repositories.prepare()
        baseline_resolved = self.repositories.resolve(
            source_repository, self.config.baseline_commit
        )
        if self.config.target_mode == "auto":
            self._discover_target(experiment_dir)
        human_resolved = (
            self.repositories.resolve(source_repository, self.config.human_fix_commit)
            if self.config.human_fix_commit
            else None
        )
        manifest = {
            "experiment_id": experiment_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "config": self.config.manifest_dict(),
            "resolved_commits": {
                "baseline": baseline_resolved,
                "human_fix": human_resolved,
            },
            "actual_model": self.model_name,
            "target_discovery": (
                {
                    "selection": self.hotspot_summary.get("selection"),
                    "hotspots": self.hotspot_summary.get("hotspots"),
                    "profile_format": self.hotspot_summary.get("profile_format"),
                    "task_classification": self.hotspot_summary.get(
                        "task_classification"
                    ),
                    "profiler_routing": self.hotspot_summary.get(
                        "profiler_routing"
                    ),
                }
                if self.hotspot_summary
                else None
            ),
        }
        write_json(experiment_dir / "manifest.json", manifest)
        write_json(experiment_dir / "environment.json", _environment())

        LOGGER.info("[Reference] baseline")
        (
            baseline_workspace,
            _,
            baseline_performance,
            baseline_resources,
            baseline_workload,
        ) = self._prepare_reference(experiment_dir, "baseline", self.config.baseline_commit)
        task_classification = classify_baseline_evidence(
            baseline_resources, baseline_workload
        )
        write_json(experiment_dir / "task_classification.json", task_classification)
        profiler_routing = route_from_task_classification(task_classification)
        profiler_routing = require_objective_profiler(
            profiler_routing, self.config.optimization_objective
        )
        write_json(experiment_dir / "profiler_routing.json", profiler_routing)
        profiler_evidence = self._collect_profiler_evidence(
            experiment_dir,
            baseline_workspace,
            profiler_routing,
            baseline_resources,
            baseline_workload,
        )
        human_performance: PerformanceResult | None = None
        human_resources: ResourceResult | None = None
        human_workload: PerformanceResult | None = None
        if self.config.human_fix_commit:
            LOGGER.info("[Reference] human fix")
            (
                _,
                _,
                human_performance,
                human_resources,
                human_workload,
            ) = self._prepare_reference(
                experiment_dir, "human_fix", self.config.human_fix_commit
            )

        run_summaries: list[dict[str, Any]] = []
        rows: list[dict[str, Any]] = []
        for run_number in range(1, self.config.experiment_runs + 1):
            LOGGER.info("[Experiment] independent run %d", run_number)
            summary, run_rows, workspace = self._run_one(
                experiment_dir,
                run_number,
                baseline_performance,
                baseline_resources,
                baseline_workload,
            )
            run_summaries.append(summary)
            rows.extend(run_rows)

        fieldnames = [
            "run",
            "iteration",
            "decision",
            "functional_passed",
            "speedup_percent",
            "memory_reduction_percent",
            "significant",
            "workload_speedup_percent",
            "workload_significant",
            "workload_median_seconds",
            "median_seconds",
            "robust_rsd_percent",
            "peak_rss_bytes",
            "tracemalloc_peak_bytes",
            "read_bytes",
            "write_bytes",
            "lines_added",
            "lines_deleted",
            "patch_error",
        ]
        with (experiment_dir / "candidates.csv").open(
            "w", encoding="utf-8", newline=""
        ) as output:
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        functional_count = sum(bool(row["functional_passed"]) for row in rows)
        accepted_count = sum(row["decision"] == "ACCEPT" for row in rows)
        successful_runs = sum(bool(item["accepted_iterations"]) for item in run_summaries)
        human_comparison = (
            compare_performance(baseline_performance, human_performance).to_dict()
            if human_performance
            else None
        )
        human_workload_comparison = (
            compare_performance(baseline_workload, human_workload).to_dict()
            if baseline_workload is not None and human_workload is not None
            else None
        )
        human_memory_comparison = (
            compare_memory(baseline_resources, human_resources).to_dict()
            if baseline_resources is not None
            and baseline_resources.passed
            and human_resources is not None
            and human_resources.passed
            else None
        )
        if self.config.optimization_objective == "memory":
            best_run_key = lambda item: (
                (item.get("overall_memory_comparison") or {}).get(
                    "reduction_percent", float("-inf")
                )
            )
        else:
            best_run_key = lambda item: item["overall_comparison"][
                "speedup_percent"
            ]
        best_run = max(
            run_summaries,
            key=best_run_key,
        )
        release_candidate = self._write_release_candidate(
            experiment_dir, best_run, baseline_resolved
        )
        run_usage = _usage_sum([item["usage"] for item in run_summaries])
        benchmark_usage = _usage_sum(self.benchmark_usages)
        total_usage = {
            key: run_usage.get(key, 0) + benchmark_usage.get(key, 0)
            for key in run_usage
        }
        estimated_cost, cost_note = _estimated_cost_cny(total_usage)
        summary = {
            "status": "COMPLETE",
            "task_id": self.config.task_id,
            "candidate_count": len(rows),
            "functional_candidate_count": functional_count,
            "functional_success_rate": functional_count / len(rows) if rows else 0.0,
            "accepted_candidate_count": accepted_count,
            "accepted_candidate_rate": accepted_count / len(rows) if rows else 0.0,
            "runs_with_accepted_patch": successful_runs,
            "run_success_rate": successful_runs / len(run_summaries),
            "human_fix_comparison": human_comparison,
            "human_fix_memory_comparison": human_memory_comparison,
            "human_fix_original_workload_comparison": human_workload_comparison,
            "best_deepseek_comparison": best_run["overall_comparison"],
            "best_deepseek_memory_comparison": best_run.get(
                "overall_memory_comparison"
            ),
            "best_deepseek_original_workload_comparison": best_run.get(
                "overall_original_workload_comparison"
            ),
            "run_summaries": run_summaries,
            "baseline_resources": baseline_resources.to_dict() if baseline_resources else None,
            "task_classification": task_classification,
            "profiler_routing": profiler_routing,
            "profiler_evidence": profiler_evidence,
            "human_fix_resources": human_resources.to_dict() if human_resources else None,
            "baseline_original_workload": (
                baseline_workload.to_dict() if baseline_workload else None
            ),
            "human_fix_original_workload": (
                human_workload.to_dict() if human_workload else None
            ),
            "usage": total_usage,
            "model_calls": sum(item["model_calls"] for item in run_summaries)
            + len(self.benchmark_usages),
            "benchmark_generation": self.benchmark_summary,
            "elapsed_seconds": time.perf_counter() - started,
            "estimated_cost_cny": estimated_cost,
            "estimated_cost_note": cost_note,
            "release_candidate": release_candidate,
        }
        if self.config.keep_workspaces:
            summary["workspace_cleanup"] = {"policy": "keep", "removed": []}
        else:
            summary["workspace_cleanup"] = self._remove_experiment_workspaces(
                experiment_dir
            )
        write_json(experiment_dir / "summary.json", summary)
        (experiment_dir / "REPORT_ZH.md").write_text(
            _render_report(summary, manifest), encoding="utf-8"
        )
        LOGGER.info("[Complete] artifacts: %s", experiment_dir)
        return experiment_dir
