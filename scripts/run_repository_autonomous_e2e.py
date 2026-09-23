#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmark.analyzer import write_json  # noqa: E402
from src.framework.agents import AgentOutput, FrameworkAgents  # noqa: E402
from src.framework.config import FrameworkConfig  # noqa: E402
from src.framework.evaluator import Evaluator  # noqa: E402
from src.framework.generated_benchmark import sha256_file  # noqa: E402
from src.framework.hotspots import parse_cprofile  # noqa: E402
from src.framework.pipeline import OptimizationFramework  # noqa: E402
from src.framework.repository import RepositoryManager  # noqa: E402
from src.framework.sandbox import SandboxLimits  # noqa: E402
from src.framework.workloads import (  # noqa: E402
    TestScenario,
    discover_workload_candidates,
    extract_test_scenarios,
)
from src.llm.deepseek_client import DeepSeekClient  # noqa: E402


def _agent_record(output: AgentOutput) -> dict[str, Any]:
    return {
        "actual_model": output.actual_model,
        "usage": output.usage,
        "system_prompt": output.system_prompt,
        "prompt": output.prompt,
        "raw_response": output.content,
    }


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.find("\n")
        last_fence = stripped.rfind("```")
        if first_newline >= 0 and last_fence > first_newline:
            stripped = stripped[first_newline + 1 : last_fence].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        raise ValueError("DeepSeek did not return a JSON object")
    value = json.loads(stripped[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("DeepSeek selection must be a JSON object")
    return value


def _repository_overview(workspace: Path) -> str:
    for name in ("README.md", "README.rst", "README.txt", "README"):
        path = workspace / name
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")[:8000]
    return "No repository README was found."


def _imports_context(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    parts: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            segment = ast.get_source_segment(source, node)
            if segment:
                parts.append(segment)
    return "\n".join(parts)


def _scenario_catalog(
    workspace: Path, discovery: dict[str, Any], limit: int
) -> tuple[list[TestScenario], str]:
    scenarios: list[TestScenario] = []
    for candidate in discovery["candidates"]:
        if candidate["source"] not in {"existing_benchmark", "existing_test"}:
            continue
        scenarios.extend(
            extract_test_scenarios(
                workspace,
                Path(candidate["path"]),
                None,
                source_kind=str(candidate["source"]),
            )
        )
    priority = {"existing_benchmark": 0, "existing_test": 1}
    scenarios.sort(
        key=lambda item: (
            priority.get(item.source, 2),
            -item.assertion_count,
            len(item.source_code),
            item.scenario_id,
        )
    )
    scenarios = scenarios[:limit]
    catalog = [
        {
            "scenario_id": item.scenario_id,
            "source": item.source,
            "path": item.source_path,
            "symbol": item.source_symbol,
            "called_names": list(item.called_names),
            "assertion_count": item.assertion_count,
        }
        for item in scenarios
    ]
    return scenarios, json.dumps(catalog, ensure_ascii=False, indent=2)


def _failure(stage: str, result: Any) -> dict[str, Any]:
    return {
        "stage": stage,
        "command": result.command,
        "return_code": result.return_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _validate_candidate(
    *,
    candidate: Path,
    workspace: Path,
    attempt_dir: Path,
    evaluator: Evaluator,
) -> tuple[bool, dict[str, Any], dict[str, Any] | None]:
    python = str(PROJECT_ROOT / ".venv" / "bin" / "python")
    syntax = evaluator.run(
        (
            python,
            "-c",
            "import pathlib,sys; p=pathlib.Path(sys.argv[1]); "
            "compile(p.read_text(encoding='utf-8'), str(p), 'exec')",
            str(candidate),
        ),
        workspace,
        attempt_dir,
    )
    write_json(attempt_dir / "syntax.json", syntax.to_dict())
    if not syntax.passed:
        return False, _failure("syntax", syntax), None

    contract = evaluator.run(
        (
            python,
            str(PROJECT_ROOT / "scripts" / "validate_repository_workload.py"),
            str(candidate),
        ),
        workspace,
        attempt_dir,
    )
    write_json(attempt_dir / "contract.json", contract.to_dict())
    if not contract.passed:
        return False, _failure("contract", contract), None
    try:
        metadata = json.loads(contract.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        return False, {"stage": "contract_json", "error": str(exc)}, None

    evaluator.primary_benchmark = str(metadata["primary_benchmark"])
    performance = evaluator.performance_test(
        workspace,
        (python, str(candidate), "--fast", "-o", "{output}"),
        attempt_dir / "validation.pyperf.json",
    )
    write_json(attempt_dir / "performance.json", performance.to_dict())
    if not performance.passed:
        return False, _failure("runtime", performance.command_result), metadata

    profile_path = attempt_dir / "profile.prof"
    profile = evaluator.run(
        (
            python,
            str(PROJECT_ROOT / "scripts" / "profile_generated_workload.py"),
            "--benchmark",
            str(candidate),
            "--primary",
            str(metadata["primary_benchmark"]),
            "--output",
            str(profile_path),
        ),
        workspace,
        attempt_dir,
    )
    write_json(attempt_dir / "profile_command.json", profile.to_dict())
    if not profile.passed or not profile_path.is_file():
        return False, _failure("profile", profile), metadata
    hotspots = parse_cprofile(
        profile_path,
        workspace,
        limit=5,
        recorded_repository=Path("/workspace"),
    )
    write_json(attempt_dir / "hotspots.json", hotspots)
    if not hotspots["hotspots"]:
        return False, {
            "stage": "profile",
            "error": "No repository production hotspot was found",
        }, metadata
    metadata["hotspots"] = hotspots["hotspots"]
    return True, {"stage": "complete"}, metadata


def _report(
    *,
    resolved: str,
    selection: dict[str, Any],
    scenario: TestScenario,
    metadata: dict[str, Any],
    optimization_dir: Path,
) -> str:
    top = metadata["hotspots"][0]
    return "\n".join(
        [
            "# 仓库级自主 Workload 闭环实验",
            "",
            "本实验没有向 workload agent 或 profiler 提供目标函数名。",
            "",
            f"- Baseline：`{resolved}`",
            f"- DeepSeek 自选证据：`{scenario.source_path}::{scenario.source_symbol}`",
            f"- 选择理由：{selection['reason']}",
            f"- 生成 workload：{metadata['workload_description']}",
            f"- 动态命中生产代码数量：{metadata['production_hit_count']}",
            f"- profiler 自动 Top 1：`{top['qualified_name']}`",
            f"- profiler 自动文件：`{top['file']}`",
            "- workload 可信度：自动验收通过，但尚未声明代表生产流量",
            f"- 后续优化闭环：`{optimization_dir}`",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run repository -> LLM workload -> profiler -> optimization E2E."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "more_itertools_repository_autonomous_e2e.yaml",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    discovery_settings = raw.get("workload_discovery") or {}
    config = FrameworkConfig.load(args.config, PROJECT_ROOT)
    client = DeepSeekClient.from_environment(
        temperature=config.temperature, timeout_seconds=config.timeout_seconds
    )
    if client.model != config.model:
        raise RuntimeError(
            f"Configured model is {config.model!r}, but DEEPSEEK_MODEL is {client.model!r}"
        )
    execution = config.execution_sandbox
    if execution is None:
        raise RuntimeError("Autonomous workload validation requires execution_sandbox")
    limits = SandboxLimits(
        cpus=execution.cpus,
        memory=execution.memory,
        pids=execution.pids,
        timeout_seconds=execution.timeout_seconds,
        max_output_bytes=execution.max_output_bytes,
    )
    evaluator = Evaluator(
        config.timeout_seconds,
        docker_image=execution.image,
        project_root=PROJECT_ROOT,
        sandbox_limits=limits,
    )
    agents = FrameworkAgents(client, PROJECT_ROOT / "prompts")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_root = config.artifacts_root / stamp
    builder = run_root / "workload_builder"
    workspace = builder / "workspace"
    builder.mkdir(parents=True, exist_ok=False)
    try:
        print("[Repository] checkout pinned baseline", flush=True)
        resolved = RepositoryManager(config).checkout(workspace, config.baseline_commit)
        print("[Workload] scan repository evidence", flush=True)
        discovery = discover_workload_candidates(
            workspace, limit=int(discovery_settings.get("file_limit", 50))
        )
        scenarios, catalog = _scenario_catalog(
            workspace,
            discovery,
            int(discovery_settings.get("scenario_limit", 200)),
        )
        if not scenarios:
            raise RuntimeError("Repository scan found no benchmark or testcase scenarios")
        write_json(builder / "discovery.json", discovery)
        write_json(
            builder / "scenario_catalog.json",
            [scenario.to_dict() for scenario in scenarios],
        )

        overview = _repository_overview(workspace)
        print(f"[Workload Agent] select from {len(scenarios)} scenarios", flush=True)
        selection_output = agents.select_repository_workload(
            repository_overview=overview,
            scenario_catalog=catalog,
        )
        write_json(builder / "selection_llm.json", _agent_record(selection_output))
        selection = _parse_json_object(selection_output.content)
        by_id = {item.scenario_id: item for item in scenarios}
        scenario_id = str(selection.get("scenario_id", ""))
        if scenario_id not in by_id:
            raise RuntimeError(f"DeepSeek selected unknown scenario_id: {scenario_id!r}")
        scenario = by_id[scenario_id]
        selection["reason"] = str(selection.get("reason", "")).strip()
        if not selection["reason"]:
            raise RuntimeError("DeepSeek workload selection omitted its reason")
        write_json(builder / "selection.json", selection)
        write_json(builder / "selected_scenario.json", scenario.to_dict())

        imports = _imports_context(workspace / scenario.source_path)
        candidate = builder / "generated_workload.py"
        benchmark_code = ""
        metadata: dict[str, Any] | None = None
        max_repairs = int(discovery_settings.get("max_repairs", 3))
        for attempt in range(max_repairs + 1):
            print(f"[Workload Agent] generate/repair attempt {attempt}", flush=True)
            attempt_dir = builder / f"attempt_{attempt:02d}"
            attempt_dir.mkdir()
            if attempt == 0:
                output, benchmark_code = agents.generate_repository_workload(
                    repository_overview=overview,
                    source_path=scenario.source_path,
                    source_symbol=scenario.source_symbol,
                    imports_context=imports,
                    scenario_source=scenario.source_code,
                    selection_reason=selection["reason"],
                )
            else:
                output, benchmark_code = agents.repair_repository_workload(
                    repository_overview=overview,
                    source_path=scenario.source_path,
                    source_symbol=scenario.source_symbol,
                    imports_context=imports,
                    scenario_source=scenario.source_code,
                    benchmark_code=benchmark_code,
                    failure=failure,
                )
            write_json(attempt_dir / "llm.json", _agent_record(output))
            candidate.write_text(benchmark_code, encoding="utf-8")
            (attempt_dir / "candidate.py").write_text(
                benchmark_code, encoding="utf-8"
            )
            passed, failure, metadata = _validate_candidate(
                candidate=candidate,
                workspace=workspace,
                attempt_dir=attempt_dir,
                evaluator=evaluator,
            )
            write_json(
                attempt_dir / "validation.json",
                {"passed": passed, "failure": failure, "metadata": metadata},
            )
            if passed:
                break
        else:
            raise RuntimeError("DeepSeek could not produce a valid repository workload")
        assert metadata is not None

        locked = run_root / "locked_workload"
        locked.mkdir()
        shutil.copy2(candidate, locked / "generated_workload.py")
        shutil.copy2(
            PROJECT_ROOT / "scripts" / "profile_generated_workload.py",
            locked / "profile_generated_workload.py",
        )
        provenance = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "baseline_commit": resolved,
            "model": client.model,
            "target_hint_supplied": False,
            "oracle_symbol_supplied": False,
            "selection": selection,
            "scenario": scenario.to_dict(),
            "automatic_validation_passed": True,
            "human_confirmed": False,
            "script_sha256": sha256_file(locked / "generated_workload.py"),
            "validation": metadata,
        }
        write_json(locked / "provenance.json", provenance)

        dynamic = dict(raw)
        dynamic.pop("workload_discovery", None)
        dynamic["target_mode"] = "auto"
        dynamic.pop("target_file", None)
        dynamic.pop("target_symbol", None)
        dynamic["editable_files"] = []
        dynamic["human_fix_commit"] = None
        dynamic["context_files"] = list(metadata["source_evidence"])
        dynamic["hotspot_discovery"] = {
            "harness": str(locked),
            "command": [
                "python",
                "/harness/profile_generated_workload.py",
                "--benchmark",
                "/harness/generated_workload.py",
                "--primary",
                str(metadata["primary_benchmark"]),
                "--output",
                "/artifacts/profile.prof",
            ],
            "image": execution.image,
            "limit": 5,
            "cpus": execution.cpus,
            "memory": execution.memory,
            "pids": execution.pids,
            "timeout_seconds": execution.timeout_seconds,
            "max_output_bytes": execution.max_output_bytes,
            "validation_expected_symbol": None,
        }
        dynamic["benchmark_mode"] = "fixed"
        dynamic["benchmark_command"] = [
            "{python}",
            str(locked / "generated_workload.py"),
            "-o",
            "{output}",
        ]
        dynamic["primary_benchmark"] = str(metadata["primary_benchmark"])
        dynamic["artifacts_root"] = str(run_root / "optimization")
        dynamic_path = run_root / "resolved_config.yaml"
        dynamic_path.write_text(
            yaml.safe_dump(dynamic, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        shutil.rmtree(workspace)

        print("[Optimization] profiler selects target; start closed loop", flush=True)
        resolved_config = FrameworkConfig.load(dynamic_path, PROJECT_ROOT)
        optimization = OptimizationFramework(
            project_root=PROJECT_ROOT,
            config=resolved_config,
            agents=agents,
            evaluator=Evaluator(
                resolved_config.timeout_seconds,
                primary_benchmark=resolved_config.primary_benchmark,
                docker_image=execution.image,
                project_root=PROJECT_ROOT,
                sandbox_limits=limits,
            ),
            model_name=client.model,
        ).run()
        write_json(
            run_root / "summary.json",
            {
                "status": "COMPLETE",
                "baseline_commit": resolved,
                "target_hint_supplied": False,
                "selection": selection,
                "selected_scenario": scenario.to_dict(),
                "workload_validation": metadata,
                "optimization_artifacts": str(optimization),
            },
        )
        (run_root / "REPORT_ZH.md").write_text(
            _report(
                resolved=resolved,
                selection=selection,
                scenario=scenario,
                metadata=metadata,
                optimization_dir=optimization,
            ),
            encoding="utf-8",
        )
    finally:
        if workspace.exists():
            shutil.rmtree(workspace)

    print(f"[Complete] artifacts: {run_root}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Autonomous E2E failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
