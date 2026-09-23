#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.config import FrameworkConfig  # noqa: E402
from src.framework.hotspots import parse_cprofile  # noqa: E402
from src.framework.memory_hotspots import parse_tracemalloc_snapshot  # noqa: E402
from src.framework.repository import RepositoryManager  # noqa: E402
from src.framework.sandbox import SandboxLimits, run_in_docker  # noqa: E402


TARGET = "urllib.parse.unquote_to_bytes"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-run only the urllib profiler callback without calling an LLM."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "cpython_urllib_memory_e2e.yaml",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    config = FrameworkConfig.load(args.config, PROJECT_ROOT)
    if config.execution_sandbox is None or config.profiler_callback is None:
        raise RuntimeError("Task config requires execution_sandbox and profiler_callback")
    output = args.output or (
        PROJECT_ROOT
        / "artifacts"
        / "cpython_urllib_profiler_retest"
        / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    manager = RepositoryManager(config)
    resolved = manager.checkout(workspace, config.baseline_commit)
    settings = config.execution_sandbox
    callback = config.profiler_callback
    result = run_in_docker(
        image=settings.image,
        workspace=workspace,
        harness=PROJECT_ROOT / "scripts",
        output=output,
        inner_command=[
            "python",
            "/harness/run_profile_callback.py",
            "--module",
            "/workload_harness/profile_unquote_memory.py",
            "--cprofile-output",
            "/artifacts/cpu.prof",
            "--tracemalloc-output",
            "/artifacts/memory.snapshot",
            "--metadata-output",
            "/artifacts/callback.json",
            "--frames",
            str(callback.frames),
        ],
        limits=SandboxLimits(
            cpus=settings.cpus,
            memory=settings.memory,
            pids=settings.pids,
            timeout_seconds=settings.timeout_seconds,
            max_output_bytes=settings.max_output_bytes,
        ),
        readonly_mounts=(
            (PROJECT_ROOT / "subjects" / "cpython_urllib", "/workload_harness"),
        ),
    )
    if result.return_code != 0 or result.timed_out:
        raise RuntimeError(result.stderr or "Profiler callback failed")

    cpu = parse_cprofile(
        output / "cpu.prof",
        workspace,
        limit=callback.limit,
        recorded_repository=Path("/workspace"),
    )
    memory = parse_tracemalloc_snapshot(
        output / "memory.snapshot",
        workspace,
        limit=callback.limit,
        recorded_repository=Path("/workspace"),
    )
    callback_payload = json.loads((output / "callback.json").read_text())
    cpu_names = [str(item.get("qualified_name")) for item in cpu.get("hotspots", [])]
    memory_names = [
        str(item.get("qualified_name")) for item in memory.get("hotspots", [])
    ]
    passed = bool(callback_payload.get("passed") and TARGET in cpu_names)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "llm_called": False,
        "passed": passed,
        "baseline_commit": resolved,
        "target": TARGET,
        "target_in_cpu_top_n": TARGET in cpu_names,
        "target_in_memory_top_n": TARGET in memory_names,
        "callback": callback_payload,
        "cpu_hotspots": cpu,
        "memory_hotspots": memory,
        "sandbox": result.to_dict(),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    shutil.rmtree(workspace)
    print(f"Status: {'PASS' if passed else 'FAIL'}")
    print(f"Artifacts: {output.resolve()}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
