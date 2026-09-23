#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.config import FrameworkConfig  # noqa: E402
from src.framework.evaluator import (  # noqa: E402
    Evaluator,
    PerformanceResult,
    ResourceResult,
    compare_performance,
)
from src.framework.generated_benchmark import sha256_file  # noqa: E402
from src.framework.patching import assert_hashes_unchanged, file_hashes  # noqa: E402
from src.framework.replay import reconstruct_frozen_workspaces  # noqa: E402
from src.framework.sandbox import SandboxLimits  # noqa: E402


LABELS = {
    "baseline": "Baseline",
    "human_fix": "Human Fix",
    "deepseek_fix": "DeepSeek Fix",
}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def functional_gate(
    evaluator: Evaluator,
    config: FrameworkConfig,
    workspace: Path,
    destination: Path,
) -> dict[str, Any]:
    protected = file_hashes(workspace, config.context_files)
    commands = {
        "targeted_tests": config.targeted_test_command,
        "full_tests": config.full_test_command,
    }
    if config.invariant_test_command:
        commands["invariants_and_target_hit"] = config.invariant_test_command
    results: dict[str, Any] = {}
    for name, command in commands.items():
        result = evaluator.functional_test(workspace, command, destination / name)
        results[name] = result.to_dict()
        if not result.passed:
            write_json(destination / "summary.json", {"passed": False, "stages": results})
            raise RuntimeError(f"{name} failed: {result.stderr or result.stdout}")
    assert_hashes_unchanged(workspace, protected)
    summary = {"passed": True, "stages": results, "protected_files": True}
    write_json(destination / "summary.json", summary)
    return summary


def measure_resources(
    evaluator: Evaluator,
    config: FrameworkConfig,
    workspace: Path,
    destination: Path,
    repetitions: int,
) -> tuple[list[ResourceResult], float]:
    if config.resource_command is None:
        raise RuntimeError("Memory retest requires resource_command")
    samples: list[ResourceResult] = []
    for index in range(1, repetitions + 1):
        result = evaluator.resource_test(
            workspace,
            config.resource_command,
            destination / f"sample_{index:02d}" / "resource_workload.json",
        )
        write_json(
            destination / f"sample_{index:02d}" / "resources.json",
            result.to_dict(),
        )
        if not result.passed or result.tracemalloc_peak_bytes is None:
            raise RuntimeError(
                f"Resource sample {index} failed: "
                f"{result.command_result.stderr or result.command_result.stdout}"
            )
        samples.append(result)
    median_peak = statistics.median(
        item.tracemalloc_peak_bytes for item in samples if item.tracemalloc_peak_bytes
    )
    return samples, float(median_peak)


def reduction_percent(baseline: float, candidate: float) -> float:
    return 100.0 * (baseline - candidate) / baseline


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# urllib 内存闭环无 LLM 独立复测",
        "",
        "本次仅重建并测量已经冻结的 Baseline、Human Fix 和 DeepSeek Fix，模型调用次数为 0。",
        "",
        "| 版本 | 功能检查 | 运行时间中位数 | 相对 Baseline | 内存峰值中位数 | 内存下降 |",
        "|---|:---:|---:|---:|---:|---:|",
    ]
    for name in ("baseline", "human_fix", "deepseek_fix"):
        item = summary["versions"][name]
        lines.append(
            f"| {LABELS[name]} | {'通过' if item['functional_passed'] else '失败'} | "
            f"{item['median_seconds']:.6f} s | {item['speedup_percent']:.2f}% | "
            f"{item['median_tracemalloc_peak_bytes']:.0f} bytes | "
            f"{item['memory_reduction_percent']:.2f}% |"
        )
    lines.extend(
        [
            "",
            f"- 每个版本独立内存测量：{summary['resource_repetitions']} 次",
            "- 计时模式：pyperf 标准模式（未使用 `--fast`）",
            "- 所有功能测试、benchmark 和资源测量均在 Docker 沙箱中执行。",
            "- 本报告验证冻结补丁，不生成、修改或选择新补丁。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Independently retest the frozen urllib memory result without LLM calls."
    )
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "cpython_urllib_memory_e2e.yaml",
    )
    parser.add_argument("--resource-repetitions", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.resource_repetitions < 1:
        raise ValueError("--resource-repetitions must be positive")

    artifacts = args.artifacts.resolve()
    config = FrameworkConfig.load(args.config, PROJECT_ROOT)
    execution = config.execution_sandbox
    if execution is None:
        raise RuntimeError("Retest requires execution_sandbox")
    release = json.loads(
        (artifacts / "release_candidate" / "manifest.json").read_text(encoding="utf-8")
    )
    patch_path = artifacts / "release_candidate" / "best.patch"
    if sha256_file(patch_path) != release.get("patch_sha256"):
        raise RuntimeError("Frozen best.patch hash mismatch")

    output = args.output or (
        artifacts
        / "standard_retest"
        / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    workspaces = reconstruct_frozen_workspaces(
        artifact_dir=artifacts,
        config=config,
        destination=output / "workspaces",
        run_number=int(release["run"]),
    )
    evaluator = Evaluator(
        config.timeout_seconds,
        primary_benchmark=config.primary_benchmark,
        docker_image=execution.image,
        project_root=PROJECT_ROOT,
        sandbox_limits=SandboxLimits(
            cpus=execution.cpus,
            memory=execution.memory,
            pids=execution.pids,
            timeout_seconds=execution.timeout_seconds,
            max_output_bytes=execution.max_output_bytes,
        ),
    )

    started = time.perf_counter()
    measured: dict[str, dict[str, Any]] = {}
    performance_results: dict[str, PerformanceResult] = {}
    for name in ("baseline", "human_fix", "deepseek_fix"):
        print(f"[Retest] {LABELS[name]}", flush=True)
        version_dir = output / name
        functional_gate(
            evaluator, config, workspaces[name], version_dir / "functional"
        )
        performance = evaluator.performance_test(
            workspaces[name],
            config.benchmark_command,
            version_dir / "performance" / "pyperf.json",
        )
        write_json(version_dir / "performance" / "performance.json", performance.to_dict())
        if not performance.passed or performance.primary is None:
            raise RuntimeError(
                f"{name} pyperf failed: "
                f"{performance.command_result.stderr or performance.command_result.stdout}"
            )
        resources, median_peak = measure_resources(
            evaluator,
            config,
            workspaces[name],
            version_dir / "resources",
            args.resource_repetitions,
        )
        performance_results[name] = performance
        measured[name] = {
            "functional_passed": True,
            "performance": performance.to_dict(),
            "resource_samples": [item.to_dict() for item in resources],
            "median_seconds": performance.primary.median_seconds,
            "median_tracemalloc_peak_bytes": median_peak,
        }

    baseline_performance = performance_results["baseline"]
    baseline_peak = measured["baseline"]["median_tracemalloc_peak_bytes"]
    for name in ("baseline", "human_fix", "deepseek_fix"):
        if name == "baseline":
            speedup = 0.0
        else:
            speedup = compare_performance(
                baseline_performance, performance_results[name]
            ).speedup_percent
        measured[name]["speedup_percent"] = speedup
        measured[name]["memory_reduction_percent"] = reduction_percent(
            baseline_peak, measured[name]["median_tracemalloc_peak_bytes"]
        )

    summary = {
        "status": "PASS",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "no_llm": True,
        "llm_call_count": 0,
        "source_artifacts": str(artifacts),
        "patch_sha256": release["patch_sha256"],
        "resource_repetitions": args.resource_repetitions,
        "elapsed_seconds": time.perf_counter() - started,
        "versions": measured,
    }
    write_json(output / "summary.json", summary)
    (output / "REPORT_ZH.md").write_text(render_report(summary), encoding="utf-8")
    shutil.rmtree(output / "workspaces")
    print(f"[Complete] {output.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
