#!/usr/bin/env python3
"""Two unpaid real-task checks using a private runner, sources and Maven cache.

Only preparation, selected tests, and original-version official JMH are run.
There is no import/use of the paid batch main(), API credentials, or Agent exec.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

TASKS = (("netty", "2791f0f"), ("presto", "000fa29"))


def now():
    return datetime.now(timezone.utc).isoformat()


def classpath_export_command(command):
    """Enable only the explicitly requested export, not lifecycle checks/tests."""
    if "dependency:build-classpath" in command:
        return [*command, "-Dair.check.skip-dependency=false", "-Dmdep.skip=false"]
    return command


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def active_evaluators(shared):
    """Do not overlap any known live evaluation/Agent queue on this account."""
    active = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            words = (proc / "cmdline").read_bytes().split(b"\0")
            text = " ".join(w.decode(errors="replace") for w in words)
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if any(Path(w.decode(errors="replace")).name in
               ("run_benchllm_full_batch.py", "isolated_validate.py", "retry_failed.py")
               for w in words if w):
            active.append(int(proc.name))
        elif str(shared) in text and (
                "org.openjdk.jmh.runner.ForkedMain" in text or
                ("benchllm_project_tools.py" in text and " benchmark " in text)):
            active.append(int(proc.name))
    return active


def snapshot_runner(shared, root):
    source = shared / "perf-benchmark-poc"
    dest = root / "runner-snapshot"
    dest.mkdir()
    # Copy code only, not model credentials, artifacts, environments or old logs.
    for folder in ("scripts", "src"):
        shutil.copytree(source / folder, dest / folder,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    hashes = {}
    for path in sorted(dest.rglob("*.py")):
        hashes[str(path.relative_to(dest))] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(root / "runner-snapshot-sha256.json", hashes)
    return dest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shared-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--task", choices=["/".join(t) for t in TASKS], action="append")
    parser.add_argument("--maven-cache-seed", type=Path)
    args = parser.parse_args()
    shared, root = args.shared_root.resolve(), args.run_root.resolve()
    expected = shared / "artifacts/benchllmrealse"
    if root.parent != expected or not root.name.startswith("coverage-typical-unpaid-"):
        raise ValueError("Run root must be a fresh, explicitly scoped coverage directory")
    chosen = tuple(tuple(t.split("/")) for t in args.task) if args.task else TASKS
    if len(set(chosen)) != len(chosen):
        raise ValueError("Duplicate task")
    seed = args.maven_cache_seed.resolve() if args.maven_cache_seed else shared / "batch-maven-home"
    if seed != shared / "batch-maven-home" and not (
            seed.name == "batch-maven-home" and seed.parent.parent == expected and
            seed.parent.name.startswith("coverage-typical-unpaid-")):
        raise ValueError("Cache seed must belong to the shared baseline or a prior isolated attempt")
    root.mkdir(exist_ok=True)
    lock = (root / "queue.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root / "protocol.json").exists():
        raise RuntimeError("Do not overwrite an existing attempt; select a new run root")
    active = active_evaluators(shared)
    if active:
        raise RuntimeError("Evaluation is still active; refusing concurrent builds: " + str(active))
    write_json(root / "pid.json", {"pid": os.getpid(), "started": now()})
    write_json(root / "protocol.json", {
        "started": now(), "tasks": ["/".join(t) for t in chosen],
        "paid_agent_calls": False, "production_edits": False, "test_exclusions": False,
        "runner": "private deployed-code snapshot with runtime candidate hooks",
        "cache": "private full file copy of Maven cache; no hardlinks or shared write paths",
        "maven_cache_seed": str(seed),
        "classpath_export_fix": "explicit air.check.skip-dependency=false and mdep.skip=false only for build-classpath",
        "baseline": "shallow checkout of fix parent, no descendant fix history",
        "jdk": "/usr/lib/jvm/java-8-openjdk-amd64",
        "stages": ["prepare", "sandbox_selected_tests", "original_formal_jmh"],
        "measurement": {"forks": 2, "warmup": 5, "measurement": 10, "seconds": 1},
        "limits_seconds": {"build": 1800, "tests": 600, "jmh": 1800},
        "ssh_entry": "lab-server",
    })
    summary = []
    try:
        (root / "status.txt").write_text("setup: copying private runner and Maven cache\n")
        snapshot = snapshot_runner(shared, root)
        shutil.copytree(seed, root / "batch-maven-home",
                        symlinks=False)
        # Dataset link is read-only by workflow; discovery does not write to it.
        (root / "BenchLLMRealSE").symlink_to(shared / "BenchLLMRealSE", target_is_directory=True)
        shutil.copyfile(shared / "junit-platform-console-standalone-1.9.3.jar",
                        root / "junit-platform-console-standalone-1.9.3.jar")
        for folder in ("sources", "workspaces", "support", "tasks"):
            (root / folder).mkdir()
        # Private refs/config, read-only alternates for large immutable Git objects.
        for repo, _ in chosen:
            private = root / "sources" / repo
            subprocess.run(["git", "init", "--bare", str(private)], check=True)
            # A mirror clone of a shallow cache only preserves objects reachable
            # from advertised refs, missing older task commits in that cache.
            # Explicit alternates expose existing objects without fetching or
            # modifying the shared cache; all refs remain in the private repo.
            (private / "objects/info/alternates").write_text(
                str(shared / "sources" / repo / "objects") + "\n")
        sys.path.insert(0, str(snapshot / "scripts"))
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        full = importlib.import_module("run_benchllm_full_batch")
        fixes = importlib.import_module("coverage_fixes")
        original_flags = full.maven_prepare_flags
        # Only Netty's artificial Java8 override is removed. Presto retains its
        # existing Java8 settings; this avoids mixing two independent hypotheses.
        def flags(run_root):
            result = original_flags(run_root)
            return fixes.preserve_project_language_flags(result) if current_repo == "netty" else result
        original_history = full.history_plugin_present
        def history(workspace, modules):
            if current_repo != "presto":
                return original_history(workspace, modules)
            return fixes.declared_plugin_in_parent_chain(
                workspace / "pom.xml", root / "batch-maven-home",
                "pl.project13.maven", "git-commit-id-plugin")
        full.maven_prepare_flags = flags
        full.history_plugin_present = history
        original_run = full.run
        def run_with_export_fix(command, **kwargs):
            return original_run(classpath_export_command(command), **kwargs)
        full.run = run_with_export_fix
        # No fallback that excludes unrelated tests: a new failure is evidence.
        full.unrelated_test_excludes = lambda *_: None
        tasks = full.select_tasks(full.discover_tasks(root), ",".join("/".join(t) for t in chosen))
        codex = "/downloads/patataWJY/.local/bin/codex"
        # Codex sandbox is a local OS isolation command, not an Agent/model call.
        sandbox_env = {**os.environ, "CODEX_HOME": str(shared / "codex-home")}
        for metadata in tasks:
            current_repo, task = metadata["repository"], metadata["id"]
            output = root / "tasks" / current_repo / task
            output.mkdir(parents=True)
            record = {"repository": current_repo, "task": task, "started": now(),
                      "agent_started": False, "paid": False, "stage": "prepare"}
            support = root / "support" / current_repo / task
            try:
                (root / "status.txt").write_text(f"{len(summary)}/{len(tasks)} complete; {current_repo}/{task}: prepare\n")
                _, workspace, support, manifest = full.prepare_project(root, root, metadata)
                record["prepare_passed"] = True
                record["test_classes"] = manifest["test_classes"]
                record["benchmark_pattern"] = manifest["pattern"]
                record["stage"] = "sandbox_selected_tests"
                (root / "status.txt").write_text(f"{len(summary)}/{len(tasks)} complete; {current_repo}/{task}: sandbox tests\n")
                full.run([codex, "sandbox", "--permission-profile", ":workspace", "--cd", workspace,
                          "--", *full.tool(current_repo, "verify", support, workspace)],
                         log=support / "sandbox-verify.log", timeout=600, env=sandbox_env)
                record["verification_passed"] = True
                record["stage"] = "original_formal_jmh"
                (root / "status.txt").write_text(f"{len(summary)}/{len(tasks)} complete; {current_repo}/{task}: original formal JMH\n")
                full.run(full.tool(current_repo, "benchmark", support, workspace, output),
                         log=output / "benchmark.log", timeout=1800)
                rows = json.loads((output / "jmh.json").read_text())
                full.result_keys(rows)
                record["jmh_rows"] = len(rows)
                record["outcome"] = "original_environment_validated"
            except Exception as exc:
                record.update(outcome="environment_failed", failed_stage=record["stage"],
                              error_type=type(exc).__name__, error=str(exc))
                (output / "error.log").write_text(traceback.format_exc())
            finally:
                workspace = root / "workspaces" / (current_repo + "-" + task + "-original")
                if (workspace / ".git").exists():
                    record["workspace_git_status"] = full.git(workspace, "status", "--porcelain")
                    record["workspace_head"] = full.git(workspace, "rev-parse", "HEAD")
                    record["shallow"] = full.git(workspace, "rev-parse", "--is-shallow-repository")
                    record["tags"] = full.git(workspace, "tag", "--points-at", "HEAD")
                record["ended"] = now()
                write_json(output / "result.json", record)
                summary.append(record)
                write_json(root / "summary.json", summary)
        passed = sum(r["outcome"] == "original_environment_validated" for r in summary)
        (root / "status.txt").write_text(f"complete; {passed}/{len(tasks)} original environments validated; no Agent calls\n")
    except Exception as exc:
        write_json(root / "setup-error.json", {"ended": now(), "error_type": type(exc).__name__,
                                               "error": str(exc), "traceback": traceback.format_exc()})
        (root / "status.txt").write_text("setup_failed; no Agent calls\n")
        raise


if __name__ == "__main__":
    main()
