#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tracemalloc
from collections import deque
from itertools import repeat
from pathlib import Path


REPOSITORY = Path.cwd().resolve()
sys.path.insert(0, str(REPOSITORY))

from more_itertools.recipes import triplewise  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=1_000_000)
    parser.add_argument("--cpu", type=int)
    args = parser.parse_args()

    if args.cpu is not None and hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, {args.cpu})

    tracemalloc.start()
    deque(triplewise(repeat(None, args.size)), maxlen=0)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    payload = {
        "tracemalloc_current_bytes": current,
        "tracemalloc_peak_bytes": peak,
        "workload": {
            "input_size": args.size,
            "expected_output_count": max(0, args.size - 2),
            "target_symbol": "more_itertools.recipes.triplewise",
            "requested_cpu": args.cpu,
            "target_source": str(
                Path(sys.modules[triplewise.__module__].__file__).resolve()
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
