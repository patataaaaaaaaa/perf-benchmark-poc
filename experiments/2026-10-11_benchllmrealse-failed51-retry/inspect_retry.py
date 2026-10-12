#!/usr/bin/env python3
"""Small, read-only batch status, no credential/balance queries or model calls."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-dir", type=Path, required=True)
    p = parser.parse_args().batch_dir.resolve()
    def read(name, default):
        f = p / name
        return json.loads(f.read_text()) if f.exists() else default
    info = read("pid.json", {})
    pid = info.get("pid")
    proc = Path("/proc") / str(pid)
    try:
        alive = str(p / "inputs/retry_failed.py") in (proc / "cmdline").read_bytes().decode(errors="replace")
    except (FileNotFoundError, PermissionError):
        alive = False
    prep, evaluated = read("prepare-summary.json", []), read("evaluation-summary.json", [])
    paid = [r for r in evaluated if r.get("agent_started")]
    positive_usage = [r for r in paid if ((r.get("usage") or {}).get("total_tokens") or 0) > 0]
    state = (p / "status.txt").read_text().strip() if (p / "status.txt").exists() else "initializing"
    print(json.dumps({
        "checked_utc": datetime.now(timezone.utc).isoformat(), "batch": str(p),
        "pid": pid, "alive": alive, "status": state,
        "unpaid_checked": len(prep), "unpaid_total": 48,
        "unpaid_outcomes": dict(Counter(r["outcome"] for r in prep)),
        "evaluation_queue_length": len(read("evaluation-queue.json", [])),
        "evaluations_completed": len(evaluated),
        "evaluation_outcomes": dict(Counter(r["outcome"] for r in evaluated)),
        "new_agent_launches_completed": len(paid), "positive_usage_agent_results": len(positive_usage),
        "replayed_patches_succeeded": sum(r["outcome"] == "replayed_patch_evaluation_succeeded" for r in evaluated),
        "queue_error": read("queue-error.json", None),
        "recent_prepare_failures": [{k: r.get(k) for k in ("repository", "task", "failed_stage", "error_type")}
                                    for r in prep if r["outcome"] != "preparable"][-3:],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
