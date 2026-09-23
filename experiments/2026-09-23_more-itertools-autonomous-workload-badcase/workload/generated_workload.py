import sys
from pathlib import Path

# Make repository code importable when the workload runs from the repo root.
sys.path.insert(0, str(Path.cwd()))

import pyperf
import more_itertools as mi


SOURCE_EVIDENCE = ("tests/test_more.py",)
WORKLOAD_DESCRIPTION = (
    "Benchmark deterministic more_itertools.peekable operations: indexing, "
    "slicing, and large prepend consumption over in-memory iterables."
)
SELECTION_RATIONALE = (
    "PeekableTests exercises core peekable/prepend behavior with many "
    "assertions and no randomness, sleeps, filesystem, or network access. "
    "The workload scales input sizes while preserving the original test "
    "operation structure."
)
PRIMARY_BENCHMARK = "peekable_indexing"


# Workload sizes.
INDEX_N = 20_000
SLICE_N = 20_000
PREPEND_N = 20_000

# Deterministic return values for the completed iterations.
EXPECTED_INDEXING = INDEX_N
EXPECTED_SLICING = SLICE_N + 50_109  # 70_109 for the default SLICE_N
EXPECTED_PREPEND = PREPEND_N + 5


def bench_peekable_indexing():
    """Scaled version of PeekableTests.test_indexing.

    Returns the number of items consumed, which is ``INDEX_N``.
    """
    n = INDEX_N
    p = mi.peekable(range(n))

    # Indexing should not advance the iterator.
    _ = p[0]
    _ = next(p)
    count = 1

    _ = p[2]
    _ = next(p)
    count += 1

    _ = p[0]
    _ = p[n - 3]

    _ = next(p)
    count += 1

    _ = p[n - 4]
    _ = p[-2]
    _ = p[-9]

    # Fully consume the remaining lazy/peekable state.
    for _ in p:
        count += 1

    return count


def bench_peekable_slicing():
    """Scaled version of PeekableTests.test_slicing.

    Returns the total number of elements observed in slice results and final
    consumption.
    """
    n = SLICE_N
    seq = list(range(n))
    p = mi.peekable(seq)

    count = 0

    # Pre-advance slices.
    count += len(p[1:4])

    # Advancing the iterator moves slices up also.
    _ = next(p)
    count += 1

    # Mirrors the slice set used in the original test.
    count += len(p[1:4])
    count += len(p[:5])
    count += len(p[:])
    count += len(p[:100])
    count += len(p[::2])
    count += len(p[::-1])

    # Fully consume the rest of the peekable.
    for _ in p:
        count += 1

    return count


def bench_prepend_many():
    """Scaled version of PeekableTests.test_prepend_many.

    Returns the number of items produced after prepending many elements.
    """
    n = PREPEND_N
    it = mi.peekable(range(5))

    # Avoid direct use of range() for the prepended values, mirroring the
    # original test's generator expression.
    it.prepend(*(x for x in range(n)))

    count = 0
    for _ in it:
        count += 1

    return count


def get_cases():
    return {
        "peekable_indexing": (bench_peekable_indexing, EXPECTED_INDEXING),
        "peekable_slicing": (bench_peekable_slicing, EXPECTED_SLICING),
        "prepend_many": (bench_prepend_many, EXPECTED_PREPEND),
    }


def main():
    runner = pyperf.Runner()
    for name, (func, _expected) in get_cases().items():
        runner.bench_func(name, func)


if __name__ == "__main__":
    main()
