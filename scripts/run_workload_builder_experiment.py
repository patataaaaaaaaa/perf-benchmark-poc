#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.agents import AgentOutput, FrameworkAgents  # noqa: E402
from src.framework.config import FrameworkConfig  # noqa: E402
from src.framework.evaluator import Evaluator  # noqa: E402
from src.framework.generated_benchmark import (  # noqa: E402
    GeneratedBenchmarkValidation,
    validate_generated_benchmark,
)
from src.framework.hotspots import parse_cprofile  # noqa: E402
from src.framework.patching import extract_symbol_context  # noqa: E402
from src.framework.repository import RepositoryManager  # noqa: E402
from src.framework.sandbox import SandboxLimits, run_in_docker  # noqa: E402
from src.framework.workloads import (  # noqa: E402
    WorkloadSpec,
    assess_workload_fidelity,
    extract_test_scenarios,
    workload_script_sha256,
)
from src.llm.deepseek_client import DeepSeekClient  # noqa: E402


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _write_agent_record(path: Path, output: AgentOutput) -> None:
    _write_json(
        path,
        {
            "actual_model": output.actual_model,
            "usage": output.usage,
            "system_prompt": output.system_prompt,
            "prompt": output.prompt,
            "raw_response": output.content,
        },
    )


def _profile_once(
    *,
    workspace: Path,
    output: Path,
    image: str,
    limits: SandboxLimits,
    harness: Path,
    command: list[str],
    readonly_mounts: tuple[tuple[Path, str], ...] = (),
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    result = run_in_docker(
        image=image,
        workspace=workspace,
        harness=harness,
        output=output,
        inner_command=command,
        limits=limits,
        readonly_mounts=readonly_mounts,
    )
    _write_json(output / "sandbox.json", result.to_dict())
    (output / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (output / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.timed_out or result.return_code != 0:
        raise RuntimeError(
            f"Profiler run failed (exit={result.return_code}, timeout={result.timed_out}); "
            f"see {output / 'stderr.txt'}"
        )
    profile = output / "profile.prof"
    if not profile.is_file():
        raise RuntimeError(f"Profiler did not create {profile}")
    report = parse_cprofile(
        profile,
        workspace,
        limit=5,
        recorded_repository=Path("/workspace"),
    )
    _write_json(output / "hotspots.json", report)
    return report


def _rank(report: dict[str, Any], symbol: str) -> int | None:
    for item in report.get("hotspots", []):
        if item.get("qualified_name") == symbol:
            return int(item["rank"])
    return None


def _summarize_profiles(
    reports: list[dict[str, Any]], expected_symbol: str
) -> dict[str, Any]:
    top1 = [
        report["hotspots"][0]["qualified_name"] if report.get("hotspots") else None
        for report in reports
    ]
    ranks = [_rank(report, expected_symbol) for report in reports]
    top5_sets = [
        {item["qualified_name"] for item in report.get("hotspots", [])}
        for report in reports
    ]
    common_top5 = set.intersection(*top5_sets) if top5_sets else set()
    union_top5 = set.union(*top5_sets) if top5_sets else set()
    return {
        "repetitions": len(reports),
        "top1_names": top1,
        "top1_consistent": bool(top1) and len(set(top1)) == 1,
        "expected_symbol": expected_symbol,
        "expected_ranks": ranks,
        "expected_in_top5_count": sum(rank is not None for rank in ranks),
        "common_top5": sorted(common_top5),
        "top5_jaccard_all_runs": (
            len(common_top5) / len(union_top5) if union_top5 else None
        ),
    }


def _compare_sources(
    manual: list[dict[str, Any]], derived: list[dict[str, Any]]
) -> dict[str, Any]:
    comparisons: list[dict[str, Any]] = []
    for index, (left, right) in enumerate(zip(manual, derived), start=1):
        left_names = [item["qualified_name"] for item in left.get("hotspots", [])]
        right_names = [item["qualified_name"] for item in right.get("hotspots", [])]
        union = set(left_names) | set(right_names)
        overlap = set(left_names) & set(right_names)
        comparisons.append(
            {
                "repetition": index,
                "same_top1": bool(left_names and right_names)
                and left_names[0] == right_names[0],
                "manual_top1": left_names[0] if left_names else None,
                "derived_top1": right_names[0] if right_names else None,
                "top5_overlap": sorted(overlap),
                "top5_jaccard": len(overlap) / len(union) if union else None,
            }
        )
    return {
        "paired_repetitions": len(comparisons),
        "same_top1_count": sum(item["same_top1"] for item in comparisons),
        "pairs": comparisons,
    }


def _report_markdown(summary: dict[str, Any]) -> str:
    reference = summary["reference_workload"]
    derived = summary["repository_derived_workload"]
    comparison = summary["comparison"]
    outcome = (
        "通过"
        if derived["expected_in_top5_count"] == derived["repetitions"]
        and derived["top1_consistent"]
        and comparison["same_top1_count"] == comparison["paired_repetitions"]
        else "未通过"
    )
    return "\n".join(
        [
            "# Workload Builder 受控实验报告",
            "",
            f"结论：**{outcome}**。这是仓库证据派生 workload 的自动验收结果，"
            "不等于人工确认其代表真实业务场景。",
            "",
            f"- Baseline commit：`{summary['baseline_commit']}`",
            f"- 候选来源：`{summary['scenario']['source']}`",
            f"- 提取位置：`{summary['scenario']['source_path']}::{summary['scenario']['source_symbol']}`",
            f"- 目标函数：`{summary['target_symbol']}`",
            f"- 生成脚本自动验收：`{summary['workload_spec']['automatic_validation_passed']}`",
            f"- 人工确认：`{summary['workload_spec']['human_confirmed']}`",
            "",
            "## 三次 profiler 结果",
            "",
            f"- 参考 workload Top1：`{reference['top1_names']}`",
            f"- 仓库证据派生 workload Top1：`{derived['top1_names']}`",
            f"- 派生 workload 中目标函数排名：`{derived['expected_ranks']}`",
            f"- 两类 workload 同轮 Top1 相同次数：`{comparison['same_top1_count']}` / "
            f"`{comparison['paired_repetitions']}`",
            f"- 派生 workload 三次 Top5 交并比：`{derived['top5_jaccard_all_runs']}`",
            "",
            "## 如何理解",
            "",
            "本实验验证的是：框架能否从仓库已有 benchmark 或 testcase 中提取证据，"
            "交给 DeepSeek 放大成可测量脚本，并在沙箱中稳定定位到与参考 workload "
            "相同的核心热点。"
            "它还没有证明该脚本代表用户的真实生产流量，因此 `human_confirmed` 保持为 false。",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Controlled testcase-to-workload builder experiment."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "more_itertools_triplewise_auto_e2e.yaml",
    )
    parser.add_argument(
        "--source-file",
        "--test-file",
        dest="source_file",
        type=Path,
        default=Path("tests/test_recipes.py"),
    )
    parser.add_argument(
        "--source-kind",
        choices=("existing_test", "existing_benchmark", "example"),
        default="existing_test",
    )
    parser.add_argument("--scenario-symbol")
    parser.add_argument("--query", default="triplewise")
    parser.add_argument(
        "--target-symbol", default="more_itertools.recipes.triplewise"
    )
    parser.add_argument(
        "--target-file", type=Path, default=Path("more_itertools/recipes.py")
    )
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument(
        "--reuse-generated",
        type=Path,
        help="Reuse an existing generated workload and skip all DeepSeek calls.",
    )
    parser.add_argument(
        "--reference-script",
        type=Path,
        default=PROJECT_ROOT / "subjects" / "more_itertools" / "profile_triplewise_workload.py",
    )
    parser.add_argument(
        "--reference-arg",
        action="append",
        help="Argument passed to the reference script; repeat for multiple arguments.",
    )
    parser.add_argument(
        "--reference-id", default="more_itertools_triplewise_issue_889_manual_v1"
    )
    parser.add_argument(
        "--reference-source", default="historical_issue_manual_translation"
    )
    parser.add_argument(
        "--reference-description",
        default="Fully consume triplewise(repeat(None, 1_000_000)).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repetitions < 1:
        raise ValueError("--repetitions must be at least 1")
    config = FrameworkConfig.load(args.config, PROJECT_ROOT)
    execution = config.execution_sandbox
    if execution is None:
        raise RuntimeError("This experiment requires execution_sandbox")
    client: DeepSeekClient | None = None
    if args.reuse_generated is None:
        client = DeepSeekClient.from_environment(
            temperature=config.temperature, timeout_seconds=config.timeout_seconds
        )
        if client.model != config.model:
            raise RuntimeError(
                f"Configured model is {config.model!r}, but DEEPSEEK_MODEL is {client.model!r}"
            )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = PROJECT_ROOT / "artifacts" / "workload_builder" / stamp
    workspace = run_dir / "workspace"
    run_dir.mkdir(parents=True, exist_ok=False)
    limits = SandboxLimits(
        cpus=execution.cpus,
        memory=execution.memory,
        pids=execution.pids,
        timeout_seconds=execution.timeout_seconds,
        max_output_bytes=execution.max_output_bytes,
    )

    try:
        print("[Prepare] checkout pinned baseline")
        resolved = RepositoryManager(config).checkout(workspace, config.baseline_commit)
        print("[Extract] find testcase scenario")
        scenarios = extract_test_scenarios(
            workspace,
            args.source_file,
            args.query,
            source_kind=args.source_kind,
            scenario_symbol=args.scenario_symbol,
        )
        if not scenarios:
            raise RuntimeError(
                f"No scenario in {args.source_file} calls query {args.query!r}"
            )
        if len(scenarios) != 1:
            raise RuntimeError(
                f"Controlled experiment expected one matching test block, found {len(scenarios)}"
            )
        scenario = scenarios[0]
        _write_json(run_dir / "extracted_scenario.json", scenario.to_dict())
        (run_dir / "extracted_scenario.py.txt").write_text(
            scenario.source_code + "\n", encoding="utf-8"
        )

        source_context = extract_symbol_context(
            (workspace / args.target_file).read_text(encoding="utf-8"),
            args.target_symbol,
        )
        agents = FrameworkAgents(client, PROJECT_ROOT / "prompts") if client else None
        candidate_dir = run_dir / "repository_derived"
        candidate_dir.mkdir()
        benchmark_path = candidate_dir / "generated_workload.py"
        validation: GeneratedBenchmarkValidation | None = None
        benchmark_code = ""

        max_attempts = (
            1 if args.reuse_generated else config.benchmark_generation_max_repairs + 1
        )
        for attempt in range(max_attempts):
            print(f"[Generate] repository-derived workload attempt {attempt}")
            if attempt == 0:
                if args.reuse_generated:
                    reused = args.reuse_generated.expanduser().resolve()
                    benchmark_code = reused.read_text(encoding="utf-8")
                    output = None
                else:
                    assert agents is not None
                    output, benchmark_code = agents.generate_benchmark(
                        target_symbol=args.target_symbol,
                        source_context=source_context,
                        tests_context=scenario.source_code,
                    )
            else:
                assert validation is not None
                assert agents is not None
                output, benchmark_code = agents.repair_benchmark(
                    target_symbol=args.target_symbol,
                    source_context=source_context,
                    tests_context=scenario.source_code,
                    benchmark_code=benchmark_code,
                    failure=validation.failure_evidence(),
                )
            attempt_dir = candidate_dir / f"attempt_{attempt:02d}"
            attempt_dir.mkdir()
            if output is not None:
                _write_agent_record(attempt_dir / "llm.json", output)
            else:
                _write_json(
                    attempt_dir / "reuse.json",
                    {
                        "llm_called": False,
                        "source": str(reused),
                        "source_sha256": workload_script_sha256(reused),
                    },
                )
            (attempt_dir / "candidate.py").write_text(
                benchmark_code, encoding="utf-8"
            )
            benchmark_path.write_text(benchmark_code, encoding="utf-8")

            evaluator = Evaluator(
                config.timeout_seconds,
                docker_image=execution.image,
                project_root=PROJECT_ROOT,
                sandbox_limits=limits,
            )
            validation = validate_generated_benchmark(
                benchmark_path=benchmark_path,
                result_path=attempt_dir / "validation.pyperf.json",
                workspace=workspace,
                python=str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                target_symbol=args.target_symbol,
                project_root=PROJECT_ROOT,
                timeout_seconds=config.timeout_seconds,
                fast_mode=True,
                command_runner=evaluator.run,
            )
            _write_json(attempt_dir / "validation.json", validation.to_dict())
            if validation.passed:
                break
        if validation is None or not validation.passed:
            raise RuntimeError("DeepSeek workload did not pass automatic validation")
        assert validation.primary_benchmark is not None
        assert validation.workload is not None
        fidelity = assess_workload_fidelity(scenario.source_code, benchmark_code)
        _write_json(candidate_dir / "fidelity.json", fidelity.to_dict())

        workload_spec = WorkloadSpec(
            workload_id=f"{config.task_id}_{scenario.source_symbol}_derived_v1",
            source=f"{scenario.source}+llm_adapted",
            source_path=scenario.source_path,
            source_symbol=scenario.source_symbol,
            script_path=str(benchmark_path.relative_to(run_dir)),
            command=(
                "python",
                "/harness/run_generated_workload.py",
                "--benchmark",
                "/candidate/generated_workload.py",
                "--primary",
                validation.primary_benchmark,
            ),
            target_symbol=args.target_symbol,
            input_description=str(validation.workload["workload_description"]),
            expected_behavior="Every case returns its frozen positive integer checksum.",
            confidence="medium",
            adaptation_type=fidelity.adaptation_type,
            fidelity_status=fidelity.fidelity_status,
            llm_adapted=True,
            automatic_validation_passed=True,
            human_confirmed=False,
            experiment_locked=True,
            frozen=False,
            script_sha256=workload_script_sha256(benchmark_path),
        )
        _write_json(candidate_dir / "workload_spec.json", workload_spec.to_dict())

        reference_script = args.reference_script.expanduser().resolve()
        if not reference_script.is_file():
            raise FileNotFoundError(f"Reference workload is missing: {reference_script}")
        reference_args = args.reference_arg
        if reference_args is None and reference_script.name == "profile_triplewise_workload.py":
            reference_args = ["--size", "1000000"]
        reference_args = reference_args or []
        reference_spec = {
            "workload_id": args.reference_id,
            "source": args.reference_source,
            "script_path": str(reference_script),
            "target_symbol": args.target_symbol,
            "input_description": args.reference_description,
            "automatic_validation_passed": True,
            "human_confirmed": True,
            "frozen": True,
            "script_sha256": workload_script_sha256(reference_script),
        }
        _write_json(run_dir / "reference_workload_spec.json", reference_spec)

        print(f"[Profile] compare both workloads, {args.repetitions} repetitions each")
        reference_reports: list[dict[str, Any]] = []
        derived_reports: list[dict[str, Any]] = []
        for repetition in range(1, args.repetitions + 1):
            reference_reports.append(
                _profile_once(
                    workspace=workspace,
                    output=run_dir / "reference" / f"profile_{repetition:02d}",
                    image=execution.image,
                    limits=limits,
                    harness=reference_script.parent,
                    command=[
                        "python",
                        "-m",
                        "cProfile",
                        "-o",
                        "/artifacts/profile.prof",
                        f"/harness/{reference_script.name}",
                        *reference_args,
                    ],
                )
            )
            derived_reports.append(
                _profile_once(
                    workspace=workspace,
                    output=candidate_dir / f"profile_{repetition:02d}",
                    image=execution.image,
                    limits=limits,
                    harness=PROJECT_ROOT / "scripts",
                    command=[
                        "python",
                        "/harness/profile_generated_workload.py",
                        "--benchmark",
                        "/candidate/generated_workload.py",
                        "--primary",
                        validation.primary_benchmark,
                        "--output",
                        "/artifacts/profile.prof",
                    ],
                    readonly_mounts=((candidate_dir, "/candidate"),),
                )
            )

        summary = {
            "schema_version": 1,
            "baseline_commit": resolved,
            "target_symbol": args.target_symbol,
            "scenario": scenario.to_dict(),
            "workload_spec": workload_spec.to_dict(),
            "reference_workload": _summarize_profiles(
                reference_reports, args.target_symbol
            ),
            "repository_derived_workload": _summarize_profiles(
                derived_reports, args.target_symbol
            ),
            "comparison": _compare_sources(reference_reports, derived_reports),
        }
        _write_json(run_dir / "summary.json", summary)
        (run_dir / "REPORT_ZH.md").write_text(
            _report_markdown(summary), encoding="utf-8"
        )
    finally:
        if workspace.exists():
            shutil.rmtree(workspace)

    print(f"[Complete] artifacts: {run_dir}")
    print(f"Report: {run_dir / 'REPORT_ZH.md'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Workload builder failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
