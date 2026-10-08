#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.benchllmrealse.codex_cli import (  # noqa: E402
    BenchLLMPerfOptTask,
    CodexCLIConfig,
    CodexCLIRunner,
    CodexRunResult,
)


def _command(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    parsed = tuple(shlex.split(value))
    if not parsed:
        raise argparse.ArgumentTypeError("command must not be empty")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Codex CLI as the coding agent for one BenchLLMRealSE PerfOpt task. "
            "The target workspace must already be a clean checkout of the buggy revision."
        )
    )
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--commit-id", required=True)
    parser.add_argument("--prompt-number", type=int, default=1)
    parser.add_argument(
        "--model",
        default=os.environ.get("CODEX_BENCH_MODEL"),
        required=os.environ.get("CODEX_BENCH_MODEL") is None,
        help="Exact DeepSeek model identifier; also read from CODEX_BENCH_MODEL.",
    )
    parser.add_argument(
        "--profile",
        default=os.environ.get("CODEX_BENCH_PROFILE"),
        help="Optional Codex config profile that selects the DeepSeek provider.",
    )
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--codex", default="codex", help="Codex CLI executable")
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    parser.add_argument("--command-timeout-seconds", type=int, default=1200)
    parser.add_argument(
        "--verification-command",
        help="Authoritative build/test command, parsed without a shell.",
    )
    parser.add_argument(
        "--benchmark-command",
        help="Authoritative JMH command, parsed without a shell and run after verification.",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        help="Output directory; defaults under artifacts/benchllmrealse/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate task paths and print the planned run without invoking Codex.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    task = BenchLLMPerfOptTask.load(
        args.benchmark_root,
        args.repo_name,
        args.commit_id,
        args.prompt_number,
    )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifacts_dir = args.artifacts_dir or (
        PROJECT_ROOT
        / "artifacts"
        / "benchllmrealse"
        / args.repo_name
        / args.commit_id
        / f"prompt{args.prompt_number}-{stamp}"
    )
    config = CodexCLIConfig(
        executable=args.codex,
        model=args.model,
        profile=args.profile,
        reasoning_effort=args.reasoning_effort,
        timeout_seconds=args.timeout_seconds,
        command_timeout_seconds=args.command_timeout_seconds,
    )
    runner = CodexCLIRunner(config)

    if args.dry_run:
        try:
            checked = runner.preflight(
                workspace=args.workspace,
                allowed_paths=task.source_paths,
                artifacts_dir=artifacts_dir,
                expected_baseline_ref=f"{task.fix_commit}^",
            )
        except Exception as exc:
            print(f"BenchLLMRealSE preflight failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        plan = {
            "benchmark_root": str(task.benchmark_root),
            "workspace": str(args.workspace.resolve()),
            "repository": task.repository_name,
            "commit": task.commit_id,
            "fix_commit": task.fix_commit,
            "prompt": str(task.prompt_path),
            "allowed_source_paths": list(task.source_paths),
            "unit_test_paths": list(task.unit_test_paths),
            "model": config.model,
            "profile": config.profile,
            "codex_version": checked["codex_version"],
            "baseline_commit": checked["baseline_commit"],
            "expected_baseline_commit": checked["expected_baseline_commit"],
            "artifacts_dir": str(artifacts_dir.resolve()),
        }
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    try:
        result = runner.run(
            workspace=args.workspace,
            task_prompt=task.prompt,
            allowed_paths=task.source_paths,
            artifacts_dir=artifacts_dir,
            verification_command=_command(args.verification_command),
            benchmark_command=_command(args.benchmark_command),
            expected_baseline_ref=f"{task.fix_commit}^",
        )
    except Exception as exc:
        print(f"BenchLLMRealSE agent run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({"artifacts": str(artifacts_dir), **as_summary(result)}, indent=2))
    return 0 if result.succeeded else 1


def as_summary(result: CodexRunResult) -> dict[str, object]:
    return {
        "outcome": result.outcome,
        "model": result.model,
        "changed_files": list(result.changed_files),
        "forbidden_changes": list(result.forbidden_changes),
        "error": result.error,
    }


if __name__ == "__main__":
    raise SystemExit(main())
