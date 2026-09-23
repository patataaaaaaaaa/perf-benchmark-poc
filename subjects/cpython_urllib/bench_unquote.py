#!/usr/bin/env python3
from __future__ import annotations

import argparse

import pyperf

from _candidate import load_candidate


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--repeat-count", type=int, default=200_000)
    known, remaining = parser.parse_known_args()
    if known.repeat_count < 1:
        raise ValueError("--repeat-count must be positive")

    candidate = load_candidate()
    target = candidate.unquote_to_bytes
    text = "Ł%01š%20" * known.repeat_count
    expected_length = known.repeat_count * 6
    probe = target(text)
    if not isinstance(probe, bytes) or len(probe) != expected_length:
        raise AssertionError("unquote_to_bytes returned an unexpected result")

    runner = pyperf.Runner(_argparser=parser)
    runner.parse_args(remaining)
    runner.metadata["target_symbol"] = "urllib.parse.unquote_to_bytes"
    runner.metadata["input_characters"] = len(text)
    runner.bench_func("unquote_to_bytes_large", target, text)


if __name__ == "__main__":
    main()
