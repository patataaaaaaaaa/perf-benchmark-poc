#!/usr/bin/env python3
"""Apply one accepted release candidate to an explicit review branch.

This command never merges or pushes. It requires a clean repository at the
recorded baseline, applies the exact tested patch, and reruns functional gates
inside the configured Docker sandbox before leaving the branch for review.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.config import FrameworkConfig  # noqa: E402
from src.framework.evaluator import Evaluator  # noqa: E402
from src.framework.generated_benchmark import sha256_file  # noqa: E402
from src.framework.patching import apply_safe_patch  # noqa: E402
from src.framework.sandbox import SandboxLimits  # noqa: E402


def git(repository: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repository, text=True, capture_output=True, check=False
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--target-repository", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--branch", required=True, help="New review branch name")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually create the branch and apply the patch; omission is preflight only",
    )
    args = parser.parse_args()

    artifacts = args.artifacts.expanduser().resolve()
    target = args.target_repository.expanduser().resolve()
    release_dir = artifacts / "release_candidate"
    manifest_path = release_dir / "manifest.json"
    patch_path = release_dir / "best.patch"
    if not manifest_path.is_file() or not patch_path.is_file():
        raise FileNotFoundError("release_candidate/manifest.json or best.patch is missing")
    release = json.loads(manifest_path.read_text(encoding="utf-8"))
    if release.get("status") != "READY_FOR_REVIEW":
        raise RuntimeError(f"Release candidate is not publishable: {release.get('status')}")
    if sha256_file(patch_path) != release.get("patch_sha256"):
        raise RuntimeError("Release candidate patch hash mismatch")
    if not (target / ".git").exists():
        raise ValueError(f"Target is not a Git repository: {target}")
    if git(target, "status", "--porcelain"):
        raise RuntimeError("Target repository must be clean before promotion")
    head = git(target, "rev-parse", "HEAD")
    expected = str(release["baseline_commit"])
    if head != expected:
        raise RuntimeError(f"Target HEAD {head} does not match baseline {expected}")
    if git(target, "show-ref", "--verify", f"refs/heads/{args.branch}", check=False):
        raise RuntimeError(f"Branch already exists: {args.branch}")

    print("[Promotion Preflight] PASS")
    print(f"  target={target}")
    print(f"  baseline={head}")
    print(f"  patch_sha256={release['patch_sha256']}")
    if not args.apply:
        print("[Dry Run] add --apply to create the review branch and rerun tests")
        return 0

    config = FrameworkConfig.load(args.config, PROJECT_ROOT)
    execution = config.execution_sandbox
    if execution is None:
        raise ValueError("Promotion requires execution_sandbox")
    target_file = Path(str(release["target_file"]))
    target_symbol = str(release["target_symbol"])
    python = config.targeted_test_command[0]
    evaluator = Evaluator(
        config.timeout_seconds,
        docker_image=execution.image,
        project_root=PROJECT_ROOT,
        sandbox_limits=SandboxLimits(
            cpus=execution.cpus,
            memory=execution.memory,
            pids=execution.pids,
            timeout_seconds=execution.timeout_seconds,
            max_output_bytes=execution.max_output_bytes,
        ),
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = artifacts / "promotion" / stamp
    original_branch = git(target, "symbolic-ref", "--short", "-q", "HEAD", check=False)
    created = False
    try:
        git(target, "switch", "-c", args.branch)
        created = True
        apply_safe_patch(target, patch_path.read_text(encoding="utf-8"), (target_file,))
        module, symbol = target_symbol.rsplit(".", 1)
        commands = [
            (
                "syntax",
                (
                    python,
                    "-c",
                    "import pathlib,sys; p=pathlib.Path(sys.argv[1]); "
                    "compile(p.read_text(encoding='utf-8'), str(p), 'exec')",
                    str(target_file),
                ),
            ),
            ("import", (python, "-c", f"from {module} import {symbol}")),
            ("targeted_tests", config.targeted_test_command),
            ("full_tests", config.full_test_command),
        ]
        if config.invariant_test_command:
            commands.append(("invariants_and_target_hit", config.invariant_test_command))
        results = {}
        for name, command in commands:
            print(f"[Promotion Test] {name}", flush=True)
            result = evaluator.functional_test(target, command, output / name)
            results[name] = result.to_dict()
            if not result.passed:
                raise RuntimeError(f"Promotion test failed: {name}")
        git(target, "diff", "--check")
        write_json(
            output / "promotion.json",
            {
                "status": "READY_TO_COMMIT",
                "branch": args.branch,
                "baseline_commit": head,
                "patch_sha256": release["patch_sha256"],
                "tests": results,
                "automatic_merge": False,
                "automatic_push": False,
            },
        )
    except Exception:
        if created:
            git(target, "reset", "--hard", head, check=False)
            if original_branch:
                git(target, "switch", original_branch, check=False)
            else:
                git(target, "checkout", "--detach", head, check=False)
            git(target, "branch", "-D", args.branch, check=False)
        raise

    print(f"[Promotion Complete] branch={args.branch}")
    print("The patch is tested and ready for human review/commit; it was not merged or pushed.")
    print(f"Artifacts: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
