from __future__ import annotations

import csv
import json
import logging
import os
import platform
import subprocess
import sys
import time
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
from src.framework.evaluator import (
    Evaluator,
    PerformanceComparison,
    PerformanceResult,
    ResourceResult,
    compare_performance,
    run_command,
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


LOGGER = logging.getLogger("performance_framework")


def _performance_summary(result: PerformanceResult) -> dict[str, Any]:
    return {
        "primary_benchmark": result.primary_benchmark,
        "benchmarks": {
            name: stats.to_dict() for name, stats in result.benchmarks.items()
        },
        "measurement_process": result.command_result.metrics.to_dict(),
    }


def decide_candidate(
    functional_passed: bool,
    performance_passed: bool,
    improvement_percent: float | None,
    minimum_percent: float,
    *,
    significant: bool = True,
    require_significance: bool = False,
) -> str:
    if not functional_passed:
        return "REJECT_FUNCTIONAL"
    if not performance_passed or improvement_percent is None:
        return "REJECT_PERFORMANCE"
    if require_significance and not significant:
        return "REJECT_NOT_SIGNIFICANT"
    return "ACCEPT" if improvement_percent >= minimum_percent else "REJECT_PERFORMANCE"


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
    mode = (
        "本机快速预跑"
        if (
            "--fast" in manifest["config"]["benchmark_command"]
            or manifest["config"].get("benchmark_fast_mode")
        )
        else "服务器正式测量"
    )
    lines = [
        "# More-itertools `triplewise` 实验报告",
        "",
        f"- 模式：{mode}",
        f"- Baseline：`{manifest['resolved_commits']['baseline']}`",
        f"- Human Fix：`{manifest['resolved_commits']['human_fix']}`",
        f"- 模型：`{manifest['actual_model']}`",
        f"- Benchmark 来源：`{manifest['config'].get('benchmark_mode', 'fixed')}`",
        f"- 候选数：{summary['candidate_count']}",
        f"- 功能正确候选：{summary['functional_candidate_count']}（{summary['functional_success_rate']:.1%}）",
        f"- 被闭环接受候选：{summary['accepted_candidate_count']}（{summary['accepted_candidate_rate']:.1%}）",
        "",
        "## 运行时间结果",
        "",
        "| 对象 | 相对 Baseline 加速 | 显著 |",
        "|---|---:|---:|",
        f"| 官方 Human Fix | {human.get('speedup_percent', 0):.2f}% | {human.get('significant')} |",
        f"| 最佳 DeepSeek Run | {best.get('speedup_percent', 0):.2f}% | {best.get('significant')} |",
        "",
        "## CPU、内存与 I/O（独立展示）",
        "",
        "| 版本 | User CPU(s) | System CPU(s) | Peak RSS(bytes) | tracemalloc peak(bytes) | Read(bytes) | Write(bytes) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
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
            "I/O 在该 CPU 型任务中仅记录，不参与接受决策；macOS 上不可用时保留为 `null`。",
            "",
            "## 三个独立 Run",
            "",
            "| Run | 轮数 | 接受轮次 | 最佳加速 | 模型调用 | Tokens |",
            "|---:|---:|---|---:|---:|---:|",
        ]
    )
    for index, run in enumerate(summary["run_summaries"], 1):
        lines.append(
            f"| {index} | {run['iterations_run']} | {run['accepted_iterations']} | "
            f"{run['overall_comparison']['speedup_percent']:.2f}% | "
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
        python = self.config.targeted_test_command[0]
        stages: dict[str, Any] = {}
        commands: list[tuple[str, tuple[str, ...]]] = [
            (
                "syntax",
                (python, "-m", "py_compile", str(self.config.target_file)),
            ),
        ]
        if "." in self.config.target_symbol:
            module, symbol = self.config.target_symbol.rsplit(".", 1)
            commands.append(
                ("import", (python, "-c", f"from {module} import {symbol}"))
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
            result = run_command(command, workspace, self.config.timeout_seconds)
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
        source = (workspace / self.config.target_file).read_text(encoding="utf-8")
        source_context = extract_symbol_context(source, self.config.target_symbol)
        needle = self.config.target_symbol.rsplit(".", 1)[-1]
        excerpts: list[str] = []
        for relative in self.config.context_files:
            text = (workspace / relative).read_text(encoding="utf-8")
            excerpt = extract_matching_context(text, needle)
            if excerpt:
                excerpts.append(f"# {relative}\n{excerpt}")
        return source_context, "\n\n".join(excerpts)

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

    def _prepare_reference(
        self, experiment_dir: Path, name: str, ref: str | None
    ) -> tuple[Path, str, PerformanceResult, ResourceResult | None]:
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
        write_json(
            destination / "version.json",
            {"requested_ref": ref, "resolved_commit": resolved},
        )
        return workspace, resolved, performance, resources

    def _run_one(
        self,
        experiment_dir: Path,
        run_number: int,
        baseline_performance: PerformanceResult,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], Path]:
        run_dir = experiment_dir / f"run_{run_number:02d}"
        workspace = run_dir / "workspace"
        resolved = self.repositories.checkout(workspace, self.config.baseline_commit)
        protected_hashes = file_hashes(workspace, self.config.context_files)
        current_performance = baseline_performance
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
            )
            evaluation = {
                "run": run_number,
                "iteration": iteration,
                "decision": decision,
                "functional_passed": functional_passed,
                "comparison_vs_current_best": comparison.to_dict() if comparison else None,
                "minimum_speedup_percent": self.config.min_speedup_percent,
                "require_significance": self.config.require_significance,
                "patch_error": patch_error,
                "patch_stats": stats,
                "candidate_performance": (
                    candidate_performance.to_dict() if candidate_performance else None
                ),
                "candidate_resources": (
                    candidate_resources.to_dict() if candidate_resources else None
                ),
            }
            write_json(iteration_dir / "evaluation.json", evaluation)

            if decision == "ACCEPT":
                best_patch = repository_diff(workspace)
                current_performance = candidate_performance  # type: ignore[assignment]
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
                "significant": comparison.significant if comparison else None,
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
        summary = {
            "status": "COMPLETE",
            "baseline_commit": resolved,
            "stop_reason": stop_reason,
            "iterations_run": len(memory),
            "accepted_iterations": accepted_iterations,
            "overall_comparison": overall.to_dict(),
            "best_patch_changed_source": bool(best_patch),
            "final_resources": final_resources.to_dict() if final_resources else None,
            "final_retest": final_performance.to_dict(),
            "usage": _usage_sum(usages),
            "model_calls": len(usages),
            "elapsed_seconds": time.perf_counter() - started,
        }
        write_json(final_dir / "summary.json", summary)
        return summary, rows, workspace

    def run(self) -> Path:
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        experiment_dir = self.config.artifacts_root / experiment_id
        experiment_dir.mkdir(parents=True, exist_ok=False)
        started = time.perf_counter()
        source_repository = self.repositories.prepare()
        baseline_resolved = self.repositories.resolve(
            source_repository, self.config.baseline_commit
        )
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
        }
        write_json(experiment_dir / "manifest.json", manifest)
        write_json(experiment_dir / "environment.json", _environment())

        LOGGER.info("[Reference] baseline")
        _, _, baseline_performance, baseline_resources = self._prepare_reference(
            experiment_dir, "baseline", self.config.baseline_commit
        )
        human_performance: PerformanceResult | None = None
        human_resources: ResourceResult | None = None
        if self.config.human_fix_commit:
            LOGGER.info("[Reference] human fix")
            _, _, human_performance, human_resources = self._prepare_reference(
                experiment_dir, "human_fix", self.config.human_fix_commit
            )

        run_summaries: list[dict[str, Any]] = []
        rows: list[dict[str, Any]] = []
        winner_workspaces: list[Path] = []
        for run_number in range(1, self.config.experiment_runs + 1):
            LOGGER.info("[Experiment] independent run %d", run_number)
            summary, run_rows, workspace = self._run_one(
                experiment_dir, run_number, baseline_performance
            )
            run_summaries.append(summary)
            rows.extend(run_rows)
            winner_workspaces.append(workspace)

        fieldnames = [
            "run",
            "iteration",
            "decision",
            "functional_passed",
            "speedup_percent",
            "significant",
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
        best_run = max(
            run_summaries,
            key=lambda item: item["overall_comparison"]["speedup_percent"],
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
            "best_deepseek_comparison": best_run["overall_comparison"],
            "run_summaries": run_summaries,
            "baseline_resources": baseline_resources.to_dict() if baseline_resources else None,
            "human_fix_resources": human_resources.to_dict() if human_resources else None,
            "usage": total_usage,
            "model_calls": sum(item["model_calls"] for item in run_summaries)
            + len(self.benchmark_usages),
            "benchmark_generation": self.benchmark_summary,
            "elapsed_seconds": time.perf_counter() - started,
            "estimated_cost_cny": estimated_cost,
            "estimated_cost_note": cost_note,
        }
        write_json(experiment_dir / "summary.json", summary)
        (experiment_dir / "REPORT_ZH.md").write_text(
            _render_report(summary, manifest), encoding="utf-8"
        )
        LOGGER.info("[Complete] artifacts: %s", experiment_dir)
        return experiment_dir
