#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import build_pipeline, load_selected_targets  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate, validate, and repair SymPy pyperf benchmarks."
    )
    parser.add_argument(
        "--target",
        help="Run only the target with this id; by default all configured targets run.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        help="Override experiment.max_retries from config/config.yaml.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load targets and render prompts without calling DeepSeek.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="Repeat the complete target set this many times (default: 1).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_retries is not None and args.max_retries < 0:
        print("--max-retries must be zero or greater", file=sys.stderr)
        return 2
    if args.repetitions < 1:
        print("--repetitions must be one or greater", file=sys.stderr)
        return 2

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        targets = load_selected_targets(
            PROJECT_ROOT / "subjects" / "experiment_targets.json",
            args.target,
        )
        pipeline = build_pipeline(
            project_root=PROJECT_ROOT,
            config_path=PROJECT_ROOT / "config" / "config.yaml",
            dry_run=args.dry_run,
            max_retries_override=args.max_retries,
        )
        run_dirs = [pipeline.run(targets) for _ in range(args.repetitions)]
    except Exception as exc:
        print(f"POC failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    for run_dir in run_dirs:
        print(f"Artifacts: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
