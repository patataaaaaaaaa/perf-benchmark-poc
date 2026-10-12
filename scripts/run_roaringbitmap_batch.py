#!/usr/bin/env python3
"""Detached, sequential pilot with selectable prompts and offline agent tools."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import urllib.request

PROJECT = Path(__file__).resolve().parents[1]
TASKS = ("34bce1b", "b5b4af6", "53ba593", "abdd6ff", "1de6825")


def run(command, *, cwd=None, log=None, timeout=1800):
    print("RUN", shlex.join([str(p) for p in command]), flush=True)
    if log:
        with Path(log).open("w") as output:
            return subprocess.run(command, cwd=cwd, stdout=output,
                                  stderr=subprocess.STDOUT, timeout=timeout, check=True)
    return subprocess.run(command, cwd=cwd, timeout=timeout, check=True)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def clone_at(repo, revision, path):
    if path.exists():
        if git(path, "rev-parse", "HEAD") != revision or git(path, "status", "--porcelain"):
            raise RuntimeError(f"Unexpected existing workspace: {path}")
        return
    ref = "codex/batch-parent-" + revision[:12]
    run(["git", "-C", str(repo), "update-ref", "refs/heads/" + ref, revision])
    # A parent-only shallow clone does not contain the developer's future patch.
    run(["git", "clone", "--depth=1", "--single-branch", "--branch", ref,
         "file://" + str(repo), str(path)])
    run(["git", "-C", str(path), "checkout", "--detach", revision])
    run(["git", "-C", str(path), "remote", "remove", "origin"])


def measurements(task):
    if task == "34bce1b":
        return [dict(pattern=".*ShiftLeftFromSpecifiedPositionBenchmark.*",
                     args=["-p", f"pos={pos}", "-p", f"count={count}"],
                     params={"pos": str(pos), "count": str(count)}, expected_rows=2)
                for pos, count in ((0, 1), (0, 2), (2, 1))]
    if task == "b5b4af6":
        return [dict(pattern=".*GetCardinalityMappeableContainerBenchmark.*", expected_rows=4)]
    if task == "53ba593":
        return [dict(pattern=".*CheckedAddBenchmark.optimized", expected_rows=4)]
    if task == "abdd6ff":
        return [dict(pattern=".*BSITopKProductionBenchmark.*", expected_rows=4)]
    return [dict(pattern=".*Node16ProductionBenchmark.*", expected_rows=4)]


def prepare(root, batch, task):
    metadata = json.loads((root / "BenchLLMRealSE/Dataset/PerfOpt/RoaringBitmap" / (task + ".json")).read_text())
    repo = root / "RoaringBitmap-extended-source"
    fix = metadata["commit_hash"]
    parent = git(repo, "rev-parse", fix + "^")
    workspace = batch / "workspaces" / (task + "-original")
    support = batch / "support" / task
    support.mkdir(parents=True, exist_ok=True)
    clone_at(repo, parent, workspace)
    if (support / "manifest.json").is_file() and (support / "harness.jar").is_file():
        manifest = json.loads((support / "manifest.json").read_text())
        if manifest["parent"] != parent:
            raise RuntimeError("Prepared support uses a different parent")
        return workspace, support, manifest
    source_paths = shlex.split(metadata["source_code"])
    tests = shlex.split(metadata["unittest"])
    modules = sorted({p.split("/")[0] for p in tests})
    test_classes = [p.split("/src/test/java/", 1)[1][:-5].replace("/", ".") for p in tests]
    task_commands = [v for module in modules for v in (f":{module}:test",)]
    for class_name in test_classes:
        task_commands += ["--tests", class_name]
    distribution = git(repo, "show", parent + ":gradle/wrapper/gradle-wrapper.properties")
    version = re.search(r"gradle-([0-9.]+)-bin", distribution).group(1)
    gradle = root / "tools" / ("gradle-" + version) / "bin/gradle"
    if not gradle.is_file():
        raise RuntimeError(f"Missing prepared Gradle {version}: {gradle}")
    classpath_file = support / "gradle-classpaths.json"
    base = [str(gradle), "--no-daemon", "--max-workers=2", "-g", str(root / "batch-gradle-home"),
            "--init-script", str(PROJECT / "scripts/benchllm_test_classpath.gradle"),
            "-Dbenchllm.classpath.output=" + str(classpath_file)]
    benchmark_path = metadata["jmh_case"] + ".java"
    injected = []
    try:
        target = workspace / benchmark_path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(git(repo, "show", fix + ":" + benchmark_path) + "\n")
            injected.append(target)
        if task == "b5b4af6":
            # Keep workloads identical across forks and all compared versions.
            seeded = git(repo, "show", fix + ":" + benchmark_path).replace("new Random()", "new Random(42)")
            target.write_text(seeded + "\n")
        if task in ("1de6825", "abdd6ff"):
            name = "Node16ProductionBenchmark" if task == "1de6825" else "BSITopKProductionBenchmark"
            package_path = "org/roaringbitmap/art/" if task == "1de6825" else "org/roaringbitmap/"
            extra = workspace / "jmh/src/jmh/java" / package_path / (name + ".java")
            extra.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / "scripts/benchllm_harnesses" / (name + ".java"), extra)
            injected.append(extra)
        try:
            run([*base, "--offline", *task_commands, ":jmh:shadowJar"], cwd=workspace,
                log=support / "prepare-offline.log", timeout=1200)
        except subprocess.CalledProcessError:
            # Dependency preparation is outside the agent budget and never auto-retries a model.
            run([*base, *task_commands, ":jmh:shadowJar"], cwd=workspace,
                log=support / "prepare-online.log", timeout=1800)
        shutil.copyfile(workspace / "jmh/build/libs/benchmarks.jar", support / "harness.jar")
    finally:
        for p in injected:
            p.unlink(missing_ok=True)
        if task == "b5b4af6" and benchmark_path not in [str(p.relative_to(workspace)) for p in injected]:
            target.write_text(git(repo, "show", parent + ":" + benchmark_path) + "\n")
    if git(workspace, "status", "--porcelain"):
        raise RuntimeError("Preparation left tracked/untracked changes")
    runtime = json.loads(classpath_file.read_text())
    manifest = dict(task=task, parent=parent, fix=fix, source_paths=source_paths,
                    test_classes=test_classes, runtime_classpath=sorted({p for m in modules for p in runtime[m]}),
                    measurements=measurements(task), gradle_version=version,
                    metric_origin="supplemental-production" if task in ("1de6825", "abdd6ff") else "official-production",
                    measurement_protocol=dict(warmup=5, measurement=10, forks=2, seconds=1))
    write_json(support / "manifest.json", manifest)
    return workspace, support, manifest


def tool(mode, support, workspace, output=None):
    result = [sys.executable, str(PROJECT / "scripts/benchllm_java_tools.py"), mode,
              "--support", str(support), "--workspace", str(workspace)]
    if output:
        result += ["--output", str(output)]
    return result


def evaluate_reference(support, workspace, output, label):
    """Record a reference failure without rewriting its code or hiding cases."""
    stage = "verification"
    record = dict(code_version=label)
    try:
        run(tool("verify", support, workspace), log=output / "verification.log", timeout=180)
        stage = "benchmark"
        run(tool("benchmark", support, workspace, output), log=output / "benchmark.log", timeout=900)
        record["outcome"] = "succeeded"
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        record.update(outcome="reference_evaluation_failed", failed_stage=stage,
                      error_type=type(exc).__name__, error=str(exc))
    write_json(output / "result.json", record)
    return record


def balance_cny(root):
    """Use provider balance when supported; never emit credentials or response errors."""
    try:
        config = (root / "codex-home/config.toml").read_text()
        base = re.search(r'base_url\s*=\s*"([^"]+)"', config).group(1).rstrip("/")
        env_match = re.search(r'env_key\s*=\s*"([^"]+)"', config)
        key = os.environ.get(env_match.group(1) if env_match else "DEEPSEEK_API_KEY")
        if not key:
            return None
        request = urllib.request.Request(base.removesuffix("/v1") + "/user/balance",
                                         headers={"Authorization": "Bearer " + key})
        data = json.load(urllib.request.urlopen(request, timeout=10))
        for item in data.get("balance_infos", []):
            if item.get("currency") == "CNY":
                return float(item["total_balance"])
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-root", type=Path, required=True)
    parser.add_argument("--batch-dir", type=Path, required=True)
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=list(TASKS))
    parser.add_argument("--prompts", nargs="+", type=int, choices=(1, 2, 3, 4), default=[1, 2, 3, 4])
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--max-agent-runs", type=int, default=20)
    parser.add_argument("--reserve-cny", type=float, default=15)
    parser.add_argument("--max-spend-cny", type=float,
                        help="Stop before another call when the batch balance decrease reaches this amount.")
    parser.add_argument("--agent-timeout-seconds", type=int, default=900)
    parser.add_argument("--continue-on-developer-failure", action="store_true",
                        help="Record a failing developer reference, then evaluate the agent against the unchanged baseline/tests.")
    args = parser.parse_args()
    if len(set(args.prompts)) != len(args.prompts):
        parser.error("--prompts must not contain duplicates")
    if args.max_spend_cny is not None and args.max_spend_cny <= 0:
        parser.error("--max-spend-cny must be positive")
    if args.agent_timeout_seconds <= 0:
        parser.error("--agent-timeout-seconds must be positive")
    root, batch = args.eval_root.resolve(), args.batch_dir.resolve()
    batch.mkdir(parents=True, exist_ok=True)
    (batch / "workspaces").mkdir(exist_ok=True)
    (batch / "support").mkdir(exist_ok=True)
    console = root / "junit-platform-console-standalone-1.9.3.jar"
    shutil.copyfile(console, batch / console.name)
    initial_balance = balance_cny(root) if args.max_spend_cny is not None else None
    if args.max_spend_cny is not None and initial_balance is None and not args.prepare_only:
        (batch / "status.txt").write_text("blocked: initial balance unavailable; no model calls\n")
        return 2
    write_json(batch / "protocol.json", dict(tasks=args.tasks, prompts=args.prompts,
               max_agent_runs=args.max_agent_runs, reserve_cny=args.reserve_cny,
               max_spend_cny=args.max_spend_cny, initial_balance_cny=initial_balance,
               model="deepseek-v4-pro", agent_timeout_seconds=args.agent_timeout_seconds,
               outer_optimization_loop=False,
               continue_on_developer_failure=args.continue_on_developer_failure,
               public_performance_prompts=[p for p in args.prompts if p in (3, 4)],
               started=datetime.now(timezone.utc).isoformat()))
    summary = []
    count = 0
    for task in args.tasks:
        try:
            (batch / "status.txt").write_text(task + ": preparing (no model calls)\n")
            original, support, manifest = prepare(root, batch, task)
            # A no-model smoke test uses the SAME sandbox restrictions as the agent.
            sandbox_cmd = [shutil.which("codex") or "/downloads/patataWJY/.local/bin/codex", "sandbox",
                           "--permission-profile", ":workspace", "--cd", str(original),
                           "--", *tool("verify", support, original)]
            run(sandbox_cmd, log=support / "sandbox-verify.log", timeout=180)
            if args.prepare_only:
                continue
            task_output = batch / task
            task_output.mkdir(exist_ok=True)
            for label in ("original", "developer"):
                workspace = original
                if label == "developer":
                    workspace = batch / "workspaces" / (task + "-developer")
                    clone_at(root / "RoaringBitmap-extended-source", manifest["fix"], workspace)
                output = task_output / label
                output.mkdir(exist_ok=True)
                (batch / "status.txt").write_text(task + ": " + label + " evaluation\n")
                reference = evaluate_reference(support, workspace, output, label)
                if reference["outcome"] != "succeeded":
                    summary.append(dict(task=task, code_version=label,
                                        outcome=reference["outcome"],
                                        failed_stage=reference["failed_stage"],
                                        artifacts=str(output)))
                    write_json(batch / "summary.json", summary)
                    if label != "developer" or not args.continue_on_developer_failure:
                        raise RuntimeError(f"{label} reference failed at {reference['failed_stage']}")
                    print("DEVELOPER_REFERENCE_FAILED_CONTINUING_AGENT", task, flush=True)
            for prompt in args.prompts:
                if count >= args.max_agent_runs:
                    (batch / "status.txt").write_text("stopped: max agent runs\n")
                    return 0
                balance = balance_cny(root)
                write_json(batch / "budget.json", dict(observed_balance_cny=balance,
                           reserve_cny=args.reserve_cny, agent_runs_started=count,
                           initial_balance_cny=initial_balance, max_spend_cny=args.max_spend_cny,
                           note="Balance guard only enforced when provider returns CNY balance."))
                if args.max_spend_cny is not None and balance is None:
                    (batch / "status.txt").write_text("stopped: balance unavailable\n")
                    return 2
                if initial_balance is not None and balance is not None and args.max_spend_cny is not None:
                    if initial_balance - balance >= args.max_spend_cny:
                        (batch / "status.txt").write_text("stopped: batch spending threshold reached\n")
                        return 0
                if balance is not None and balance <= args.reserve_cny:
                    (batch / "status.txt").write_text("stopped: balance reserve reached\n")
                    return 0
                workspace = batch / "workspaces" / (task + "-prompt" + str(prompt))
                clone_at(root / "RoaringBitmap-extended-source", manifest["parent"], workspace)
                output = task_output / ("prompt" + str(prompt))
                test = shlex.join(tool("verify", support, workspace))
                bench = shlex.join(tool("benchmark", support, workspace, output))
                command = [sys.executable, str(PROJECT / "scripts/run_benchllm_codex.py"),
                           "--benchmark-root", str(root / "BenchLLMRealSE"), "--workspace", str(workspace),
                           "--repo-name", "RoaringBitmap", "--commit-id", task, "--prompt-number", str(prompt),
                           "--expected-baseline", manifest["parent"], "--model", "deepseek-v4-pro",
                           "--codex", sandbox_cmd[0], "--timeout-seconds", str(args.agent_timeout_seconds),
                           "--command-timeout-seconds", "900",
                           "--artifacts-dir", str(output), "--agent-test-command", test,
                           "--verification-command", test, "--benchmark-command", bench]
                if prompt in (3, 4):
                    command += ["--agent-benchmark-command", shlex.join(tool("quick", support, workspace))]
                (batch / "status.txt").write_text(f"{task}: prompt{prompt} agent/evaluation\n")
                count += 1
                write_json(batch / "budget.json", dict(observed_balance_cny=balance,
                           reserve_cny=args.reserve_cny, agent_runs_started=count,
                           initial_balance_cny=initial_balance, max_spend_cny=args.max_spend_cny,
                           balance_sample_phase="before_current_agent",
                           note="Count includes the agent task being launched; balance is not a final billing snapshot."))
                try:
                    run(command, log=task_output / f"prompt{prompt}.runner.log", timeout=2100)
                    outcome = "succeeded"
                except subprocess.CalledProcessError:
                    outcome = "failed"
                except subprocess.TimeoutExpired:
                    outcome = "runner_timeout"
                summary.append(dict(task=task, prompt=prompt, outcome=outcome, artifacts=str(output)))
                write_json(batch / "summary.json", summary)
        except Exception as exc:
            print("TASK_INFRASTRUCTURE_FAILURE", task, type(exc).__name__, str(exc), flush=True)
            summary.append(dict(task=task, outcome="infrastructure_failed", error=str(exc)))
            write_json(batch / "summary.json", summary)
            if args.prepare_only:
                raise
    failures = any(row["outcome"] != "succeeded" for row in summary)
    (batch / "status.txt").write_text("complete_with_failures\n" if failures else "complete\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
