#!/usr/bin/env python3
from __future__ import annotations

import inspect
import sys
from pathlib import Path

from _candidate import load_candidate


def main() -> int:
    repository = Path.cwd().resolve()
    target = load_candidate().unquote_to_bytes
    cases: tuple[tuple[str | bytes, bytes], ...] = (
        ("", b""),
        (b"", b""),
        ("abc%20def", b"abc def"),
        (b"abc%2Fdef", b"abc/def"),
        ("Ł%20", "Ł ".encode()),
        ("%zz%", b"%zz%"),
        ("%01", b"\x01"),
    )
    for value, expected in cases:
        actual = target(value)
        if actual != expected or not isinstance(actual, bytes):
            raise AssertionError(f"Unexpected result for {value!r}: {actual!r}")

    hit = False
    code = target.__code__

    def profiler(frame, event, arg):  # type: ignore[no-untyped-def]
        nonlocal hit
        if event == "call" and frame.f_code is code:
            hit = True
        return profiler

    sys.setprofile(profiler)
    try:
        target("dynamic%20hit")
    finally:
        sys.setprofile(None)
    if not hit:
        raise AssertionError("Dynamic target-hit validation did not observe the target")
    source = Path(inspect.getsourcefile(target) or "").resolve()
    if not source.is_relative_to(repository):
        raise AssertionError(f"Target imported from {source}, not {repository}")
    print("urllib behavior and dynamic target hit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
