#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


IGNORED_SOURCE_PARTS = {"bench", "benchmark", "benchmarks", "test", "tests"}


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_repository_workload.py WORKLOAD.py")
    workload_path = Path(sys.argv[1]).resolve()
    repository = Path.cwd().resolve()
    sys.path.insert(0, str(repository))

    spec = importlib.util.spec_from_file_location(
        "_autonomous_repository_workload", workload_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load generated repository workload")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    evidence = getattr(module, "SOURCE_EVIDENCE", None)
    if not isinstance(evidence, tuple) or not evidence:
        raise AssertionError("SOURCE_EVIDENCE must be a non-empty tuple")
    normalized_evidence: list[str] = []
    for raw in evidence:
        relative = Path(str(raw))
        if relative.is_absolute() or ".." in relative.parts:
            raise AssertionError(f"Unsafe SOURCE_EVIDENCE path: {relative}")
        if not (repository / relative).is_file():
            raise AssertionError(f"SOURCE_EVIDENCE does not exist: {relative}")
        normalized_evidence.append(relative.as_posix())

    description = getattr(module, "WORKLOAD_DESCRIPTION", None)
    rationale = getattr(module, "SELECTION_RATIONALE", None)
    if not isinstance(description, str) or not description.strip():
        raise AssertionError("WORKLOAD_DESCRIPTION must be a non-empty string")
    if not isinstance(rationale, str) or not rationale.strip():
        raise AssertionError("SELECTION_RATIONALE must be a non-empty string")
    cases = module.get_cases()
    if not isinstance(cases, dict) or not 1 <= len(cases) <= 3:
        raise AssertionError("get_cases() must return one to three cases")
    primary = getattr(module, "PRIMARY_BENCHMARK", None)
    if primary not in cases:
        raise AssertionError("PRIMARY_BENCHMARK is not present in get_cases()")

    case_summaries: list[dict[str, object]] = []
    repository_hits: set[tuple[str, str]] = set()
    production_hits: set[tuple[str, str]] = set()
    for name, case in cases.items():
        if not isinstance(name, str) or not name:
            raise AssertionError("Every case name must be a non-empty string")
        if not isinstance(case, tuple) or len(case) != 2:
            raise AssertionError(f"Case {name!r} must be a (callback, expected) tuple")
        callback, expected = case
        if not callable(callback):
            raise AssertionError(f"Case {name!r} callback is not callable")
        if not isinstance(expected, int) or isinstance(expected, bool) or expected <= 0:
            raise AssertionError(f"Case {name!r} expected must be a positive integer")

        def profiler(frame, event, arg):  # type: ignore[no-untyped-def]
            if event != "call":
                return profiler
            raw_file = frame.f_code.co_filename
            if not raw_file or str(raw_file).startswith("<"):
                return profiler
            source = Path(raw_file).resolve()
            try:
                relative = source.relative_to(repository)
            except ValueError:
                return profiler
            hit = (relative.as_posix(), frame.f_code.co_name)
            repository_hits.add(hit)
            if not any(part.lower() in IGNORED_SOURCE_PARTS for part in relative.parts):
                production_hits.add(hit)
            return profiler

        sys.setprofile(profiler)
        try:
            first = callback()
        finally:
            sys.setprofile(None)
        second = callback()
        if first != expected or second != expected:
            raise AssertionError(
                f"Case {name!r} returned {first!r} then {second!r}; expected {expected!r}"
            )
        case_summaries.append({"name": name, "expected_result": expected})

    if not production_hits:
        raise AssertionError(
            "Workload did not dynamically execute any repository production Python code"
        )

    print(
        json.dumps(
            {
                "passed": True,
                "source_evidence": normalized_evidence,
                "primary_benchmark": primary,
                "workload_description": description,
                "selection_rationale": rationale,
                "cases": case_summaries,
                "repository_hit_count": len(repository_hits),
                "production_hit_count": len(production_hits),
                "production_hits": [
                    {"file": file, "function": function}
                    for file, function in sorted(production_hits)[:50]
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
