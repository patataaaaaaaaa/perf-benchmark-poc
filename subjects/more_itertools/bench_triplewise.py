#!/usr/bin/env python3
from __future__ import annotations

import sys
from collections import deque
from itertools import repeat
from pathlib import Path
from time import perf_counter

import pyperf


REPOSITORY = Path.cwd().resolve()
sys.path.insert(0, str(REPOSITORY))

from more_itertools.recipes import triplewise  # noqa: E402


CONSUME = deque(maxlen=0).extend


def bench_triplewise(loops: int, size: int) -> float:
    started = perf_counter()
    for _ in range(loops):
        CONSUME(triplewise(repeat(None, size)))
    return perf_counter() - started


def main() -> None:
    runner = pyperf.Runner()
    runner.metadata["target_symbol"] = "more_itertools.recipes.triplewise"
    runner.metadata["target_source"] = str(
        Path(sys.modules[triplewise.__module__].__file__).resolve()
    )
    runner.bench_time_func("triplewise_small", bench_triplewise, 100)
    runner.bench_time_func("triplewise_medium", bench_triplewise, 10_000)
    runner.bench_time_func("triplewise_large", bench_triplewise, 1_000_000)


if __name__ == "__main__":
    main()
