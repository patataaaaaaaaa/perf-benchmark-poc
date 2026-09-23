#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
import subprocess
import sys
import time
import tracemalloc
import urllib.parse as reference_parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


BASELINE_COMMIT = "1bb68ba6d9de6bb7f00aee11d135123163f15887"
HUMAN_FIX_COMMIT = "2e279e85fece187b6058718ac7e82d1692461e26"
RAW_TEMPLATE = "https://raw.githubusercontent.com/python/cpython/{commit}/Lib/urllib/parse.py"
PRIMARY_CASE = "unquote_to_bytes"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_source(commit: str, destination: Path, retries: int = 3) -> None:
    url = RAW_TEMPLATE.format(commit=commit)
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                payload = response.read()
            compile(payload, str(destination), "exec")
            temporary = destination.with_suffix(".tmp")
            temporary.write_bytes(payload)
            temporary.replace(destination)
            return
        except Exception as exc:  # Network failures are preserved in the log.
            last_error = exc
            if attempt < retries:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Unable to download {url}: {last_error}")


def stage_source(source: Path, destination: Path) -> None:
    """Copy a pre-fetched source file into the immutable experiment artifacts."""
    if not source.is_file():
        raise FileNotFoundError(f"Source file does not exist: {source}")
    payload = source.read_bytes()
    compile(payload, str(source), "exec")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_bytes(payload)
    temporary.replace(destination)


def load_candidate(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("candidate_urllib_parse", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load candidate module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def worker(source: Path, case: str, repeat_count: int) -> int:
    candidate = load_candidate(source)
    text = "Ł%01š%20" * repeat_count
    if case == "unquote_to_bytes":
        argument: str | bytes = text
        expected = reference_parse.unquote_to_bytes(argument)
        callback = candidate.unquote_to_bytes
    elif case == "unquote":
        argument = text
        expected = reference_parse.unquote(argument)
        callback = candidate.unquote
    else:
        raise ValueError(f"Unknown case: {case}")

    tracemalloc.start(10)
    started = time.perf_counter()
    result = callback(argument)
    elapsed = time.perf_counter() - started
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    passed = result == expected
    payload = {
        "case": case,
        "passed": passed,
        "input_characters": len(text),
        "result_length": len(result),
        "elapsed_seconds": elapsed,
        "tracemalloc_current_bytes": current_bytes,
        "tracemalloc_peak_bytes": peak_bytes,
        "tracemalloc_overhead_bytes": max(0, peak_bytes - current_bytes),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if passed else 1


def run_worker(
    script: Path, source: Path, case: str, repeat_count: int
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(script),
        "--worker",
        "--source",
        str(source),
        "--case",
        case,
        "--repeat-count",
        str(repeat_count),
    ]
    result = subprocess.run(command, text=True, capture_output=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(
            f"Worker failed ({result.returncode}): {result.stderr or result.stdout}"
        )
    return json.loads(result.stdout)


def summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "passed": all(bool(item["passed"]) for item in samples),
        "sample_count": len(samples),
        "median_seconds": statistics.median(
            float(item["elapsed_seconds"]) for item in samples
        ),
        "median_peak_bytes": statistics.median(
            int(item["tracemalloc_peak_bytes"]) for item in samples
        ),
        "median_overhead_bytes": statistics.median(
            int(item["tracemalloc_overhead_bytes"]) for item in samples
        ),
        "samples": samples,
    }


def percent_reduction(baseline: float, candidate: float) -> float:
    if baseline <= 0:
        raise ValueError("Baseline must be positive")
    return 100.0 * (baseline - candidate) / baseline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the historical CPython urllib unquote memory task."
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--repeat-count", type=int, default=200_000)
    parser.add_argument("--min-memory-reduction-percent", type=float, default=30.0)
    parser.add_argument("--max-runtime-regression-percent", type=float, default=25.0)
    parser.add_argument(
        "--baseline-source",
        type=Path,
        help="Pre-fetched baseline parse.py; must be used with --human-source.",
    )
    parser.add_argument(
        "--human-source",
        type=Path,
        help="Pre-fetched human-fix parse.py; must be used with --baseline-source.",
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--source", type=Path, help=argparse.SUPPRESS)
    parser.add_argument(
        "--case", choices=("unquote", "unquote_to_bytes"), help=argparse.SUPPRESS
    )
    args = parser.parse_args()

    if args.worker:
        if args.source is None or args.case is None:
            parser.error("--worker requires --source and --case")
        return worker(args.source, args.case, args.repeat_count)
    if args.repetitions < 1 or args.repeat_count < 1:
        parser.error("repetitions and repeat-count must be positive")
    if (args.baseline_source is None) != (args.human_source is None):
        parser.error("--baseline-source and --human-source must be provided together")

    project_root = Path(__file__).resolve().parents[1]
    output = args.output or (
        project_root
        / "artifacts"
        / "urllib_memory_feasibility"
        / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    output.mkdir(parents=True, exist_ok=False)
    sources = output / "sources"
    baseline_source = sources / "baseline_parse.py"
    human_source = sources / "human_fix_parse.py"
    if args.baseline_source is not None and args.human_source is not None:
        stage_source(args.baseline_source, baseline_source)
        stage_source(args.human_source, human_source)
        source_mode = "pre_fetched"
    else:
        download_source(BASELINE_COMMIT, baseline_source)
        download_source(HUMAN_FIX_COMMIT, human_source)
        source_mode = "downloaded"

    script = Path(__file__).resolve()
    versions = {"baseline": baseline_source, "human_fix": human_source}
    results: dict[str, dict[str, Any]] = {}
    for version, source in versions.items():
        results[version] = {}
        for case in ("unquote", "unquote_to_bytes"):
            samples = [
                run_worker(script, source, case, args.repeat_count)
                for _ in range(args.repetitions)
            ]
            results[version][case] = summarize(samples)

    baseline = results["baseline"][PRIMARY_CASE]
    human = results["human_fix"][PRIMARY_CASE]
    memory_reduction = percent_reduction(
        float(baseline["median_peak_bytes"]), float(human["median_peak_bytes"])
    )
    runtime_change = percent_reduction(
        float(baseline["median_seconds"]), float(human["median_seconds"])
    )
    passed = (
        bool(baseline["passed"])
        and bool(human["passed"])
        and memory_reduction >= args.min_memory_reduction_percent
        and runtime_change >= -args.max_runtime_regression_percent
    )
    summary = {
        "status": "PASS" if passed else "FAIL",
        "task": "cpython_urllib_unquote_memory",
        "repository_url": "https://github.com/python/cpython.git",
        "issue_url": "https://github.com/python/cpython/issues/88500",
        "pull_request_url": "https://github.com/python/cpython/pull/96763",
        "baseline_commit": BASELINE_COMMIT,
        "human_fix_commit": HUMAN_FIX_COMMIT,
        "source_mode": source_mode,
        "primary_case": PRIMARY_CASE,
        "repeat_count": args.repeat_count,
        "repetitions": args.repetitions,
        "source_sha256": {
            "baseline": sha256(baseline_source),
            "human_fix": sha256(human_source),
        },
        "thresholds": {
            "min_memory_reduction_percent": args.min_memory_reduction_percent,
            "max_runtime_regression_percent": args.max_runtime_regression_percent,
        },
        "primary_comparison": {
            "memory_reduction_percent": memory_reduction,
            "runtime_speedup_percent": runtime_change,
        },
        "results": results,
    }
    write_json(output / "summary.json", summary)
    report = [
        "# CPython urllib 内存任务可行性报告",
        "",
        f"- 结论：`{summary['status']}`",
        f"- Baseline：`{BASELINE_COMMIT}`",
        f"- Human Fix：`{HUMAN_FIX_COMMIT}`",
        f"- 主 workload：`{PRIMARY_CASE}`，输入重复 {args.repeat_count:,} 次",
        f"- Baseline 峰值中位数：{baseline['median_peak_bytes']:.0f} bytes",
        f"- Human Fix 峰值中位数：{human['median_peak_bytes']:.0f} bytes",
        f"- 峰值内存下降：{memory_reduction:.2f}%",
        f"- 运行时间变化：{runtime_change:.2f}%（负数表示变慢）",
        "",
        "该脚本不调用 LLM，只验证固定官方提交是否适合作为正式内存闭环任务。",
    ]
    (output / "REPORT_ZH.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Status: {summary['status']}")
    print(f"Artifacts: {output}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
