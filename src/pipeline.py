from __future__ import annotations

import importlib.metadata
import logging
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.benchmark.analyzer import summarize, write_json, write_summary_csv
from src.benchmark.generator import BenchmarkGenerator
from src.benchmark.validator import CandidateValidation, validate_candidate
from src.llm.deepseek_client import DeepSeekClient
from src.target.loader import TargetSpec, collect_target_context, load_targets


LOGGER = logging.getLogger("perf_benchmark_poc")


@dataclass(frozen=True)
class PocConfig:
    max_retries: int
    timeout_seconds: int
    fast_mode: bool
    temperature: float
    artifacts_root: Path

    @classmethod
    def load(cls, config_path: Path, project_root: Path) -> "PocConfig":
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        artifacts = Path(raw.get("artifacts", {}).get("root", "artifacts"))
        if not artifacts.is_absolute():
            artifacts = project_root / artifacts
        return cls(
            max_retries=int(raw.get("experiment", {}).get("max_retries", 3)),
            timeout_seconds=int(raw.get("runtime", {}).get("timeout_seconds", 120)),
            fast_mode=bool(raw.get("pyperf", {}).get("fast_mode", True)),
            temperature=float(raw.get("llm", {}).get("temperature", 0)),
            artifacts_root=artifacts,
        )


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _git_sha(project_root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _validation_outputs(validation: CandidateValidation) -> tuple[str, str]:
    stdout_sections: list[str] = []
    stderr_sections: list[str] = []
    for result in (
        validation.syntax,
        validation.import_check,
        validation.runtime,
        validation.stability,
    ):
        if result is None:
            continue
        stdout_sections.append(f"[{result.stage}]\n{result.stdout}")
        stderr_sections.append(f"[{result.stage}]\n{result.stderr}")
    return "\n".join(stdout_sections), "\n".join(stderr_sections)


def _empty_final(spec: TargetSpec, status: str) -> dict[str, Any]:
    return {
        "target_id": spec.id,
        "target_name": spec.target,
        "generated": False,
        "initial_syntax_pass": False,
        "initial_import_pass": False,
        "initial_runtime_pass": False,
        "repair_attempts": 0,
        "repair_success": False,
        "final_syntax_pass": False,
        "final_import_pass": False,
        "final_runtime_pass": False,
        "final_stability_pass": False,
        "target_hit": "unknown",
        "status": status,
    }


class PocPipeline:
    def __init__(
        self,
        project_root: Path,
        config: PocConfig,
        generator: BenchmarkGenerator,
        model_name: str | None,
        dry_run: bool = False,
    ) -> None:
        self.project_root = project_root
        self.config = config
        self.generator = generator
        self.model_name = model_name
        self.dry_run = dry_run

    def _write_metadata(self, run_dir: Path, run_id: str) -> None:
        metadata = {
            "run_id": run_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "sympy_version": _package_version("sympy"),
            "pyperf_version": _package_version("pyperf"),
            "openai_version": _package_version("openai"),
            "llm_model": self.model_name,
            "temperature": self.config.temperature,
            "max_retries": self.config.max_retries,
            "timeout_seconds": self.config.timeout_seconds,
            "pyperf_fast_mode": self.config.fast_mode,
            "git_commit_sha": _git_sha(self.project_root),
            "dry_run": self.dry_run,
        }
        write_json(run_dir / "run_metadata.json", metadata)

    def run(self, targets: list[TargetSpec]) -> Path:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run_dir = self.config.artifacts_root / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        self._write_metadata(run_dir, run_id)

        final_results: list[dict[str, Any]] = []
        for spec in targets:
            LOGGER.info("[Target] %s", spec.id)
            final_results.append(self._run_target(spec, run_dir))

        summary = summarize(final_results)
        write_json(run_dir / "summary.json", summary)
        write_summary_csv(run_dir / "summary.csv", final_results)
        LOGGER.info("[Summary] %s", run_dir / "summary.json")
        return run_dir

    def _run_target(self, spec: TargetSpec, run_dir: Path) -> dict[str, Any]:
        target_dir = run_dir / spec.id
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            context = collect_target_context(spec)
        except Exception as exc:
            final = _empty_final(spec, "GENERATION_FAILED")
            write_json(target_dir / "target.json", spec.to_dict())
            (target_dir / "context_error.txt").write_text(
                f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
            )
            write_json(target_dir / "final.json", final)
            LOGGER.error("[Target] context collection failed: %s", exc)
            return final

        write_json(target_dir / "target.json", context.to_dict())
        generation_prompt = self.generator.render_generate_prompt(context)
        (target_dir / "generation_prompt.txt").write_text(
            generation_prompt, encoding="utf-8"
        )
        if self.dry_run:
            final = _empty_final(spec, "DRY_RUN")
            write_json(target_dir / "final.json", final)
            LOGGER.info("[DryRun] prompt rendered; LLM was not called")
            return final

        try:
            LOGGER.info("[Generate] requesting DeepSeek")
            candidate = self.generator.generate(context)
        except Exception as exc:
            final = _empty_final(spec, "GENERATION_FAILED")
            (target_dir / "generation_error.txt").write_text(
                f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
            )
            write_json(target_dir / "final.json", final)
            LOGGER.error("[Generate] failed: %s", exc)
            return final

        validations: list[CandidateValidation] = []
        for attempt_number in range(self.config.max_retries + 1):
            attempt_dir = target_dir / f"attempt_{attempt_number}"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            response_name = (
                "generation_response.txt"
                if attempt_number == 0
                else "repair_response.txt"
            )
            (attempt_dir / response_name).write_text(
                candidate.raw_response, encoding="utf-8"
            )
            write_json(
                attempt_dir / "llm_metadata.json",
                {
                    "configured_model": self.model_name,
                    "actual_model": candidate.actual_model,
                    "usage": candidate.usage,
                },
            )

            if candidate.skipped:
                final = _empty_final(spec, "SKIPPED")
                final["skip_reason"] = candidate.skip_reason
                final["repair_attempts"] = attempt_number
                write_json(target_dir / "final.json", final)
                LOGGER.info("[Result] SKIPPED: %s", candidate.skip_reason)
                return final

            benchmark_path = attempt_dir / "benchmark.py"
            result_path = attempt_dir / "result.json"
            benchmark_path.write_text(candidate.code or "", encoding="utf-8")
            LOGGER.info(
                "[Validate] attempt %d / %d",
                attempt_number,
                self.config.max_retries,
            )
            validation = validate_candidate(
                benchmark_path=benchmark_path,
                result_path=result_path,
                spec=spec,
                cwd=self.project_root,
                timeout_seconds=self.config.timeout_seconds,
                fast_mode=self.config.fast_mode,
            )
            validations.append(validation)
            write_json(attempt_dir / "validation.json", validation.to_dict())
            stdout, stderr = _validation_outputs(validation)
            (attempt_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
            (attempt_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
            self._log_validation(validation)

            if validation.successful:
                final = self._build_final(spec, validations, "SUCCESS")
                write_json(target_dir / "final.json", final)
                LOGGER.info("[Result] SUCCESS")
                return final

            # Stability is an evaluation outcome, not a correctness diagnostic.
            # In particular, --fast may report too few samples to establish a
            # tight confidence interval. Rewriting valid benchmark code in
            # response can make the workload worse or merely hide the warning.
            if validation.executable:
                final = self._build_final(
                    spec, validations, "EXECUTABLE_UNSTABLE"
                )
                write_json(target_dir / "final.json", final)
                LOGGER.warning("[Result] EXECUTABLE_UNSTABLE")
                return final

            if attempt_number >= self.config.max_retries:
                final = self._build_final(
                    spec, validations, "MAX_RETRIES_EXCEEDED"
                )
                write_json(target_dir / "final.json", final)
                LOGGER.error("[Result] MAX_RETRIES_EXCEEDED")
                return final

            failure = validation.first_failure()
            LOGGER.info(
                "[Repair] attempt %d / %d after %s failure",
                attempt_number + 1,
                self.config.max_retries,
                failure.stage,
            )
            try:
                candidate = self.generator.repair(
                    context=context,
                    benchmark_code=candidate.code or "",
                    validation_stage=failure.stage,
                    command=failure.command_text,
                    return_code=failure.return_code,
                    stdout=failure.stdout,
                    stderr=failure.stderr,
                )
            except Exception as exc:
                final = self._build_final(spec, validations, "VALIDATION_FAILED")
                (attempt_dir / "repair_error.txt").write_text(
                    f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
                )
                write_json(target_dir / "final.json", final)
                LOGGER.error("[Repair] request failed: %s", exc)
                return final

        raise AssertionError("Bounded retry loop terminated unexpectedly")

    @staticmethod
    def _log_validation(validation: CandidateValidation) -> None:
        checks = (
            validation.syntax,
            validation.import_check,
            validation.runtime,
            validation.stability,
        )
        for check in checks:
            if check is not None:
                LOGGER.info(
                    "[Validate:%s] %s",
                    check.stage.capitalize(),
                    "PASS" if check.passed else "FAIL",
                )
        LOGGER.info("[Validate:TargetHit] %s", validation.target_hit.upper())

    @staticmethod
    def _build_final(
        spec: TargetSpec,
        validations: list[CandidateValidation],
        status: str,
    ) -> dict[str, Any]:
        initial = validations[0]
        final_validation = validations[-1]

        def passed(value: Any) -> bool:
            return bool(value is not None and value.passed)

        repair_attempts = max(0, len(validations) - 1)
        return {
            "target_id": spec.id,
            "target_name": spec.target,
            "generated": True,
            "initial_syntax_pass": passed(initial.syntax),
            "initial_import_pass": passed(initial.import_check),
            "initial_runtime_pass": passed(initial.runtime),
            "repair_attempts": repair_attempts,
            # Repair success means that a previously non-executable candidate
            # became executable. Statistical stability is reported separately.
            "repair_success": repair_attempts > 0 and final_validation.executable,
            "final_syntax_pass": passed(final_validation.syntax),
            "final_import_pass": passed(final_validation.import_check),
            "final_runtime_pass": passed(final_validation.runtime),
            "final_stability_pass": passed(final_validation.stability),
            "target_hit": final_validation.target_hit,
            "status": status,
        }


def build_pipeline(
    project_root: Path,
    config_path: Path,
    dry_run: bool,
    max_retries_override: int | None = None,
) -> PocPipeline:
    config = PocConfig.load(config_path, project_root)
    if max_retries_override is not None:
        config = PocConfig(
            **{
                **asdict(config),
                "max_retries": max_retries_override,
            }
        )

    client: DeepSeekClient | None = None
    model_name: str | None = None
    if not dry_run:
        client = DeepSeekClient.from_environment(
            temperature=config.temperature,
            timeout_seconds=config.timeout_seconds,
        )
        model_name = client.model

    generator = BenchmarkGenerator(
        client=client,
        generate_template=project_root / "prompts" / "generate_benchmark.txt",
        repair_template=project_root / "prompts" / "repair_benchmark.txt",
    )
    return PocPipeline(
        project_root=project_root,
        config=config,
        generator=generator,
        model_name=model_name,
        dry_run=dry_run,
    )


def load_selected_targets(
    target_path: Path, target_id: str | None
) -> list[TargetSpec]:
    targets = load_targets(target_path)
    if target_id is None:
        return targets
    selected = [target for target in targets if target.id == target_id]
    if not selected:
        available = ", ".join(target.id for target in targets)
        raise ValueError(f"Unknown target {target_id!r}. Available: {available}")
    return selected
