#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path


def resolve_target(qualified_name: str):
    module_name, attribute = qualified_name.rsplit(".", 1)
    return getattr(importlib.import_module(module_name), attribute)


def main() -> int:
    benchmark_path = Path(sys.argv[1]).resolve()
    qualified_name = sys.argv[2]
    repository = Path.cwd().resolve()
    sys.path.insert(0, str(repository))

    spec = importlib.util.spec_from_file_location(
        "_generated_performance_benchmark", benchmark_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load generated benchmark")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if module.TARGET_SYMBOL != qualified_name:
        raise AssertionError("TARGET_SYMBOL does not match the configured target")
    description = module.WORKLOAD_DESCRIPTION
    if not isinstance(description, str) or not description.strip():
        raise AssertionError("WORKLOAD_DESCRIPTION must be a non-empty string")
    cases = module.get_cases()
    if not isinstance(cases, dict) or not 1 <= len(cases) <= 3:
        raise AssertionError("get_cases() must return a dict containing one to three cases")
    if module.PRIMARY_BENCHMARK not in cases:
        raise AssertionError("PRIMARY_BENCHMARK is not present in get_cases()")

    target = resolve_target(qualified_name)
    target_code = getattr(target, "__code__", None)
    if target_code is None:
        raise AssertionError("Dynamic target-hit validation currently requires a Python target")
    target_source = Path(inspect.getsourcefile(target) or "").resolve()
    if not target_source.is_relative_to(repository):
        raise AssertionError(
            f"Target imported from {target_source}, outside checkout {repository}"
        )

    summaries: list[dict[str, object]] = []
    for name, case in cases.items():
        if not isinstance(name, str) or not name:
            raise AssertionError("Every benchmark name must be a non-empty string")
        if not isinstance(case, tuple) or len(case) != 2:
            raise AssertionError(f"Case {name!r} must be a (callable, expected) tuple")
        callback, expected = case
        if not callable(callback):
            raise AssertionError(f"Case {name!r} callback is not callable")
        if not isinstance(expected, int) or isinstance(expected, bool) or expected <= 0:
            raise AssertionError(f"Case {name!r} expected result must be a positive integer")

        hit = False

        def profiler(frame, event, arg):  # type: ignore[no-untyped-def]
            nonlocal hit
            if event == "call" and frame.f_code is target_code:
                hit = True
            return profiler

        sys.setprofile(profiler)
        try:
            first = callback()
        finally:
            sys.setprofile(None)
        second = callback()
        if not hit:
            raise AssertionError(f"Case {name!r} did not dynamically execute the target")
        if first != expected or second != expected:
            raise AssertionError(
                f"Case {name!r} returned {first!r} then {second!r}; expected {expected!r}"
            )
        summaries.append({"name": name, "expected_result": expected})

    print(
        json.dumps(
            {
                "passed": True,
                "target_symbol": qualified_name,
                "target_source": str(target_source),
                "primary_benchmark": module.PRIMARY_BENCHMARK,
                "workload_description": description,
                "cases": summaries,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
