#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.evaluator import Evaluator  # noqa: E402
from src.framework.sandbox import SandboxLimits  # noqa: E402
from src.framework.task_classification import (  # noqa: E402
    PerformanceSample,
    classify_performance_task,
)


CASES = {
    "cpu": (1_500_000, 4_500_000),
    "memory": (16, 64),
    "io": (8, 32),
}
EXPECTED = {"cpu": "cpu_bound", "memory": "memory", "io": "io"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在 Docker 中验证第一版性能任务分类器"
    )
    parser.add_argument(
        "--image", default="perf-benchmark-sandbox:py311-v1"
    )
    parser.add_argument("--output-root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_root = args.output_root or (
        PROJECT_ROOT / "artifacts" / "task_classification" / timestamp
    )
    output_root.mkdir(parents=True, exist_ok=True)

    evaluator = Evaluator(
        timeout_seconds=60,
        docker_image=args.image,
        project_root=PROJECT_ROOT,
        sandbox_limits=SandboxLimits(
            cpus=1.0,
            memory="512m",
            pids=32,
            timeout_seconds=60,
            max_output_bytes=100_000,
        ),
    )
    summary: dict[str, object] = {"docker_image": args.image, "cases": {}}
    all_passed = True

    # Keep the read-only code mount separate from the writable artifact mount.
    # Real experiments already use an external repository clone; this empty
    # workspace gives this self-test the same mount shape.
    with TemporaryDirectory(prefix="perf-classifier-") as temporary:
        workspace = Path(temporary)
        for kind, sizes in CASES.items():
            print(f"[Classify] {kind}", flush=True)
            case_dir = output_root / kind
            samples: list[PerformanceSample] = []
            raw_results: list[dict[str, object]] = []
            for size in sizes:
                result_path = case_dir / f"size_{size}.json"
                result = evaluator.resource_test(
                    workspace,
                    (
                        sys.executable,
                        str(
                            PROJECT_ROOT
                            / "subjects/classification/controlled_workload.py"
                        ),
                        "--kind",
                        kind,
                        "--size",
                        str(size),
                        "--output",
                        "{output}",
                    ),
                    result_path,
                )
                raw_results.append(result.to_dict())
                if not result.passed:
                    raise RuntimeError(
                        f"Controlled workload failed for {kind}/{size}: "
                        f"{result.command_result.stderr}"
                    )
                samples.append(PerformanceSample.from_mapping(result.to_dict()))

            classification = classify_performance_task(samples)
            passed = classification.task_type == EXPECTED[kind]
            all_passed = all_passed and passed
            summary["cases"][kind] = {  # type: ignore[index]
                "expected": EXPECTED[kind],
                "passed": passed,
                "classification": classification.to_dict(),
                "measurements": raw_results,
            }

    summary["passed"] = all_passed
    summary_path = output_root / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[Complete] {summary_path.resolve()}", flush=True)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
