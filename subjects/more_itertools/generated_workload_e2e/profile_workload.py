"""Profile only the callback of the experiment-locked generated workload."""

from __future__ import annotations

import cProfile

import generated_workload


def main() -> None:
    callback, expected = generated_workload.get_cases()[
        generated_workload.PRIMARY_BENCHMARK
    ]
    warmup = callback()
    if warmup != expected:
        raise AssertionError(f"warmup returned {warmup!r}, expected {expected!r}")

    profiler = cProfile.Profile()
    actual = profiler.runcall(callback)
    if actual != expected:
        raise AssertionError(f"workload returned {actual!r}, expected {expected!r}")
    profiler.dump_stats("/artifacts/profile.prof")


if __name__ == "__main__":
    main()
