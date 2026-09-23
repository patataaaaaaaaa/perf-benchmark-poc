#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.workload_freeze import freeze_workload_candidate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Freeze an automatically validated workload after explicit human review."
    )
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument(
        "--spec",
        type=Path,
        help="Candidate WorkloadSpec; defaults to testcase_derived/workload_spec.json",
    )
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--rationale", required=True)
    parser.add_argument(
        "--confirm-sha256",
        required=True,
        help="Exact script SHA-256 shown in the reviewed WorkloadSpec",
    )
    args = parser.parse_args()

    artifact_dir = args.artifacts.expanduser().resolve()
    if args.spec:
        spec_path = args.spec.expanduser().resolve()
    else:
        current = artifact_dir / "repository_derived" / "workload_spec.json"
        legacy = artifact_dir / "testcase_derived" / "workload_spec.json"
        spec_path = current if current.is_file() else legacy
    frozen = freeze_workload_candidate(
        artifact_dir=artifact_dir,
        spec_path=spec_path,
        confirmed_sha256=args.confirm_sha256,
        reviewer=args.reviewer,
        rationale=args.rationale,
    )
    print("[Frozen] human-confirmed workload created")
    print(f"Artifacts: {frozen}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Workload freeze failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
