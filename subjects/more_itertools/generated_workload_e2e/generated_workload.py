import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from more_itertools.recipes import triplewise
import pyperf

TARGET_SYMBOL = "more_itertools.recipes.triplewise"

WORKLOAD_DESCRIPTION = (
    "Consume triplewise on fresh range iterators of 10, 10_000, and 100_000 "
    "integers; return the sum of all triplet sums plus the triplet count."
)

PRIMARY_BENCHMARK = "large_range_100000"

SMALL_N = 10
MEDIUM_N = 10_000
LARGE_N = 100_000


def expected_checksum(n):
    count = n - 2
    total = 3 * (n - 2) * (n - 1) // 2
    return total + count


def _consume_triples(n):
    total = 0
    count = 0
    for a, b, c in triplewise(iter(range(n))):
        total += a + b + c
        count += 1
    return total + count


def bench_small_range():
    return _consume_triples(SMALL_N)


def bench_medium_range():
    return _consume_triples(MEDIUM_N)


def bench_large_range():
    return _consume_triples(LARGE_N)


def get_cases():
    return {
        "small_range_10": (bench_small_range, expected_checksum(SMALL_N)),
        "medium_range_10000": (bench_medium_range, expected_checksum(MEDIUM_N)),
        "large_range_100000": (bench_large_range, expected_checksum(LARGE_N)),
    }


def main():
    runner = pyperf.Runner()
    for name, (func, _expected) in get_cases().items():
        runner.bench_func(name, func)


if __name__ == "__main__":
    main()
