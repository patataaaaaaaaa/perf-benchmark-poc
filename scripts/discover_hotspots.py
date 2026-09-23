#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.hotspots import contains_symbol, parse_cprofile  # noqa: E402
from src.framework.sandbox import SandboxLimits, run_in_docker  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a controlled workload and report project-local hotspots."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "more_itertools_triplewise_hotspot.yaml",
    )
    return parser.parse_args()


def _git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else PROJECT_ROOT / path


def _ref_map(repository: Path) -> dict[str, str]:
    path = repository / ".git" / "framework_refs.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in payload.items()}


def _prepare_repository(config: dict[str, Any]) -> Path:
    cache_root = _resolve(config.get("repository_cache", ".cache/repositories"))
    cache = cache_root / str(config["task_id"])
    url = str(config["repository_url"])
    commit = str(config["baseline_commit"])
    if not (cache / ".git").is_dir():
        cache.parent.mkdir(parents=True, exist_ok=True)
        _git(["clone", "--no-checkout", url, str(cache)])
    elif _git(["remote", "get-url", "origin"], cache) != url:
        raise RuntimeError(f"Repository cache has the wrong origin: {cache}")
    if commit not in _ref_map(cache):
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=cache,
            capture_output=True,
            check=False,
        )
        if exists.returncode != 0:
            _git(["fetch", "--depth", "1", "origin", commit], cache)
    return cache


def _expand_command(values: list[object], output: Path) -> list[str]:
    replacements = {
        "{project_root}": str(PROJECT_ROOT),
        "{python}": str(PROJECT_ROOT / ".venv" / "bin" / "python"),
        "{output}": str(output),
    }
    command: list[str] = []
    for raw in values:
        value = str(raw)
        for old, new in replacements.items():
            value = value.replace(old, new)
        command.append(value)
    return command


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    required = ("task_id", "repository_url", "baseline_commit", "profile_command")
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise ValueError(f"Missing configuration fields: {', '.join(missing)}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = _resolve(config.get("artifacts_root", "artifacts/hotspot_discovery")) / stamp
    workspace = run_dir / "workspace"
    run_dir.mkdir(parents=True, exist_ok=False)

    print("[Prepare] checkout baseline")
    cache = _prepare_repository(config)
    _git(["clone", "--shared", "--no-checkout", str(cache), str(workspace)])
    declared_commit = str(config["baseline_commit"])
    checkout_ref = _ref_map(cache).get(declared_commit, declared_commit)
    resolved_checkout = _git(["rev-parse", f"{checkout_ref}^{{commit}}"], cache)
    _git(["checkout", "--detach", resolved_checkout], workspace)

    raw_profile = run_dir / "profile.prof"
    sandbox_config = config.get("sandbox") or {}
    sandbox_enabled = bool(sandbox_config.get("enabled", False))
    if sandbox_enabled:
        print("[Profile] run controlled workload in Docker sandbox")
        sandbox_output = run_dir / "sandbox_output"
        if not sandbox_config.get("command"):
            raise ValueError("sandbox.command must be configured when sandbox is enabled")
        if not sandbox_config.get("harness"):
            raise ValueError("sandbox.harness must be configured when sandbox is enabled")
        inner_command = [str(value) for value in sandbox_config["command"]]
        limits = SandboxLimits(
            cpus=float(sandbox_config.get("cpus", 1.0)),
            memory=str(sandbox_config.get("memory", "512m")),
            pids=int(sandbox_config.get("pids", 64)),
            timeout_seconds=int(sandbox_config.get("timeout_seconds", 120)),
            max_output_bytes=int(sandbox_config.get("max_output_bytes", 1_000_000)),
        )
        sandbox_result = run_in_docker(
            image=str(sandbox_config.get("image", "python:3.11-slim")),
            workspace=workspace,
            harness=_resolve(sandbox_config["harness"]),
            output=sandbox_output,
            inner_command=inner_command,
            limits=limits,
        )
        command = list(sandbox_result.command)
        (run_dir / "stdout.txt").write_text(sandbox_result.stdout, encoding="utf-8")
        (run_dir / "stderr.txt").write_text(sandbox_result.stderr, encoding="utf-8")
        _write_json(run_dir / "sandbox.json", sandbox_result.to_dict())
        if sandbox_result.timed_out:
            raise RuntimeError("Profiling workload timed out in Docker sandbox")
        if sandbox_result.return_code != 0:
            raise RuntimeError(
                f"Sandbox workload failed with exit code {sandbox_result.return_code}; "
                f"see {run_dir / 'stderr.txt'}"
            )
        produced_profile = sandbox_output / "profile.prof"
        if produced_profile.is_file():
            shutil.copy2(produced_profile, raw_profile)
        recorded_repository = Path("/workspace")
    else:
        command = _expand_command(list(config["profile_command"]), raw_profile)
        print("[Profile] run controlled workload directly")
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                text=True,
                capture_output=True,
                timeout=int(config.get("timeout_seconds", 120)),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            (run_dir / "stdout.txt").write_text(exc.stdout or "", encoding="utf-8")
            (run_dir / "stderr.txt").write_text(exc.stderr or "", encoding="utf-8")
            raise RuntimeError("Profiling workload timed out") from exc
        (run_dir / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (run_dir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
        if completed.returncode != 0:
            raise RuntimeError(
                f"Profiling workload failed with exit code {completed.returncode}; "
                f"see {run_dir / 'stderr.txt'}"
            )
        recorded_repository = workspace
    if not raw_profile.is_file():
        raise RuntimeError("Profiling command did not create the configured output")

    print("[Analyze] filter and rank repository functions")
    report = parse_cprofile(
        raw_profile,
        workspace,
        limit=int(config.get("hotspot_limit", 5)),
        recorded_repository=recorded_repository,
    )
    expected = config.get("validation_expected_symbol")
    validation = {
        "expected_symbol": expected,
        "found_in_top_hotspots": (
            contains_symbol(report, str(expected)) if expected else None
        ),
        "note": "This expected symbol is used only after ranking for validation.",
    }
    report["validation"] = validation
    report["baseline_commit"] = declared_commit
    report["checkout_commit"] = resolved_checkout
    report["profile_command"] = command
    report["execution_mode"] = "docker" if sandbox_enabled else "direct"
    _write_json(run_dir / "hotspots.json", report)

    lines = [
        "# 自动热点定位结果",
        "",
        "本报告来自可控 workload 的实际运行数据；预期答案未参与热点排名。",
        "",
        "| 排名 | 函数 | 自身耗时(s) | 累计耗时(s) | 调用次数 | 自身耗时占比 |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for item in report["hotspots"]:
        lines.append(
            f"| {item['rank']} | `{item['qualified_name']}` | "
            f"{item['self_time_seconds']:.6f} | "
            f"{item['cumulative_time_seconds']:.6f} | "
            f"{item['total_calls']} | {item['self_time_percent']:.2f}% |"
        )
    if expected:
        outcome = "成功" if validation["found_in_top_hotspots"] else "失败"
        lines.extend(
            [
                "",
                f"验收结果：**{outcome}**。Top {config.get('hotspot_limit', 5)} "
                f"中{'包含' if validation['found_in_top_hotspots'] else '不包含'}预期热点 "
                f"`{expected}`。",
            ]
        )
    (run_dir / "REPORT_ZH.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # The checkout can be reproduced from the pinned commit and is not evidence.
    shutil.rmtree(workspace)
    print(f"[Complete] artifacts: {run_dir}")
    print(f"Hotspots: {run_dir / 'hotspots.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Hotspot discovery failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
