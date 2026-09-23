#!/usr/bin/env python3
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
from src.framework.repository import RepositoryManager  # noqa: E402
from src.framework.workloads import discover_workload_candidates  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover repository-owned benchmark, test and example workload candidates."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "more_itertools_triplewise_auto_e2e.yaml",
    )
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    config = FrameworkConfig.load(args.config, PROJECT_ROOT)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = PROJECT_ROOT / "artifacts" / "workload_discovery" / stamp
    workspace = output / "workspace"
    output.mkdir(parents=True)
    try:
        resolved = RepositoryManager(config).checkout(workspace, config.baseline_commit)
        report = discover_workload_candidates(workspace, limit=args.limit)
        report["baseline_commit"] = resolved
        (output / "candidates.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        lines = [
            "# Workload 候选发现报告",
            "",
            f"- Baseline：`{resolved}`",
            f"- 候选总数：{report['candidate_count']}",
            f"- 已有 benchmark：{report['counts_by_source']['existing_benchmark']}",
            f"- Testcase：{report['counts_by_source']['existing_test']}",
            f"- Examples：{report['counts_by_source']['example']}",
            "",
            "这些条目只是有仓库证据的候选，还没有经过性能代表性、稳定性或人工确认。",
            "",
            "| 来源 | 路径 | 可直接运行 | 需要适配 | 可信度 |",
            "|---|---|:---:|:---:|:---:|",
        ]
        for candidate in report["candidates"]:
            lines.append(
                f"| {candidate['source']} | `{candidate['path']}` | "
                f"{candidate['directly_runnable']} | {candidate['requires_adaptation']} | "
                f"{candidate['confidence']} |"
            )
        (output / "REPORT_ZH.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    finally:
        if workspace.exists():
            shutil.rmtree(workspace)

    print(f"[Complete] workload candidates: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
