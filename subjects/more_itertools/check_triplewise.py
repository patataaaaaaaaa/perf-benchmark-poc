#!/usr/bin/env python3
from __future__ import annotations

import inspect
import sys
from pathlib import Path


REPOSITORY = Path.cwd().resolve()
sys.path.insert(0, str(REPOSITORY))

from more_itertools.recipes import triplewise  # noqa: E402


def check_behavior() -> None:
    cases = [
        ([], []),
        ([0], []),
        ([0, 1], []),
        ([0, 1, 2], [(0, 1, 2)]),
        ([0, 1, 2, 3], [(0, 1, 2), (1, 2, 3)]),
    ]
    for values, expected in cases:
        assert list(triplewise(values)) == expected
        assert list(triplewise(iter(values))) == expected


def check_single_pass_consumption() -> None:
    consumed: list[int] = []

    def source():
        for value in range(5):
            consumed.append(value)
            yield value

    result = iter(triplewise(source()))
    assert next(result) == (0, 1, 2)
    assert consumed == [0, 1, 2]
    assert next(result) == (1, 2, 3)
    assert consumed == [0, 1, 2, 3]


def check_dynamic_target_hit() -> None:
    hit = False
    target_code = triplewise.__code__

    def profiler(frame, event, arg):  # type: ignore[no-untyped-def]
        nonlocal hit
        if event == "call" and frame.f_code is target_code:
            hit = True
        return profiler

    sys.setprofile(profiler)
    try:
        list(triplewise(range(5)))
    finally:
        sys.setprofile(None)
    assert hit, "dynamic target-hit validation did not observe triplewise()"
    source = Path(inspect.getsourcefile(triplewise) or "").resolve()
    assert source.is_relative_to(REPOSITORY), (
        f"target imported from {source}, not the checked-out repository {REPOSITORY}"
    )


if __name__ == "__main__":
    check_behavior()
    check_single_pass_consumption()
    check_dynamic_target_hit()
    print("triplewise invariants and dynamic target hit: PASS")
