#!/usr/bin/env python3
"""Controlled end-user scenario for automatic CPU hotspot discovery.

The script names the public operation used by the scenario, but contains no
source-file location or profiler ranking hint.  cProfile is started by the
framework around this script.
"""

from __future__ import annotations

import argparse

from _candidate import load_candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat-count", type=int, default=200_000)
    parser.add_argument("--iterations", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.repeat_count < 1 or args.iterations < 1:
        raise ValueError("repeat-count and iterations must be positive")

    operation = load_candidate().unquote_to_bytes
    encoded = "Ł%01š%20" * args.repeat_count
    expected_length = args.repeat_count * 6
    for _ in range(args.iterations):
        result = operation(encoded)
        if not isinstance(result, bytes) or len(result) != expected_length:
            raise AssertionError("unquote_to_bytes returned an unexpected result")


if __name__ == "__main__":
    main()
