#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import tracemalloc
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--primary", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    spec = importlib.util.spec_from_file_location(
        "_generated_resource_benchmark", args.benchmark.resolve()
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load generated benchmark")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    callback, expected = module.get_cases()[args.primary]

    tracemalloc.start()
    result = callback()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if result != expected:
        raise AssertionError(f"Resource workload returned {result!r}, expected {expected!r}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "tracemalloc_peak_bytes": peak,
                "workload": {
                    "primary_benchmark": args.primary,
                    "expected_result": expected,
                    "workload_description": module.WORKLOAD_DESCRIPTION,
                    "target_symbol": module.TARGET_SYMBOL,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
