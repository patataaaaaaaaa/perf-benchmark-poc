import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.benchmark.generator import BenchmarkGenerator
from src.benchmark.validator import CandidateValidation, ValidationResult
from src.llm.deepseek_client import LLMCompletion
from src.pipeline import PocConfig, PocPipeline
from src.target.loader import TargetSpec


class FakeClient:
    def __init__(self) -> None:
        self.responses = iter(
            [
                "this is not valid Python !!!",
                "from sympy import expand\nexpand(1)\n",
            ]
        )

    def complete(self, prompt: str) -> LLMCompletion:
        return LLMCompletion(
            content=next(self.responses),
            actual_model="fake-model-v1",
            input_tokens=100,
            output_tokens=20,
            total_tokens=120,
            cached_tokens=0,
            reasoning_tokens=5,
        )


def check(stage: str, passed: bool) -> ValidationResult:
    return ValidationResult(
        stage=stage,
        passed=passed,
        command=["python", stage],
        return_code=0 if passed else 1,
        stdout="",
        stderr="syntax error" if not passed else "",
    )


class PipelineTests(unittest.TestCase):
    def test_target_miss_precedes_stability_failure(self) -> None:
        validation = CandidateValidation(
            syntax=check("syntax", True),
            import_check=check("import", True),
            runtime=check("runtime", True),
            stability=check("stability", False),
            target_hit="false",
        )

        self.assertEqual(validation.first_failure().stage, "target_hit")

    def test_failed_candidate_is_repaired_and_traced(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        spec = TargetSpec(
            id="sympy_expand_001",
            module="sympy",
            target="expand",
            qualified_name="sympy.expand",
            description="Expand a polynomial",
        )
        failed = CandidateValidation(
            syntax=check("syntax", False),
            import_check=None,
            runtime=None,
            stability=None,
            target_hit="false",
        )
        successful = CandidateValidation(
            syntax=check("syntax", True),
            import_check=check("import", True),
            runtime=check("runtime", True),
            stability=check("stability", True),
            target_hit="true",
        )

        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary) / "artifacts"
            config = PocConfig(
                max_retries=3,
                timeout_seconds=10,
                fast_mode=True,
                temperature=0,
                artifacts_root=artifacts,
            )
            generator = BenchmarkGenerator(
                client=FakeClient(),  # type: ignore[arg-type]
                generate_template=project_root / "prompts" / "generate_benchmark.txt",
                repair_template=project_root / "prompts" / "repair_benchmark.txt",
            )
            pipeline = PocPipeline(
                project_root=project_root,
                config=config,
                generator=generator,
                model_name="fake-model",
            )

            with patch(
                "src.pipeline.validate_candidate",
                side_effect=[failed, successful],
            ):
                run_dir = pipeline.run([spec])

            target_dir = run_dir / spec.id
            self.assertTrue((target_dir / "attempt_0" / "generation_response.txt").is_file())
            self.assertTrue((target_dir / "attempt_1" / "repair_response.txt").is_file())
            self.assertTrue((target_dir / "attempt_1" / "llm_metadata.json").is_file())
            final = (target_dir / "final.json").read_text(encoding="utf-8")
            self.assertIn('"status": "SUCCESS"', final)
            self.assertIn('"repair_attempts": 1', final)
            self.assertTrue((run_dir / "summary.csv").is_file())

    def test_stability_failure_is_recorded_without_repair(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        spec = TargetSpec(
            id="sympy_expand_001",
            module="sympy",
            target="expand",
            qualified_name="sympy.expand",
            description="Expand a polynomial",
        )
        unstable = CandidateValidation(
            syntax=check("syntax", True),
            import_check=check("import", True),
            runtime=check("runtime", True),
            stability=check("stability", False),
            target_hit="true",
        )

        with tempfile.TemporaryDirectory() as temporary:
            config = PocConfig(
                max_retries=3,
                timeout_seconds=10,
                fast_mode=True,
                temperature=0,
                artifacts_root=Path(temporary) / "artifacts",
            )
            generator = BenchmarkGenerator(
                client=FakeClient(),  # type: ignore[arg-type]
                generate_template=project_root / "prompts" / "generate_benchmark.txt",
                repair_template=project_root / "prompts" / "repair_benchmark.txt",
            )
            pipeline = PocPipeline(
                project_root=project_root,
                config=config,
                generator=generator,
                model_name="fake-model",
            )

            with patch(
                "src.pipeline.validate_candidate",
                return_value=unstable,
            ) as validator:
                run_dir = pipeline.run([spec])

            target_dir = run_dir / spec.id
            final = (target_dir / "final.json").read_text(encoding="utf-8")
            self.assertIn('"status": "EXECUTABLE_UNSTABLE"', final)
            self.assertIn('"repair_attempts": 0', final)
            self.assertFalse((target_dir / "attempt_1").exists())
            validator.assert_called_once()


if __name__ == "__main__":
    unittest.main()
