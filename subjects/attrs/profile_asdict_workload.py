#!/usr/bin/env python3
"""Repository-benchmark-derived reference workload for attrs.asdict."""

from __future__ import annotations

import sys
from pathlib import Path


# attrs uses the standard src/ layout. The controller also sets PYTHONPATH in
# Docker, while this makes direct local replay deterministic.
sys.path.insert(0, str(Path.cwd() / "src"))

import attrs  # noqa: E402


@attrs.define
class AtomicFields:
    a: int = 0
    b: Ellipsis = ...
    c: str = "foo"
    d: tuple[str] = "bar"
    e: complex = complex()


def main() -> None:
    instance = AtomicFields()
    expected = {"a": 0, "b": ..., "c": "foo", "d": "bar", "e": 0j}
    result = None
    # The repository benchmark uses the same class and operation with 1,000
    # rounds. Scale only the repeat count so cProfile has enough signal.
    for _ in range(100_000):
        result = attrs.asdict(instance)
    if result != expected:
        raise AssertionError(f"attrs.asdict returned an unexpected result: {result!r}")


if __name__ == "__main__":
    main()
