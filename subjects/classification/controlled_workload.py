from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
import tracemalloc
from pathlib import Path


def cpu_workload(size: int) -> int:
    value = 0
    for number in range(size):
        value = (value + number * number) % 1_000_000_007
    return value


def memory_workload(size_mib: int) -> int:
    block = bytearray(size_mib * 1024 * 1024)
    for offset in range(0, len(block), 4096):
        block[offset] = offset % 251
    time.sleep(0.25)
    return len(block)


def io_workload(size_mib: int) -> int:
    chunk = b"x" * (1024 * 1024)
    with tempfile.NamedTemporaryFile(prefix="perf-classifier-", delete=False) as stream:
        path = Path(stream.name)
        for _ in range(size_mib):
            stream.write(chunk)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        total = 0
        with path.open("rb") as stream:
            while data := stream.read(len(chunk)):
                total += len(data)
        time.sleep(0.25)
        return total
    finally:
        path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("cpu", "memory", "io"), required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    tracemalloc.start()
    if args.kind == "cpu":
        result = cpu_workload(args.size)
    elif args.kind == "memory":
        result = memory_workload(args.size)
    else:
        result = io_workload(args.size)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    args.output.write_text(
        json.dumps(
            {
                "tracemalloc_peak_bytes": peak,
                "workload": {
                    "kind": args.kind,
                    "input_size": args.size,
                    "result": result,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
