#!/usr/bin/env python3
"""Stable timing harness for the same scenario used during hotspot discovery."""

from __future__ import annotations

import argparse
import sys
from collections import deque
from itertools import repeat
from pathlib import Path

import pyperf


def run_workload(triplewise, size: int) -> None:
    last = deque(triplewise(repeat(None, size)), maxlen=1)
    if len(last) != 1 or last[0] != (None, None, None):
        raise AssertionError("triplewise workload produced an unexpected result")


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--size", type=int, default=1_000_000)
    known, remaining = parser.parse_known_args()
    if known.size < 3:
        raise ValueError("size must be at least 3")

    sys.path.insert(0, str(Path.cwd()))
    from more_itertools import triplewise

    # Check the scenario once outside the timed samples.
    run_workload(triplewise, known.size)

    sys.argv = [sys.argv[0], *remaining]
    runner = pyperf.Runner()
    runner.metadata["workload_kind"] = "original_hotspot_discovery_scenario"
    runner.metadata["input_size"] = known.size
    runner.bench_func("original_triplewise_workload", run_workload, triplewise, known.size)


if __name__ == "__main__":
    main()
