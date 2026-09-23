#!/usr/bin/env python3
from __future__ import annotations

import argparse
import cProfile
import importlib.util
import json
import sys
import tracemalloc
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "profile-callback-v1"


def load_module(path: Path) -> Any:
    resolved = path.resolve()
    # A callback is allowed to keep small helpers beside its entry module.  A
    # normal ``python callback.py`` invocation includes that directory on
    # sys.path; reproduce the same import behavior for dynamic loading.
    parent = str(resolved.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location("_profile_callback", resolved)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import callback module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("prepare_workload", "run_workload", "validate_workload"):
        if not callable(getattr(module, name, None)):
            raise RuntimeError(f"Callback module must define callable {name}()")
    return module


def json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return repr(value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one explicit workload callback under selected Python profilers."
    )
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--cprofile-output", type=Path)
    parser.add_argument("--tracemalloc-output", type=Path)
    parser.add_argument("--resource-only", action="store_true")
    parser.add_argument("--metadata-output", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=10)
    args = parser.parse_args()
    if (
        args.cprofile_output is None
        and args.tracemalloc_output is None
        and not args.resource_only
    ):
        raise ValueError("At least one profiler output must be requested")
    if args.frames < 1:
        raise ValueError("--frames must be positive")

    sys.path.insert(0, str(Path.cwd()))
    module = load_module(args.module)

    # Imports, input construction and optional warmup are intentionally outside
    # both profiler windows.
    prepared = module.prepare_workload()
    warmup_validation: Any = None
    warmup = getattr(module, "warmup_workload", None)
    if callable(warmup):
        warmup_result = warmup(prepared)
        warmup_validation = module.validate_workload(warmup_result)
        prepared = module.prepare_workload()

    profiler = cProfile.Profile() if args.cprofile_output else None
    if args.tracemalloc_output:
        tracemalloc.start(args.frames)
    if profiler:
        profiler.enable()
    try:
        result = module.run_workload(prepared)
    finally:
        if profiler:
            profiler.disable()

    # Capture while both prepared state and result are still strongly referenced.
    snapshot = tracemalloc.take_snapshot() if args.tracemalloc_output else None
    current_peak = (
        tracemalloc.get_traced_memory() if args.tracemalloc_output else (None, None)
    )
    validation = module.validate_workload(result)

    if profiler and args.cprofile_output:
        args.cprofile_output.parent.mkdir(parents=True, exist_ok=True)
        profiler.dump_stats(str(args.cprofile_output))
    if snapshot is not None and args.tracemalloc_output:
        args.tracemalloc_output.parent.mkdir(parents=True, exist_ok=True)
        snapshot.dump(str(args.tracemalloc_output))
        tracemalloc.stop()

    profilers = []
    if profiler:
        profilers.append("cprofile")
    if snapshot is not None:
        profilers.append("tracemalloc")
    if args.resource_only:
        profilers.append("process_io")
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.write_text(
        json.dumps(
            {
                "contract_version": CONTRACT_VERSION,
                "module": str(args.module),
                "profilers": profilers,
                "warmup_validation": json_safe(warmup_validation),
                "validation": json_safe(validation),
                "tracemalloc_current_bytes": current_peak[0],
                "tracemalloc_peak_bytes": current_peak[1],
                "passed": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
