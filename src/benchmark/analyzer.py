from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def summarize(final_results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(final_results)

    def count(field: str, value: Any = True) -> int:
        return sum(item.get(field) == value for item in final_results)

    def rate(number: int, denominator: int = total) -> float:
        return round(number / denominator, 4) if denominator else 0.0

    generated_count = count("generated")
    skipped_count = count("status", "SKIPPED")
    initial_syntax = count("initial_syntax_pass")
    initial_import = count("initial_import_pass")
    initial_runtime = count("initial_runtime_pass")
    final_runtime = count("final_runtime_pass")
    repair_needed = sum(int(item.get("repair_attempts", 0)) > 0 for item in final_results)
    repair_success = sum(
        int(item.get("repair_attempts", 0)) > 0
        and bool(item.get("final_runtime_pass"))
        and item.get("target_hit") != "false"
        for item in final_results
    )
    stable = count("final_stability_pass")
    executable_unstable = count("status", "EXECUTABLE_UNSTABLE")
    repair_attempts = [
        int(item.get("repair_attempts", 0))
        for item in final_results
        if int(item.get("repair_attempts", 0)) > 0
    ]

    return {
        "total_targets": total,
        "generated_count": generated_count,
        "generation_rate": rate(generated_count),
        "skipped_count": skipped_count,
        "initial_syntax_pass_count": initial_syntax,
        "initial_syntax_pass_rate": rate(initial_syntax),
        "initial_import_pass_count": initial_import,
        "initial_import_pass_rate": rate(initial_import),
        "initial_runtime_pass_count": initial_runtime,
        "initial_runtime_pass_rate": rate(initial_runtime),
        "final_runtime_pass_count": final_runtime,
        "final_runtime_pass_rate": rate(final_runtime),
        "repair_needed_count": repair_needed,
        "repair_success_count": repair_success,
        "repair_success_rate": rate(repair_success, repair_needed),
        "stable_benchmark_count": stable,
        "stable_benchmark_rate": rate(stable),
        "executable_unstable_count": executable_unstable,
        "target_hit_true_count": count("target_hit", "true"),
        "target_hit_unknown_count": count("target_hit", "unknown"),
        "target_hit_false_count": count("target_hit", "false"),
        "average_repair_attempts": (
            round(sum(repair_attempts) / len(repair_attempts), 4)
            if repair_attempts
            else 0.0
        ),
    }


def write_summary_csv(path: Path, final_results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "target_id",
        "target_name",
        "generated",
        "initial_syntax_pass",
        "initial_import_pass",
        "initial_runtime_pass",
        "repair_attempts",
        "repair_success",
        "final_syntax_pass",
        "final_import_pass",
        "final_runtime_pass",
        "final_stability_pass",
        "target_hit",
        "status",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(final_results)
