#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.config import FrameworkConfig  # noqa: E402
from src.framework.evaluator import Evaluator  # noqa: E402
from src.framework.generated_benchmark import validate_generated_benchmark  # noqa: E402
from src.framework.patching import apply_safe_patch  # noqa: E402
from src.framework.repository import RepositoryManager  # noqa: E402
from src.framework.sandbox import SandboxLimits  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "more_itertools_triplewise_auto_e2e.yaml",
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        help="Optional previously frozen generated benchmark to validate in Docker.",
    )
    parser.add_argument(
        "--patch",
        type=Path,
        help="Optional previously generated candidate patch to apply before execution.",
    )
    args = parser.parse_args()

    config = FrameworkConfig.load(args.config, PROJECT_ROOT)
    execution = config.execution_sandbox
    if execution is None:
        raise ValueError("The selected config does not enable execution_sandbox")
    config = replace(
        config,
        target_file=Path("more_itertools/recipes.py"),
        target_symbol="more_itertools.recipes.triplewise",
        editable_files=(Path("more_itertools/recipes.py"),),
    )
    evaluator = Evaluator(
        config.timeout_seconds,
        primary_benchmark="triplewise_large",
        docker_image=execution.image,
        project_root=PROJECT_ROOT,
        sandbox_limits=SandboxLimits(
            cpus=execution.cpus,
            memory=execution.memory,
            pids=execution.pids,
            timeout_seconds=execution.timeout_seconds,
            max_output_bytes=execution.max_output_bytes,
        ),
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = PROJECT_ROOT / "artifacts" / "execution_sandbox_smoke" / stamp
    workspace = run_dir / "workspace"
    run_dir.mkdir(parents=True)
    RepositoryManager(config).checkout(workspace, config.baseline_commit)
    if args.patch:
        apply_safe_patch(
            workspace,
            args.patch.read_text(encoding="utf-8"),
            config.editable_files,
        )

    python = config.targeted_test_command[0]
    commands = {
        "syntax": (
            python,
            "-c",
            "import pathlib,sys; p=pathlib.Path(sys.argv[1]); "
            "compile(p.read_text(encoding='utf-8'), str(p), 'exec')",
            "more_itertools/recipes.py",
        ),
        "import": (
            python,
            "-c",
            "from more_itertools.recipes import triplewise",
        ),
        "targeted_tests": config.targeted_test_command,
        "full_tests": config.full_test_command,
        "invariants": config.invariant_test_command,
    }
    results: dict[str, object] = {}
    passed = True
    for name, command in commands.items():
        if command is None:
            continue
        print(f"[Sandbox Smoke] {name}")
        result = evaluator.functional_test(
            workspace, command, run_dir / "commands" / name
        )
        results[name] = result.to_dict()
        passed = passed and result.passed
        if not result.passed:
            break

    if passed:
        print("[Sandbox Smoke] fixed pyperf benchmark")
        performance = evaluator.performance_test(
            workspace,
            (
                python,
                str(PROJECT_ROOT / "subjects" / "more_itertools" / "bench_triplewise.py"),
                "--fast",
                "-o",
                "{output}",
            ),
            run_dir / "performance" / "pyperf.json",
        )
        results["performance"] = performance.to_dict()
        passed = passed and performance.passed

    if passed:
        print("[Sandbox Smoke] fixed resource measurement")
        resources = evaluator.resource_test(
            workspace,
            (
                python,
                str(
                    PROJECT_ROOT
                    / "subjects"
                    / "more_itertools"
                    / "measure_triplewise.py"
                ),
                "--output",
                "{output}",
            ),
            run_dir / "resources" / "resource_workload.json",
        )
        results["resources"] = resources.to_dict()
        passed = passed and resources.passed

    if passed and args.benchmark:
        print("[Sandbox Smoke] generated benchmark validation")
        validation = validate_generated_benchmark(
            benchmark_path=args.benchmark.resolve(),
            result_path=run_dir / "generated" / "pyperf.json",
            workspace=workspace,
            python=python,
            target_symbol="more_itertools.recipes.triplewise",
            project_root=PROJECT_ROOT,
            timeout_seconds=config.timeout_seconds,
            fast_mode=True,
            command_runner=evaluator.run,
        )
        results["generated_benchmark"] = validation.to_dict()
        passed = passed and validation.passed
        if passed and validation.primary_benchmark:
            print("[Sandbox Smoke] generated benchmark resource measurement")
            generated_resources = evaluator.resource_test(
                workspace,
                (
                    python,
                    str(PROJECT_ROOT / "scripts" / "measure_generated_benchmark.py"),
                    "--benchmark",
                    str(args.benchmark.resolve()),
                    "--primary",
                    validation.primary_benchmark,
                    "--output",
                    "{output}",
                ),
                run_dir / "generated_resources" / "resource_workload.json",
            )
            results["generated_resources"] = generated_resources.to_dict()
            passed = passed and generated_resources.passed

    (run_dir / "summary.json").write_text(
        json.dumps({"passed": passed, "results": results}, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.rmtree(workspace)
    print(f"[Complete] passed={passed} artifacts={run_dir}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
