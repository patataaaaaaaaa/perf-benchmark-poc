#!/usr/bin/env python3
"""Controlled workload for validating automatic hotspot discovery.

This script intentionally names only the public operation used by the scenario.
It contains no profiler ranking or source-location hint.
"""

from __future__ import annotations

import argparse
import sys
from collections import deque
from itertools import repeat
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=1_000_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.size < 3:
        raise ValueError("size must be at least 3")

    # The command is run with the checked-out repository as cwd. Inserting it
    # ensures this workload imports that checkout rather than an installed copy.
    sys.path.insert(0, str(Path.cwd()))
    from more_itertools import triplewise

    last = deque(triplewise(repeat(None, args.size)), maxlen=1)
    if len(last) != 1 or last[0] != (None, None, None):
        raise AssertionError("triplewise workload produced an unexpected result")


if __name__ == "__main__":
    main()
