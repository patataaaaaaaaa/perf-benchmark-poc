#!/usr/bin/env python3
"""Private, serial retry of 48 pre-call failures and 3 existing Agent patches.

Prepare all 48 without models first. Pay only after both references succeed.
Never rerun the 13 completed Agent evaluations or regenerate existing patches.
"""
import argparse
import fcntl
import importlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import traceback

import isolated_validate as isolation
import coverage_fixes as fixes

PREVIOUS_FULL = "full64-p4-retry-20261010T041500Z"
PREVIOUS_PREP = "failed55-prepare-20261010T123140Z"
PREVIOUS_SEVEN = "preparable7-p4-20261011T023531Z"
JMH_TIMEOUT = 21600
AGENT_TIMEOUT = 900
RESERVE_CNY = 2


def task_key(row):
    return row["repository"], row.get("task", row.get("id"))


def select_retry_sets(full, preparation, seven):
    """Validate the complete 64-task partition before any work or payment."""
    finished = {task_key(r) for r in full if r["outcome"] == "succeeded"}
    finished.update(task_key(r) for r in seven if r["outcome"] == "succeeded")
    prepare = {task_key(r) for r in preparation if r["outcome"] == "infrastructure_failed"}
    replay = {task_key(r) for r in seven if r["outcome"] == "benchmark_failed"}
    groups = [finished, prepare, replay]
    if [len(g) for g in groups] != [13, 48, 3]:
        raise ValueError("Historical task counts changed; expected disjoint 13/48/3 partition")
    if any(groups[i] & groups[j] for i in range(3) for j in range(i)):
        raise ValueError("Historical task partition overlaps")
    known = {task_key(r) for r in full}
    if len(known) != 64 or set.union(*groups) != known:
        raise ValueError("Historical records do not partition all 64 tasks")
    return finished, prepare, replay


def add_source_alternates(shared, root, repositories):
    for repo in sorted(repositories):
        private = root / "sources" / repo
        subprocess.run(["git", "init", "--bare", str(private)], check=True)
        (private / "objects/info/alternates").write_text(str(shared / "sources" / repo / "objects") + "\n")


def load_provider_environment(shared):
    """Read one named credential without shell execution, copying or printing it."""
    config = (shared / "codex-home/config.toml").read_text()
    match = re.search(r'env_key\s*=\s*"([A-Za-z_][A-Za-z0-9_]*)"', config)
    key = match.group(1) if match else "DEEPSEEK_API_KEY"
    if os.environ.get(key):
        return
    for line in (shared / "secrets.env").read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?" + re.escape(key) + r"\s*=\s*(.*)$", line)
        if m:
            try:
                values = shlex.split(m.group(1), comments=True)
            except ValueError:
                raise RuntimeError("Provider credential file has unsupported quoting") from None
            if len(values) != 1 or not values[0]:
                raise RuntimeError("Provider credential is empty or unsupported")
            os.environ[key] = values[0]
            return
    raise RuntimeError("Provider credential is unavailable")


def task_error(path, record, exc):
    record.update(outcome="infrastructure_failed", failed_stage=record["stage"],
                  error_type=type(exc).__name__, error=str(exc))
    (path / "error.log").write_text(traceback.format_exc())


def finalize_workspace(full, workspace, record):
    if (workspace / ".git").exists():
        try:
            record["workspace_git_status"] = full.git(workspace, "status", "--porcelain")
            record["workspace_head"] = full.git(workspace, "rev-parse", "HEAD")
        except Exception as exc:
            record["workspace_inspection_error"] = type(exc).__name__


def references_ready(references):
    return set(references) == {"original", "developer"} and all(
        row.get("outcome") == "succeeded" for row in references.values())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shared-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()
    shared, root = args.shared_root.resolve(), args.run_root.resolve()
    if root.parent != shared / "artifacts/benchllmrealse" or not root.name.startswith("failed51-retry-"):
        raise ValueError("Unexpected run root")
    root.mkdir(exist_ok=True)
    lock = (root / "queue.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root / "protocol.json").exists():
        raise RuntimeError("Preserve existing attempts; do not overwrite a batch")
    if isolation.active_evaluators(shared):
        raise RuntimeError("Another evaluation is active; do not overlap builds/JMH")
    history = shared / "artifacts/benchllmrealse"
    old_full = json.loads((history / PREVIOUS_FULL / "summary.json").read_text())
    old_prep = json.loads((history / PREVIOUS_PREP / "summary.json").read_text())
    old_seven = json.loads((history / PREVIOUS_SEVEN / "summary.json").read_text())
    excluded, prep_keys, replay_keys = select_retry_sets(old_full, old_prep, old_seven)
    write = isolation.write_json
    write(root / "pid.json", {"pid": os.getpid(), "started": isolation.now()})
    write(root / "protocol.json", {
        "started": isolation.now(), "goal": "expand measurable real-task coverage and retry failed results",
        "excluded_completed_agents": sorted(excluded), "unpaid_prepare_tasks": sorted(prep_keys),
        "reuse_existing_agent_patches": sorted(replay_keys), "new_agent_calls_max": 48,
        "paid_after_both_references_pass": True, "prompt": 4, "model": "deepseek-v4-pro",
        "agent_seconds": AGENT_TIMEOUT, "reserve_cny": RESERVE_CNY,
        "jmh_timeout_seconds": JMH_TIMEOUT, "jmh": {"forks": 2, "warmup": 5, "measurement": 10, "seconds": 1},
        "parameter_policy": "all official defaults, no truncation",
        "isolation": "private code, writable Maven/Gradle/tools, Git refs; read-only source object alternates",
        "test_exclusions": False, "production_fixes_by_operator": False,
        "failure_policy": "per-task failure continues; billing/configuration faults stop paid phase",
        "outer_agent_retry_loop": False, "ssh_entry": "lab-server",
    })
    prepared, evaluated = [], []
    stage = "setup"
    try:
        (root / "status.txt").write_text("setup: private code and cache copies; no model calls\n")
        snapshot = isolation.snapshot_runner(shared, root)
        for name in ("workspaces", "sources", "support", "tasks"):
            (root / name).mkdir()
        seed = history / "coverage-typical-unpaid-20261011T080738Z/batch-maven-home"
        shutil.copytree(seed, root / "batch-maven-home", symlinks=False)
        shutil.copytree(shared / "batch-gradle-home", root / "batch-gradle-home", symlinks=False,
                        ignore=shutil.ignore_patterns("daemon", "*.lock", "*.lck"))
        shutil.copytree(shared / "tools", root / "tools", symlinks=False)
        shutil.copyfile(shared / "junit-platform-console-standalone-1.9.3.jar", root / "junit-platform-console-standalone-1.9.3.jar")
        (root / "BenchLLMRealSE").symlink_to(shared / "BenchLLMRealSE", target_is_directory=True)
        add_source_alternates(shared, root, {r for r, _ in prep_keys | replay_keys})
        sys.path.insert(0, str(snapshot / "scripts"))
        full = importlib.import_module("run_benchllm_full_batch")
        original_run, original_flags, original_history = full.run, full.maven_prepare_flags, full.history_plugin_present
        current_repo = None
        def run(command, **kwargs):
            return original_run(isolation.classpath_export_command(command), **kwargs)
        def flags(run_root):
            values = original_flags(run_root)
            return fixes.preserve_project_language_flags(values) if current_repo == "netty" else values
        def inherited_history(workspace, modules):
            if current_repo != "presto":
                return original_history(workspace, modules)
            return fixes.declared_plugin_in_parent_chain(workspace / "pom.xml", root / "batch-maven-home",
                                                       "pl.project13.maven", "git-commit-id-plugin")
        full.run, full.maven_prepare_flags, full.history_plugin_present = run, flags, inherited_history
        full.unrelated_test_excludes = lambda *_: None
        codex = "/downloads/patataWJY/.local/bin/codex"
        env = {**os.environ, "CODEX_HOME": str(shared / "codex-home")}
        run([codex, "sandbox", "--permission-profile", ":workspace", "--cd", snapshot,
             "--", sys.executable, "-c", "print('configuration preflight passed')"],
            log=root / "sandbox-preflight.log", timeout=60, env=env)
        all_tasks = full.discover_tasks(root)
        task_map = {task_key(t): t for t in all_tasks}
        # Finish environment accounting first: no models are called in this loop.
        stage = "unpaid_prepare"
        for metadata in all_tasks:
            key = task_key(metadata)
            if key not in prep_keys:
                continue
            current_repo, task = key
            out = root / "tasks" / current_repo / task
            out.mkdir(parents=True)
            ws = root / "workspaces" / (current_repo + "-" + task + "-original")
            record = {"repository": current_repo, "task": task, "stage": "prepare", "agent_started": False,
                      "started": isolation.now()}
            (root / "status.txt").write_text(f"unpaid_prepare {len(prepared)}/48; {current_repo}/{task}\n")
            try:
                _, ws, support, manifest = full.prepare_project(root, root, metadata)
                record["stage"] = "sandbox_selected_tests"
                run([codex, "sandbox", "--permission-profile", ":workspace", "--cd", ws,
                     "--", *full.tool(current_repo, "verify", support, ws)],
                    log=support / "sandbox-verify.log", timeout=600, env=env)
                record.update(outcome="preparable", test_classes=manifest["test_classes"])
            except Exception as exc:
                task_error(out, record, exc)
            finalize_workspace(full, ws, record)
            if record["outcome"] == "preparable" and (
                    record.get("workspace_git_status") or record.get("workspace_inspection_error")):
                record.update(outcome="infrastructure_failed", failed_stage="workspace_integrity",
                              error_type="WorkspaceIntegrityError", error="Workspace is dirty or cannot be inspected after preparation")
            record["ended"] = isolation.now()
            prepared.append(record)
            write(out / "prepare-result.json", record)
            write(root / "prepare-summary.json", prepared)
        ready = {task_key(r) for r in prepared if r["outcome"] == "preparable"}
        # Fast prepared Netty tasks first; long Presto references last. Existing
        # paid Kafka patches are replayed before new Kafka/Presto paid attempts.
        def priority(key):
            return (0 if key[0] == "netty" else 1 if key in replay_keys else 2 if key[0] == "kafka" else 3, key[1])
        queue = sorted(ready | replay_keys, key=priority)
        write(root / "evaluation-queue.json", [dict(repository=r, task=t, reuse_patch=(r, t) in replay_keys) for r, t in queue])
        stage = "references_and_agent"
        provider_loaded = False
        for key in queue:
            current_repo, task = key
            metadata = task_map[key]
            out = root / "tasks" / current_repo / task
            out.mkdir(parents=True, exist_ok=True)
            record = {"repository": current_repo, "task": task, "started": isolation.now(),
                      "stage": "reference_original", "agent_started": False, "reuse_patch": key in replay_keys}
            references = {}
            try:
                if key in replay_keys:
                    cached = full.prepare_cached(root, root, metadata, history / PREVIOUS_SEVEN)
                    if cached is None:
                        raise RuntimeError("Existing patch frozen support is unavailable")
                    source, original, support, manifest = cached
                else:
                    source = root / "sources" / current_repo
                    original = root / "workspaces" / (current_repo + "-" + task + "-original")
                    support = root / "support" / current_repo / task
                    manifest = json.loads((support / "manifest.json").read_text())
                for label in ("original", "developer"):
                    record["stage"] = "reference_" + label
                    (root / "status.txt").write_text(f"evaluation {len(evaluated)}/{len(queue)}; {current_repo}/{task}: {label}\n")
                    workspace = original
                    if label == "developer":
                        workspace = root / "workspaces" / (current_repo + "-" + task + "-developer")
                        full.clone_at(source, manifest["fix"], workspace)
                    target = out / label
                    target.mkdir(exist_ok=True)
                    ref = {"code_version": label, "stage": "verification"}
                    try:
                        run(full.tool(current_repo, "verify", support, workspace), log=target / "verification.log", timeout=600)
                        ref["stage"] = "benchmark"
                        run(full.tool(current_repo, "benchmark", support, workspace, target), log=target / "benchmark.log", timeout=JMH_TIMEOUT)
                        rows = json.loads((target / "jmh.json").read_text())
                        keys = full.result_keys(rows)
                        if label == "original":
                            write(support / "expected-jmh-keys.json", keys)
                        ref.update(outcome="succeeded", jmh_rows=len(rows))
                    except Exception as exc:
                        ref.update(outcome="reference_evaluation_failed", error_type=type(exc).__name__, error=str(exc))
                    write(target / "result.json", ref)
                    references[label] = ref
                    # A known broken reference is not an opportunity to pay.
                    if ref["outcome"] != "succeeded":
                        break
                record["references"] = references
                if not references_ready(references):
                    record["outcome"] = "reference_evaluation_failed_no_new_agent"
                elif key in replay_keys:
                    record["stage"] = "existing_patch_evaluation"
                    ws = root / "workspaces" / (current_repo + "-" + task + "-replayed-agent")
                    full.clone_at(source, manifest["parent"], ws)
                    old = history / PREVIOUS_SEVEN / "tasks" / current_repo / task / "prompt4"
                    patch = old / "agent.patch"
                    old_result = json.loads((old / "result.json").read_text())
                    if old_result.get("verification", {}).get("returncode") != 0 or not patch.stat().st_size:
                        raise RuntimeError("Existing patch is not a verified reusable candidate")
                    run(["git", "apply", "--check", patch], cwd=ws, log=out / "patch-check.log", timeout=60)
                    run(["git", "apply", patch], cwd=ws, log=out / "patch-apply.log", timeout=60)
                    changed = set(full.git(ws, "diff", "--name-only").splitlines())
                    if not changed or not changed.issubset(set(manifest["source_paths"])):
                        raise RuntimeError("Replayed patch changes outside allowed source files")
                    target = out / "replayed-agent"
                    target.mkdir()
                    run([codex, "sandbox", "--permission-profile", ":workspace", "--cd", ws,
                         "--", *full.tool(current_repo, "verify", support, ws)],
                        log=target / "verification.log", timeout=600, env=env)
                    run(full.tool(current_repo, "benchmark", support, ws, target), log=target / "benchmark.log", timeout=JMH_TIMEOUT)
                    rows = json.loads((target / "jmh.json").read_text())
                    full.result_keys(rows)
                    record.update(outcome="replayed_patch_evaluation_succeeded", jmh_rows=len(rows),
                                  original_agent_result=str(old / "result.json"), original_usage=old_result.get("usage"))
                    shutil.copyfile(patch, target / "agent.patch")
                else:
                    record["stage"] = "paid_agent"
                    if not provider_loaded:
                        load_provider_environment(shared)
                        provider_loaded = True
                        env = {**os.environ, "CODEX_HOME": str(shared / "codex-home")}
                    balance = full.roaring.balance_cny(shared)
                    write(root / "budget.json", {"observed_balance_cny": balance, "reserve_cny": RESERVE_CNY,
                                                 "agent_calls_started": sum(r["agent_started"] for r in evaluated)})
                    if balance is None or balance <= RESERVE_CNY:
                        record.update(outcome="pending_budget", global_stop_reason="balance_unavailable_or_reserve_reached")
                    else:
                        ws = root / "workspaces" / (current_repo + "-" + task + "-prompt4")
                        full.clone_at(source, manifest["parent"], ws)
                        agent_out = out / "prompt4"
                        verify = ["/usr/bin/timeout", "--kill-after=5s", "600", *full.tool(current_repo, "verify", support, ws)]
                        command = [sys.executable, snapshot / "scripts/run_benchllm_codex.py", "--benchmark-root", root / "BenchLLMRealSE",
                                   "--workspace", ws, "--repo-name", current_repo, "--commit-id", task, "--prompt-number", "4",
                                   "--expected-baseline", manifest["parent"], "--model", "deepseek-v4-pro", "--codex", codex,
                                   "--timeout-seconds", str(AGENT_TIMEOUT), "--command-timeout-seconds", str(JMH_TIMEOUT),
                                   "--artifacts-dir", agent_out, "--agent-test-command", shlex.join(map(str, verify)),
                                   "--verification-command", shlex.join(map(str, verify)),
                                   "--agent-benchmark-command", shlex.join(map(str, full.tool(current_repo, "quick", support, ws))),
                                   "--benchmark-command", shlex.join(map(str, full.tool(current_repo, "benchmark", support, ws, agent_out)))]
                        record["agent_started"] = True
                        (root / "status.txt").write_text(f"evaluation {len(evaluated)}/{len(queue)}; {current_repo}/{task}: P4 Agent\n")
                        try:
                            run(command, log=out / "prompt4.runner.log", timeout=AGENT_TIMEOUT + 2 * JMH_TIMEOUT + 120, env=env)
                        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                            pass
                        result = json.loads((agent_out / "result.json").read_text()) if (agent_out / "result.json").exists() else {"outcome": "runner_failed"}
                        record.update(outcome=result["outcome"], usage=result.get("usage"))
                        if full.global_api_failure(agent_out):
                            record["global_stop_reason"] = "credentials_or_billing"
            except Exception as exc:
                task_error(out, record, exc)
                if record["stage"] == "paid_agent" and not provider_loaded:
                    record["global_stop_reason"] = "provider_configuration"
            record["ended"] = isolation.now()
            evaluated.append(record)
            write(out / "evaluation-result.json", record)
            write(root / "evaluation-summary.json", evaluated)
            if record.get("global_stop_reason"):
                (root / "status.txt").write_text(f"stopped: {record['global_stop_reason']}; unpaid48 done; evaluation {len(evaluated)}/{len(queue)}\n")
                return 2
        (root / "status.txt").write_text(f"complete; unpaid48 checked, {len(ready)} preparable; evaluation {len(evaluated)}/{len(queue)} processed\n")
        write(root / "completion.json", {"ended": isolation.now(), "prepare_count": len(prepared), "preparable": len(ready),
                                         "evaluation_count": len(evaluated), "new_agent_starts": sum(r["agent_started"] for r in evaluated)})
    except Exception as exc:
        write(root / "queue-error.json", {"stage": stage, "ended": isolation.now(), "error_type": type(exc).__name__, "error": str(exc)})
        (root / "status.txt").write_text("queue_failed: " + stage + "\n")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
