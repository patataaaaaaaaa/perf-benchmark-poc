#!/usr/bin/env python3
"""Merge the three valid parameter pairs and reject partial JMH runs."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


PAIRS = ((0, 1), (0, 2), (2, 1))
BENCHMARK = "org.roaringbitmap.longlong.ShiftLeftFromSpecifiedPositionBenchmark"


def validate_and_merge(artifacts: Path) -> list[dict]:
    merged: list[dict] = []
    for pos, count in PAIRS:
        path = artifacts / f"jmh-pos{pos}-count{count}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or len(data) != 2:
            raise ValueError(f"expected two benchmark results in {path}")
        found = set()
        for result in data:
            name = result.get("benchmark")
            params = result.get("params") or {}
            score = (result.get("primaryMetric") or {}).get("score")
            if (
                name not in {f"{BENCHMARK}.original", f"{BENCHMARK}.optimized"}
                or params.get("pos") != str(pos)
                or params.get("count") != str(count)
                or not isinstance(score, (int, float))
                or not math.isfinite(score)
                or score <= 0
            ):
                raise ValueError(f"unexpected or invalid JMH result in {path}: {result}")
            found.add(name)
        if found != {f"{BENCHMARK}.original", f"{BENCHMARK}.optimized"}:
            raise ValueError(f"missing original or optimized result in {path}")
        merged.extend(data)
    return merged


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_roaringbitmap_34bce1b_jmh.py ARTIFACTS_DIR", file=sys.stderr)
        return 2
    artifacts = Path(sys.argv[1])
    try:
        merged = validate_and_merge(artifacts)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"JMH validation failed: {exc}", file=sys.stderr)
        return 1
    (artifacts / "jmh.json").write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Validated {len(merged)} JMH results across {len(PAIRS)} parameter pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
