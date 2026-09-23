#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.evaluator import Evaluator  # noqa: E402
from src.framework.sandbox import SandboxLimits, run_in_docker  # noqa: E402
from src.framework.task_classification import (  # noqa: E402
    PerformanceSample,
    classify_performance_task,
)


CASES = {
    "openpyxl_memory": {
        "project": "openpyxl",
        "sizes": (20_000, 120_000),
        "extension": "xlsx",
        "expected_signal": "memory",
        "version": "3.1.5",
        "source": "https://foss.heptapod.net/openpyxl/openpyxl",
        "workload_basis": "openpyxl official performance and optimized-mode docs",
    },
    "fsspec_local_io": {
        "project": "fsspec",
        "sizes": (16, 64),
        "extension": "bin",
        "expected_signal": "io",
        "version": "2025.3.0",
        "source": "https://github.com/fsspec/filesystem_spec",
        "workload_basis": "fsspec LocalFileSystem documented file API",
    },
    "cachetools_memory": {
        "project": "cachetools",
        "sizes": (16, 64),
        "extension": "json",
        "expected_signal": "memory",
        "version": "5.5.0",
        "source": "https://github.com/tkem/cachetools",
        "workload_basis": "cachetools LRUCache documented getsizeof-based capacity",
    },
    "smart_open_local_io": {
        "project": "smart_open",
        "sizes": (16, 64),
        "extension": "bin",
        "expected_signal": "io",
        "version": "7.0.4",
        "source": "https://github.com/piskvorky/smart_open",
        "workload_basis": "smart_open documented local-file binary streaming API",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在 Docker 中验证真实 Python 项目的性能任务分类"
    )
    parser.add_argument(
        "--image", default="perf-benchmark-classification-real:py311-v1"
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument(
        "--case",
        action="append",
        choices=tuple(CASES),
        help="只运行指定 case；可以重复传入。默认运行全部。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_root = args.output_root or (
        PROJECT_ROOT / "artifacts" / "real_task_classification" / timestamp
    )
    output_root.mkdir(parents=True, exist_ok=True)
    limits = SandboxLimits(
        cpus=1.0,
        memory="1g",
        pids=32,
        timeout_seconds=180,
        max_output_bytes=100_000,
    )
    evaluator = Evaluator(
        timeout_seconds=180,
        docker_image=args.image,
        project_root=PROJECT_ROOT,
        sandbox_limits=limits,
    )
    summary: dict[str, object] = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "docker_image": args.image,
        "llm_called": False,
        "routing_applied": False,
        "cases": {},
    }
    all_passed = True

    with TemporaryDirectory(prefix="perf-real-classifier-") as temporary:
        workspace = Path(temporary)
        selected_cases = args.case or list(CASES)
        for case_name in selected_cases:
            case = CASES[case_name]
            print(f"[Real Classify] {case_name}", flush=True)
            case_dir = output_root / case_name
            case_dir.mkdir(parents=True, exist_ok=True)
            samples: list[PerformanceSample] = []
            measurements: list[dict[str, object]] = []
            preparation: list[dict[str, object]] = []

            for size in case["sizes"]:
                input_path = case_dir / f"input_{size}.{case['extension']}"
                prepare_result = run_in_docker(
                    image=args.image,
                    workspace=workspace,
                    harness=PROJECT_ROOT / "scripts",
                    output=case_dir,
                    inner_command=[
                        "python",
                        "/subjects/classification/real_project_workload.py",
                        "--mode",
                        "prepare",
                        "--project",
                        str(case["project"]),
                        "--size",
                        str(size),
                        "--input",
                        f"/artifacts/{input_path.name}",
                        "--output",
                        f"/artifacts/prepare_{size}.json",
                    ],
                    limits=limits,
                    readonly_mounts=((PROJECT_ROOT / "subjects", "/subjects"),),
                )
                preparation.append(prepare_result.to_dict())
                if prepare_result.return_code != 0 or prepare_result.timed_out:
                    raise RuntimeError(
                        f"Preparation failed for {case_name}/{size}: "
                        f"{prepare_result.stderr}"
                    )

                result_path = case_dir / f"measure_{size}.json"
                result = evaluator.resource_test(
                    workspace,
                    (
                        sys.executable,
                        str(
                            PROJECT_ROOT
                            / "subjects/classification/real_project_workload.py"
                        ),
                        "--mode",
                        "measure",
                        "--project",
                        str(case["project"]),
                        "--size",
                        str(size),
                        "--input",
                        str(input_path),
                        "--output",
                        "{output}",
                    ),
                    result_path,
                )
                measurements.append(result.to_dict())
                if not result.passed:
                    raise RuntimeError(
                        f"Measurement failed for {case_name}/{size}: "
                        f"{result.command_result.stderr}"
                    )
                samples.append(PerformanceSample.from_mapping(result.to_dict()))

            classification = classify_performance_task(samples)
            expected_signal = str(case["expected_signal"])
            passed = classification.signals.get(expected_signal, False)
            all_passed = all_passed and passed
            summary["cases"][case_name] = {  # type: ignore[index]
                "project": case["project"],
                "version": case["version"],
                "source": case["source"],
                "workload_basis": case["workload_basis"],
                "sizes": list(case["sizes"]),
                "expected_signal": expected_signal,
                "actual_task_type": classification.task_type,
                "passed": passed,
                "classification": classification.to_dict(),
                "preparation": preparation,
                "measurements": measurements,
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
