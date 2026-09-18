#!/usr/bin/env python3
"""Re-measure frozen E2E artifacts without making any LLM calls."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.evaluator import (  # noqa: E402
    Evaluator,
    PerformanceResult,
    ResourceResult,
    compare_performance,
)
from src.framework.generated_benchmark import sha256_file  # noqa: E402


VERSION_LABELS = {
    "baseline": "Baseline（优化前）",
    "human_fix": "Human Fix（官方人工优化）",
    "deepseek_fix": "DeepSeek Fix（模型最佳版本）",
}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def resolve_inputs(artifact_dir: Path, run_number: int) -> dict[str, Any]:
    artifact_dir = artifact_dir.expanduser().resolve()
    benchmark_path = artifact_dir / "benchmark" / "benchmark.py"
    freeze_path = artifact_dir / "benchmark" / "freeze.json"
    if not benchmark_path.is_file() or not freeze_path.is_file():
        raise FileNotFoundError(
            "找不到冻结 benchmark；请把 --artifacts 指向一次完整 E2E 实验目录"
        )

    freeze = read_json(freeze_path)
    expected_hash = str(freeze.get("sha256", ""))
    actual_hash = sha256_file(benchmark_path)
    if not expected_hash or actual_hash != expected_hash:
        raise RuntimeError(
            "冻结 benchmark 的 SHA-256 校验失败，已停止复测："
            f" expected={expected_hash!r}, actual={actual_hash!r}"
        )

    primary = freeze.get("primary_benchmark")
    if not isinstance(primary, str) or not primary:
        raise ValueError(f"freeze.json 缺少 primary_benchmark: {freeze_path}")

    workspaces = {
        "baseline": artifact_dir / "baseline" / "workspace",
        "human_fix": artifact_dir / "human_fix" / "workspace",
        "deepseek_fix": artifact_dir / f"run_{run_number:02d}" / "workspace",
    }
    missing = [str(path) for path in workspaces.values() if not path.is_dir()]
    if missing:
        raise FileNotFoundError("找不到待复测 workspace:\n" + "\n".join(missing))

    python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if not python.is_file():
        raise FileNotFoundError(f"找不到项目虚拟环境 Python: {python}")

    return {
        "artifact_dir": artifact_dir,
        "benchmark_path": benchmark_path,
        "benchmark_hash": actual_hash,
        "freeze": freeze,
        "primary_benchmark": primary,
        "workspaces": workspaces,
        "python": python,
    }


def create_output_dir(artifact_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = artifact_dir / "standard_retest" / timestamp
    output.mkdir(parents=True, exist_ok=False)
    return output


def performance_command(python: Path, benchmark: Path, fast: bool) -> tuple[str, ...]:
    command = [str(python), str(benchmark)]
    if fast:
        command.append("--fast")
    command.extend(["-o", "{output}"])
    return tuple(command)


def resource_command(
    python: Path, benchmark: Path, primary_benchmark: str
) -> tuple[str, ...]:
    return (
        str(python),
        str(PROJECT_ROOT / "scripts" / "measure_generated_benchmark.py"),
        "--benchmark",
        str(benchmark),
        "--primary",
        primary_benchmark,
        "--output",
        "{output}",
    )


def measure_version(
    *,
    name: str,
    workspace: Path,
    output_dir: Path,
    evaluator: Evaluator,
    benchmark_path: Path,
    python: Path,
    primary_benchmark: str,
    fast: bool,
) -> tuple[PerformanceResult, ResourceResult]:
    version_dir = output_dir / name
    version_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Standard Retest] {VERSION_LABELS[name]}", flush=True)

    performance = evaluator.performance_test(
        repository=workspace,
        command_template=performance_command(python, benchmark_path, fast),
        result_path=version_dir / "pyperf.json",
    )
    write_json(version_dir / "performance.json", performance.to_dict())
    if not performance.passed:
        stderr = performance.command_result.stderr.strip()
        raise RuntimeError(f"{name} 的 pyperf 复测失败：{stderr or '未知错误'}")

    resources = evaluator.resource_test(
        repository=workspace,
        command_template=resource_command(python, benchmark_path, primary_benchmark),
        result_path=version_dir / "resource_workload.json",
    )
    write_json(version_dir / "resources.json", resources.to_dict())
    if not resources.passed:
        stderr = resources.command_result.stderr.strip()
        raise RuntimeError(f"{name} 的资源测量失败：{stderr or '未知错误'}")

    primary = performance.primary
    assert primary is not None
    print(
        f"  median={primary.median_seconds:.6f}s, "
        f"robust RSD={primary.robust_rsd_percent:.2f}%"
        if primary.robust_rsd_percent is not None
        else f"  median={primary.median_seconds:.6f}s",
        flush=True,
    )
    return performance, resources


def fmt_seconds(value: float | None) -> str:
    return "—" if value is None else f"{value:.6f}"


def fmt_percent(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}%"


def fmt_mebibytes(value: int | None) -> str:
    return "—" if value is None else f"{value / 1024 / 1024:.2f} MiB"


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# 端到端实验无 LLM 复测报告",
        "",
        "本次只复测已经冻结的三个代码版本，不调用 DeepSeek，也不生成或修改代码。",
        "这样可以把“生成候选代码”和“测量性能”分开，避免模型调用时间与费用干扰性能数据。",
        "",
        "## 复测设置",
        "",
        f"- 测量模式：{'快速预跑（--fast）' if summary['fast_mode'] else 'pyperf 标准模式'}",
        f"- 主 benchmark：`{summary['primary_benchmark']}`",
        f"- 冻结 benchmark SHA-256：`{summary['benchmark_sha256']}`",
        "- LLM 调用次数：0",
        "",
        "## 运行时间结果",
        "",
        "| 版本 | median（秒） | mean（秒） | robust RSD | 样本数 | 相对 Baseline | 显著差异 |",
        "|---|---:|---:|---:|---:|---:|:---:|",
    ]
    versions = summary["versions"]
    comparisons = summary["comparisons"]
    for name in ("baseline", "human_fix", "deepseek_fix"):
        performance = versions[name]["performance"]
        primary = performance["benchmarks"][summary["primary_benchmark"]]
        comparison = comparisons.get(name)
        speedup = 0.0 if comparison is None else comparison["speedup_percent"]
        significant = "—" if comparison is None else ("是" if comparison["significant"] else "否")
        lines.append(
            "| "
            + " | ".join(
                [
                    VERSION_LABELS[name],
                    fmt_seconds(primary["median_seconds"]),
                    fmt_seconds(primary["mean_seconds"]),
                    fmt_percent(primary["robust_rsd_percent"]),
                    str(primary["value_count"]),
                    fmt_percent(speedup),
                    significant,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## 独立资源测量",
            "",
            "资源数据由单独进程运行同一主 workload 得到，不与 pyperf 计时混在一起。",
            "",
            "| 版本 | wall time | user CPU | system CPU | CPU/wall | 峰值 RSS | tracemalloc peak |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name in ("baseline", "human_fix", "deepseek_fix"):
        resources = versions[name]["resources"]
        metrics = resources["command"]["metrics"]
        ratio = metrics["cpu_to_wall_ratio"]
        lines.append(
            "| "
            + " | ".join(
                [
                    VERSION_LABELS[name],
                    fmt_seconds(metrics["wall_seconds"]),
                    fmt_seconds(metrics["user_cpu_seconds"]),
                    fmt_seconds(metrics["system_cpu_seconds"]),
                    "—" if ratio is None else f"{ratio:.3f}",
                    fmt_mebibytes(metrics["peak_rss_bytes"]),
                    fmt_mebibytes(resources["tracemalloc_peak_bytes"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## 解读边界",
            "",
            "- 本报告可以用于比较同一台机器、同一次复测中的三个版本。",
            "- 若使用本机而非固定 Linux 服务器，结果仍属于本地证据，不应当作为最终论文级结论。",
            "- 运行时间与资源指标分别报告；运行时间变快不等于所有资源指标都改善。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="使用冻结 benchmark 复测 Baseline、Human Fix 和 DeepSeek Fix；不调用 LLM。"
    )
    parser.add_argument("--artifacts", type=Path, required=True, help="一次完整 E2E 实验目录")
    parser.add_argument("--run-number", type=int, default=1, help="要复测的 DeepSeek run，默认 1")
    parser.add_argument(
        "--timeout-seconds", type=int, default=1800, help="每个测量命令的超时秒数"
    )
    parser.add_argument(
        "--fast", action="store_true", help="仅调试时使用 pyperf --fast；默认是标准模式"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="只校验输入、打印计划，不执行测量"
    )
    args = parser.parse_args()

    inputs = resolve_inputs(args.artifacts, args.run_number)
    print("[Check] frozen benchmark SHA-256: PASS", flush=True)
    print(f"[Check] primary benchmark: {inputs['primary_benchmark']}", flush=True)
    for name, workspace in inputs["workspaces"].items():
        print(f"[Check] {name}: {workspace}", flush=True)
    print(f"[Mode] {'FAST (debug only)' if args.fast else 'STANDARD (no --fast)'}", flush=True)
    print("[LLM] disabled; API calls = 0", flush=True)
    if args.dry_run:
        print("[Dry Run] validation complete; no benchmark was executed", flush=True)
        return 0

    started = time.perf_counter()
    output_dir = create_output_dir(inputs["artifact_dir"])
    evaluator = Evaluator(args.timeout_seconds, inputs["primary_benchmark"])
    measured: dict[str, tuple[PerformanceResult, ResourceResult]] = {}
    for name, workspace in inputs["workspaces"].items():
        measured[name] = measure_version(
            name=name,
            workspace=workspace,
            output_dir=output_dir,
            evaluator=evaluator,
            benchmark_path=inputs["benchmark_path"],
            python=inputs["python"],
            primary_benchmark=inputs["primary_benchmark"],
            fast=args.fast,
        )

    baseline = measured["baseline"][0]
    comparisons = {
        name: compare_performance(baseline, measured[name][0]).to_dict()
        for name in ("human_fix", "deepseek_fix")
    }
    summary = {
        "schema_version": 1,
        "no_llm": True,
        "llm_call_count": 0,
        "fast_mode": args.fast,
        "source_artifacts": str(inputs["artifact_dir"]),
        "output_dir": str(output_dir),
        "benchmark_path": str(inputs["benchmark_path"]),
        "benchmark_sha256": inputs["benchmark_hash"],
        "primary_benchmark": inputs["primary_benchmark"],
        "frozen_workload": inputs["freeze"].get("workload"),
        "run_number": args.run_number,
        "elapsed_seconds": time.perf_counter() - started,
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "executable": str(inputs["python"]),
        },
        "versions": {
            name: {
                "workspace": str(inputs["workspaces"][name]),
                "performance": results[0].to_dict(),
                "resources": results[1].to_dict(),
            }
            for name, results in measured.items()
        },
        "comparisons": comparisons,
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "REPORT_ZH.md").write_text(render_report(summary), encoding="utf-8")

    print(f"[Complete] retest artifacts: {output_dir}", flush=True)
    print(f"Summary: {output_dir / 'summary.json'}", flush=True)
    print(f"中文报告: {output_dir / 'REPORT_ZH.md'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
