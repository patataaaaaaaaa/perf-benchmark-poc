from __future__ import annotations

import sys
from pathlib import Path

import pyperf


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from demo_subject.workload import center_values  # noqa: E402


VALUES = tuple(float(value) for value in range(2_000))


def main() -> None:
    runner = pyperf.Runner()
    runner.bench_func("center_values", center_values, VALUES)


if __name__ == "__main__":
    main()

