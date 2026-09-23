#!/usr/bin/env python3
"""Exercise the framework's automatic target entry without calling an LLM."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.config import FrameworkConfig  # noqa: E402
from src.framework.evaluator import Evaluator  # noqa: E402
from src.framework.pipeline import OptimizationFramework  # noqa: E402
from src.framework.sandbox import SandboxLimits  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate workload -> profiler -> target selection with no LLM calls."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "cpython_urllib_auto_target.yaml",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    config = FrameworkConfig.load(args.config, PROJECT_ROOT)
    if config.target_mode != "auto":
        raise ValueError("This validation requires target_mode: auto")
    if config.hotspot_discovery is None:
        raise ValueError("hotspot_discovery is required")

    output = args.output
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output = config.artifacts_root / stamp
    elif not output.is_absolute():
        output = PROJECT_ROOT / output
    output.mkdir(parents=True, exist_ok=False)

    execution = config.execution_sandbox
    if execution is None:
        raise ValueError("execution_sandbox is required")
    # No agent object or API client is created, which guarantees this command
    # cannot accidentally make an LLM call. The evaluator only runs Docker.
    framework = OptimizationFramework(
        project_root=PROJECT_ROOT,
        config=config,
        agents=None,  # type: ignore[arg-type]
        evaluator=Evaluator(
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
        ),
        model_name="no-llm",
    )
    framework._discover_target(output)

    selected_file = str(framework.config.target_file)
    selected_symbol = framework.config.target_symbol
    expected_symbol = config.hotspot_discovery.validation_expected_symbol
    passed = bool(selected_symbol) and (
        expected_symbol is None or selected_symbol == expected_symbol
    )
    summary: dict[str, object] = {
        "status": "PASS" if passed else "FAIL",
        "llm_called": False,
        "input": {
            "repository": str(config.repository),
            "baseline_commit": config.baseline_commit,
            "workload": "subjects/cpython_urllib/profile_unquote_workload.py",
            "preconfigured_target_file": None,
            "preconfigured_target_symbol": None,
        },
        "selection": {
            "target_file": selected_file,
            "target_symbol": selected_symbol,
            "editable_files": [str(item) for item in framework.config.editable_files],
            "expected_symbol": expected_symbol,
            "expected_symbol_used_for_selection": False,
            "profiler": (
                (framework.hotspot_summary or {}).get("selection", {}).get(
                    "profiler"
                )
            ),
        },
        "task_classification": (
            (framework.hotspot_summary or {}).get("task_classification")
        ),
        "profiler_routing": (
            (framework.hotspot_summary or {}).get("profiler_routing")
        ),
        "hotspots": (framework.hotspot_summary or {}).get("hotspots", []),
    }
    write_json(output / "summary.json", summary)

    report = [
        "# 自动入口验证报告",
        "",
        "本实验不调用大模型，只验证框架能否从真实 workload 的 profiler 数据中自动选择优化目标。",
        "",
        f"- 结果：**{summary['status']}**",
        "- LLM 调用：0 次",
        f"- 自动选择函数：`{selected_symbol}`",
        f"- 自动选择文件：`{selected_file}`",
        f"- 选择目标所用 profiler：`{summary['selection']['profiler']}`",
        f"- 预期热点是否参与排名：否",
        "",
        "## Top 热点",
        "",
        "| 排名 | 函数 | profiler 指标 | 占比 |",
        "|---:|---|---:|---:|",
    ]
    for item in summary["hotspots"]:  # type: ignore[union-attr]
        if "self_time_seconds" in item:
            metric = f"{item['self_time_seconds']:.6f} s"
            percent = float(item["self_time_percent"])
        else:
            metric = f"{item['size_bytes']} bytes"
            percent = float(item["size_percent"])
        report.append(
            f"| {item['rank']} | `{item['qualified_name']}` | "
            f"{metric} | {percent:.2f}% |"
        )
    (output / "REPORT_ZH.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"[Result] {summary['status']}")
    print(f"[Selected] {selected_symbol} ({selected_file})")
    print(f"[Complete] {output}")
    return 0 if passed else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Auto-target validation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
