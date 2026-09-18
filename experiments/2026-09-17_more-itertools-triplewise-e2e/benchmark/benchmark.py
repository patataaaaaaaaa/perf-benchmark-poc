import sys
from pathlib import Path

import pyperf

# Ensure the local repository root is importable before importing the target.
sys.path.insert(0, str(Path.cwd()))

from more_itertools.recipes import triplewise

TARGET_SYMBOL = 'more_itertools.recipes.triplewise'
WORKLOAD_DESCRIPTION = (
    "Fresh one-shot iterators: a list of 10 ints, a range of 2,000 ints, "
    "and a range of 200,000 ints. Each workload counts all triplets yielded by triplewise."
)
PRIMARY_BENCHMARK = 'large_range_200000'


def _count_triplets(iterable):
    return sum(1 for _ in triplewise(iterable))


def _small_list_10():
    iterable = iter([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    return _count_triplets(iterable)


def _medium_range_2000():
    iterable = iter(range(2_000))
    return _count_triplets(iterable)


def _large_range_200000():
    iterable = iter(range(200_000))
    return _count_triplets(iterable)


def get_cases():
    return {
        'small_list_10': (_small_list_10, 8),
        'medium_range_2000': (_medium_range_2000, 1998),
        'large_range_200000': (_large_range_200000, 199_998),
    }


def main():
    runner = pyperf.Runner()
    for name, (func, _expected) in get_cases().items():
        runner.bench_func(name, func)


if __name__ == '__main__':
    main()
