#!/usr/bin/env python3
from __future__ import annotations

import argparse
import cProfile
import importlib.util
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile only a generated workload callback, excluding setup/import."
    )
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--primary", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(Path.cwd()))
    spec = importlib.util.spec_from_file_location(
        "_profiled_generated_workload", args.benchmark.resolve()
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load generated workload")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    callback, expected = module.get_cases()[args.primary]
    warmup = callback()
    if warmup != expected:
        raise AssertionError(
            f"Generated workload warmup returned {warmup!r}, expected {expected!r}"
        )

    profiler = cProfile.Profile()
    result = profiler.runcall(callback)
    if result != expected:
        raise AssertionError(
            f"Generated workload returned {result!r}, expected {expected!r}"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    profiler.dump_stats(str(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
