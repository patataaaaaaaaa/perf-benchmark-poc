#!/usr/bin/env python3
"""Re-test a frozen experiment's original workload without LLM calls."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.config import FrameworkConfig  # noqa: E402
from src.framework.evaluator import Evaluator, compare_performance  # noqa: E402
from src.framework.sandbox import SandboxLimits  # noqa: E402
from src.framework.replay import reconstruct_frozen_workspaces  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "more_itertools_triplewise_auto_e2e.yaml",
    )
    parser.add_argument("--run-number", type=int, default=1)
    args = parser.parse_args()

    config = FrameworkConfig.load(args.config, PROJECT_ROOT)
    if config.original_workload_command is None:
        raise ValueError("Config has no original_workload_command")
    execution = config.execution_sandbox
    if execution is None:
        raise ValueError("Execution sandbox must be enabled")

    source = args.artifacts.expanduser().resolve()
    workspaces = {
        "baseline": source / "baseline" / "workspace",
        "human_fix": source / "human_fix" / "workspace",
        "deepseek_fix": source / f"run_{args.run_number:02d}" / "workspace",
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = source / "original_workload_retest" / stamp
    output.mkdir(parents=True)
    reconstructed = False
    if not all(path.is_dir() for path in workspaces.values()):
        workspaces = reconstruct_frozen_workspaces(
            artifact_dir=source,
            config=config,
            destination=output / "reconstructed_workspaces",
            run_number=args.run_number,
        )
        reconstructed = True
    evaluator = Evaluator(
        timeout_seconds=config.timeout_seconds,
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

    results = {}
    measured = {}
    for name, workspace in workspaces.items():
        print(f"[Original Workload] {name}", flush=True)
        result = evaluator.performance_test(
            workspace,
            config.original_workload_command,
            output / name / "pyperf.json",
        )
        write_json(output / name / "performance.json", result.to_dict())
        if not result.passed:
            raise RuntimeError(
                f"{name} failed: {result.command_result.stderr.strip()}"
            )
        measured[name] = result
        primary = result.primary
        assert primary is not None
        print(f"  median={primary.median_seconds:.6f}s", flush=True)

    baseline = measured["baseline"]
    for name in ("human_fix", "deepseek_fix"):
        comparison = compare_performance(baseline, measured[name])
        results[name] = comparison.to_dict()
        results[name]["passes_minimum"] = (
            comparison.speedup_percent >= config.min_workload_speedup_percent
        )

    summary = {
        "no_llm": True,
        "llm_call_count": 0,
        "workspaces_reconstructed": reconstructed,
        "source_artifacts": str(source),
        "minimum_workload_speedup_percent": config.min_workload_speedup_percent,
        "versions": {name: result.to_dict() for name, result in measured.items()},
        "comparisons": results,
    }
    write_json(output / "summary.json", summary)
    report = [
        "# 原始 workload 验收实验",
        "",
        "本次使用冻结代码版本，不调用 LLM；所有 workload 均在 Docker 沙箱中运行。",
        "",
        "| 版本 | 相对 Baseline 提升 | 达到最低要求 |",
        "|---|---:|:---:|",
    ]
    for name, label in (("human_fix", "官方修复"), ("deepseek_fix", "DeepSeek 修复")):
        item = results[name]
        report.append(
            f"| {label} | {item['speedup_percent']:.2f}% | "
            f"{'是' if item['passes_minimum'] else '否'} |"
        )
    report.extend(["", f"结果目录：`{output}`", ""])
    (output / "REPORT_ZH.md").write_text("\n".join(report), encoding="utf-8")
    if reconstructed:
        shutil.rmtree(output / "reconstructed_workspaces")
    print(f"[Complete] artifacts: {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
