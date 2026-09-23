#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import tracemalloc
from pathlib import Path

from _candidate import load_candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeat-count", type=int, default=200_000)
    args = parser.parse_args()
    if args.repeat_count < 1:
        raise ValueError("--repeat-count must be positive")

    target = load_candidate().unquote_to_bytes
    text = "Ł%01š%20" * args.repeat_count
    tracemalloc.start(10)
    started = time.perf_counter()
    result = target(text)
    elapsed = time.perf_counter() - started
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    expected_length = args.repeat_count * 6
    if not isinstance(result, bytes) or len(result) != expected_length:
        raise AssertionError("unquote_to_bytes returned an unexpected result")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "tracemalloc_current_bytes": current,
                "tracemalloc_peak_bytes": peak,
                "elapsed_seconds": elapsed,
                "workload": {
                    "input_size": len(text),
                    "repeat_count": args.repeat_count,
                    "expected_output_length": expected_length,
                    "target_symbol": "urllib.parse.unquote_to_bytes",
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
