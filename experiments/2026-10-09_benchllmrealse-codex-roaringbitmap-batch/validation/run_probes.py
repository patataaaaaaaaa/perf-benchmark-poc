#!/usr/bin/env python3
"""Run diagnostic probes against frozen workspaces; never invoke a model."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import tempfile


def run_probe(root, probe, task, version):
    manifest = json.loads((root / "support" / task / "manifest.json").read_text())
    workspace = root / "workspaces" / f"{task}-{version}"
    classpath = os.pathsep.join([
        str(root / "support" / task / "harness.jar"),
        str(root / "junit-platform-console-standalone-1.9.3.jar"),
        *[p for p in manifest["runtime_classpath"] if "org.junit" not in p],
    ])
    record = {"task": task, "version": version}
    with tempfile.TemporaryDirectory(prefix="benchllm-probe-classes-") as temporary:
        compiled = subprocess.run([
            "javac", "--release", "8", "-cp", classpath, "-d", temporary,
            *[str(workspace / p) for p in manifest["source_paths"]], str(probe),
        ], capture_output=True, text=True, timeout=90)
        record["compile_returncode"] = compiled.returncode
        if compiled.returncode:
            record["error"] = compiled.stderr
            return record
        ran = subprocess.run([
            "java", "-cp", temporary + os.pathsep + classpath,
            "FunctionalProbe", task,
        ], capture_output=True, text=True, timeout=90)
        record.update(returncode=ran.returncode, stdout=ran.stdout, stderr=ran.stderr)
        return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-root", type=Path, required=True)
    parser.add_argument("--probe", type=Path, default=Path(__file__).with_name("FunctionalProbe.java"))
    parser.add_argument("--task", choices=["34bce1b", "b5b4af6", "53ba593"])
    args = parser.parse_args()
    root, probe = args.batch_root.resolve(), args.probe.resolve()
    tasks = [args.task] if args.task else ["34bce1b", "b5b4af6", "53ba593"]
    pairs = [(task, version) for task in tasks
             for version in ["original", "developer", "prompt1", "prompt2", "prompt3", "prompt4"]
             if (root / task / version / "result.json").is_file()]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for record in pool.map(lambda pair: run_probe(root, probe, *pair), pairs):
            print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
