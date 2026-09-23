#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute one frozen generated workload without pyperf orchestration."
    )
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--primary", required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(Path.cwd()))
    spec = importlib.util.spec_from_file_location(
        "_frozen_generated_workload", args.benchmark.resolve()
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load generated workload")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    callback, expected = module.get_cases()[args.primary]
    result = callback()
    if result != expected:
        raise AssertionError(
            f"Generated workload returned {result!r}, expected {expected!r}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
