#!/usr/bin/env python3
"""Compile current task sources, then run prepared JUnit/JMH without Gradle or network."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("verify", "benchmark", "quick"))
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    support = args.support.resolve()
    manifest = json.loads((support / "manifest.json").read_text())
    workspace = args.workspace.resolve()
    jar = support / "harness.jar"
    console = support.parent.parent / "junit-platform-console-standalone-1.9.3.jar"
    runtime = [p for p in manifest["runtime_classpath"] if "org.junit" not in p]
    cp = os.pathsep.join([str(jar), str(console), *runtime])
    with tempfile.TemporaryDirectory(prefix="benchllm-java-") as temporary:
        overlay = Path(temporary) / "classes"
        overlay.mkdir()
        subprocess.run([
            "javac", "--release", "8", "-cp", cp, "-d", str(overlay),
            *[str(workspace / p) for p in manifest["source_paths"]],
        ], check=True, cwd=workspace)
        # Overlay precedence ensures tests and JMH forks execute the CURRENT patch,
        # never the baseline production classes bundled in the prepared harness.
        effective_cp = os.pathsep.join([str(overlay), cp])
        if args.mode == "verify":
            return subprocess.run([
                "java", "-cp", effective_cp, "org.junit.platform.console.ConsoleLauncher",
                "--disable-ansi-colors", "--fail-if-no-tests", "--details=summary",
                *[v for name in manifest["test_classes"] for v in ("--select-class", name)],
            ], cwd=workspace).returncode

        output = args.output.resolve() if args.output else Path(temporary) / "results"
        output.mkdir(parents=True, exist_ok=True)
        all_rows = []
        quick = args.mode == "quick"
        for index, spec in enumerate(manifest["measurements"]):
            result_path = output / f"jmh-{index}.json"
            command = [
                "java", "-cp", effective_cp, "org.openjdk.jmh.Main", spec["pattern"],
                "-wi", "1" if quick else "5", "-i", "2" if quick else "10",
                "-f", "1" if quick else "2", "-w", "1s", "-r", "1s",
                "-foe", "true", "-rf", "json", "-rff", str(result_path),
                *spec.get("args", []),
            ]
            subprocess.run(command, cwd=workspace, check=True)
            rows = json.loads(result_path.read_text())
            if len(rows) != spec["expected_rows"]:
                raise RuntimeError(f"Incomplete JMH: {len(rows)} != {spec['expected_rows']}")
            for row in rows:
                score = row["primaryMetric"]["score"]
                if not isinstance(score, (float, int)) or not math.isfinite(score) or score <= 0:
                    raise RuntimeError("Invalid JMH score")
                params = row.get("params", {})
                for key, value in spec.get("params", {}).items():
                    if params.get(key) != value:
                        raise RuntimeError(f"Unexpected JMH parameter {key}")
            all_rows.extend(rows)
        keys = [(r["benchmark"], tuple(sorted(r.get("params", {}).items()))) for r in all_rows]
        if len(keys) != len(set(keys)):
            raise RuntimeError("Duplicate JMH result")
        (output / "jmh.json").write_text(json.dumps(all_rows, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
