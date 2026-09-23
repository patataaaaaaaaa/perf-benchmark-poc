#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import psutil


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise ValueError("A command is required after --")

    started = time.perf_counter()
    process = subprocess.Popen(command)
    root = psutil.Process(process.pid)
    peak_rss = 0
    cpu: dict[int, tuple[float, float]] = {}
    io: dict[int, tuple[int, int, int, int]] = {}
    while process.poll() is None:
        try:
            processes = [root, *root.children(recursive=True)]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            processes = []
        current_rss = 0
        for item in processes:
            try:
                current_rss += int(item.memory_info().rss)
                times = item.cpu_times()
                old_cpu = cpu.get(item.pid, (0.0, 0.0))
                cpu[item.pid] = (
                    max(old_cpu[0], float(times.user)),
                    max(old_cpu[1], float(times.system)),
                )
                try:
                    counters = item.io_counters()
                except (psutil.AccessDenied, AttributeError, NotImplementedError):
                    continue
                old_io = io.get(item.pid, (0, 0, 0, 0))
                io[item.pid] = (
                    max(old_io[0], int(counters.read_bytes)),
                    max(old_io[1], int(counters.write_bytes)),
                    max(old_io[2], int(counters.read_count)),
                    max(old_io[3], int(counters.write_count)),
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                continue
        peak_rss = max(peak_rss, current_rss)
        time.sleep(0.02)
    return_code = process.wait()
    wall = time.perf_counter() - started
    user = sum(value[0] for value in cpu.values())
    system = sum(value[1] for value in cpu.values())
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(
        json.dumps(
            {
                "wall_seconds": wall,
                "user_cpu_seconds": user,
                "system_cpu_seconds": system,
                "cpu_to_wall_ratio": (user + system) / wall if wall else None,
                "peak_rss_bytes": peak_rss,
                "read_bytes": sum(value[0] for value in io.values()) if io else None,
                "write_bytes": sum(value[1] for value in io.values()) if io else None,
                "read_count": sum(value[2] for value in io.values()) if io else None,
                "write_count": sum(value[3] for value in io.values()) if io else None,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
