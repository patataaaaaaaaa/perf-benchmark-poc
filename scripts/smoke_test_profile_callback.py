#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.memory_hotspots import parse_tracemalloc_snapshot  # noqa: E402
from src.framework.sandbox import SandboxLimits, run_in_docker  # noqa: E402


TARGET_SOURCE = """def allocate_cache(entries, entry_bytes):
    result = []
    for index in range(entries):
        value = bytearray(entry_bytes)
        for offset in range(0, entry_bytes, 4096):
            value[offset] = index % 251
        result.append(value)
    return result
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="perf-benchmark-sandbox:py311-v1")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = args.output_root or (
        PROJECT_ROOT / "artifacts" / "profile_callback_smoke" / timestamp
    )
    output.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="profile-callback-") as temporary:
        workspace = Path(temporary)
        # The sandbox runs as uid 65534; TemporaryDirectory defaults to 0700.
        os.chmod(workspace, 0o755)
        (workspace / "memory_target.py").write_text(TARGET_SOURCE, encoding="utf-8")
        result = run_in_docker(
            image=args.image,
            workspace=workspace,
            harness=PROJECT_ROOT / "scripts",
            output=output,
            inner_command=[
                "python",
                "/harness/run_profile_callback.py",
                "--module",
                "/workload_harness/memory_callback.py",
                "--tracemalloc-output",
                "/artifacts/memory.snapshot",
                "--metadata-output",
                "/artifacts/callback.json",
            ],
            limits=SandboxLimits(
                cpus=1.0,
                memory="256m",
                pids=32,
                timeout_seconds=120,
                max_output_bytes=100_000,
            ),
            readonly_mounts=(
                (PROJECT_ROOT / "subjects" / "profiler_callbacks", "/workload_harness"),
            ),
        )
        if result.return_code != 0 or result.timed_out:
            raise RuntimeError(result.stderr or "Profile callback failed")
        report = parse_tracemalloc_snapshot(
            output / "memory.snapshot",
            workspace,
            limit=5,
            recorded_repository=Path("/workspace"),
        )
        hotspots = report.get("hotspots") or []
        passed = bool(
            hotspots
            and hotspots[0].get("qualified_name") == "memory_target.allocate_cache"
        )
        summary = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "docker_image": args.image,
            "llm_called": False,
            "passed": passed,
            "sandbox": result.to_dict(),
            "callback": json.loads((output / "callback.json").read_text()),
            "memory_hotspots": report,
        }
        (output / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[Complete] {output.resolve()}")
        return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
