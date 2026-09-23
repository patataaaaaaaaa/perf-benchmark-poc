#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.task_classification import (  # noqa: E402
    PerformanceSample,
    classify_performance_task,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="根据已有资源指标判断 CPU、内存或 I/O 瓶颈类型"
    )
    parser.add_argument(
        "--sample",
        action="append",
        required=True,
        type=Path,
        help="资源指标 JSON；可重复传入形成多规模样本",
    )
    parser.add_argument("--goal", help="用户声明的优化目标，只作为上下文")
    parser.add_argument("--output", type=Path, help="分类结果 JSON 输出位置")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    samples: list[PerformanceSample] = []
    for path in args.sample:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Sample must be a JSON object: {path}")
        payload.setdefault("label", str(path))
        samples.append(PerformanceSample.from_mapping(payload))

    result = classify_performance_task(samples, declared_goal=args.goal)
    rendered = json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(args.output.resolve())
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
