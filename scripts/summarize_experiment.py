#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import pyperf


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate a repeated POC experiment.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "subjects" / "experiment_run_manifest.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "experiment_20260915",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def robust_rsd(result_path: Path) -> tuple[float, int]:
    values = list(pyperf.Benchmark.load(str(result_path)).get_values())
    median = statistics.median(values)
    mad = statistics.median(abs(value - median) for value in values)
    return (1.4826 * mad / median if median else float("inf"), len(values))


def classify_rsd(value: float | None) -> str:
    if value is None:
        return "unavailable"
    if value <= 0.01:
        return "stable"
    if value < 0.05:
        return "intermediate"
    return "unstable"


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    output_dir = args.output_dir.resolve()
    target_specs = load_json(PROJECT_ROOT / "subjects" / "experiment_targets.json")
    target_ids = [item["id"] for item in target_specs]
    manifest = load_json(manifest_path)
    manual_review = manifest.get("manual_review", {})

    rows: list[dict[str, Any]] = []
    token_fields = (
        "input_tokens",
        "output_tokens",
        "reasoning_tokens",
        "cached_tokens",
        "total_tokens",
    )
    token_totals = {field: 0 for field in token_fields}

    for run in manifest["base_runs"]:
        replicate = int(run["replicate"])
        base_run = PROJECT_ROOT / run["run_dir"]
        replacements = run.get("replacements", {})
        for target_id in target_ids:
            selected_run = PROJECT_ROOT / replacements.get(target_id, run["run_dir"])
            final = load_json(selected_run / target_id / "final.json")
            attempt_number = int(final.get("repair_attempts", 0))
            attempt_dir = selected_run / target_id / f"attempt_{attempt_number}"

            usage = {field: 0 for field in token_fields}
            for metadata_path in sorted((selected_run / target_id).glob("attempt_*/llm_metadata.json")):
                metadata = load_json(metadata_path)
                attempt_usage = metadata.get("usage") or {}
                for field in token_fields:
                    usage[field] += int(attempt_usage.get(field) or 0)
                    token_totals[field] += int(attempt_usage.get(field) or 0)

            result_path = attempt_dir / "result.json"
            rsd_value: float | None = None
            value_count = 0
            if final.get("final_runtime_pass") and result_path.is_file():
                rsd_value, value_count = robust_rsd(result_path)

            code_path = attempt_dir / "benchmark.py"
            code_hash = None
            if code_path.is_file():
                code_hash = hashlib.sha256(code_path.read_bytes()).hexdigest()

            repaired = attempt_number > 0
            repair_success = bool(
                repaired
                and final.get("final_runtime_pass")
                and final.get("target_hit") != "false"
            )
            review_key = f"{replicate}:{target_id}"
            review_override = manual_review.get(review_key)
            if review_override:
                semantic_status = review_override["status"]
                semantic_note = review_override["note"]
            elif final.get("final_runtime_pass"):
                semantic_status = "valid"
                semantic_note = "Manually reviewed; target is invoked in the timed path."
            else:
                semantic_status = "not_executable"
                semantic_note = "Final candidate did not pass runtime validation."
            rows.append(
                {
                    "replicate": replicate,
                    "target_id": target_id,
                    "selected_run": str(selected_run.relative_to(PROJECT_ROOT)),
                    "replaced_transport_failure": selected_run != base_run,
                    "status": final["status"],
                    "initial_syntax_pass": final["initial_syntax_pass"],
                    "initial_import_pass": final["initial_import_pass"],
                    "initial_runtime_pass": final["initial_runtime_pass"],
                    "repair_attempts": attempt_number,
                    "repair_success": repair_success,
                    "final_runtime_pass": final["final_runtime_pass"],
                    "pyperf_check_pass": final["final_stability_pass"],
                    "static_target_hit": final["target_hit"],
                    "manual_semantic_status": semantic_status,
                    "manual_semantic_note": semantic_note,
                    "fast_value_count": value_count,
                    "fast_robust_rsd": round(rsd_value, 6) if rsd_value is not None else None,
                    "fast_rsd_class": classify_rsd(rsd_value),
                    "code_sha256": code_hash,
                    **usage,
                }
            )

    status_counts = Counter(row["status"] for row in rows)
    target_counts = Counter(row["static_target_hit"] for row in rows)
    rsd_counts = Counter(row["fast_rsd_class"] for row in rows)
    semantic_counts = Counter(row["manual_semantic_status"] for row in rows)
    valid_rows = [row for row in rows if row["manual_semantic_status"] == "valid"]
    valid_rsd_counts = Counter(row["fast_rsd_class"] for row in valid_rows)
    repair_rows = [row for row in rows if row["repair_attempts"] > 0]
    summary = {
        "candidate_count": len(rows),
        "target_count": len(target_ids),
        "replicates_per_target": len(manifest["base_runs"]),
        "transport_failure_replacements": sum(
            bool(row["replaced_transport_failure"]) for row in rows
        ),
        "initial_syntax_pass_count": sum(bool(row["initial_syntax_pass"]) for row in rows),
        "initial_import_pass_count": sum(bool(row["initial_import_pass"]) for row in rows),
        "initial_runtime_pass_count": sum(bool(row["initial_runtime_pass"]) for row in rows),
        "final_runtime_pass_count": sum(bool(row["final_runtime_pass"]) for row in rows),
        "repair_needed_count": len(repair_rows),
        "repair_success_count": sum(bool(row["repair_success"]) for row in repair_rows),
        "repair_success_rate": round(
            sum(bool(row["repair_success"]) for row in repair_rows) / len(repair_rows), 4
        ) if repair_rows else 0.0,
        "manual_semantic_counts": dict(sorted(semantic_counts.items())),
        "manual_semantic_repair_success_count": sum(
            row["manual_semantic_status"] == "valid" for row in repair_rows
        ),
        "status_counts": dict(sorted(status_counts.items())),
        "static_target_hit_counts": dict(sorted(target_counts.items())),
        "fast_robust_rsd_counts": dict(sorted(rsd_counts.items())),
        "valid_candidate_fast_robust_rsd_counts": dict(
            sorted(valid_rsd_counts.items())
        ),
        "token_usage": token_totals,
        "manifest": str(manifest_path.relative_to(PROJECT_ROOT)),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output_dir / "candidates.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(output_dir / "summary.json")
    print(output_dir / "candidates.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
