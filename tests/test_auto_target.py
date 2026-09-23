import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.framework.config import FrameworkConfig
from src.framework.pipeline import OptimizationFramework
from src.framework.sandbox import SandboxResult


class AutoTargetTests(unittest.TestCase):
    def test_cpython_auto_target_config_has_no_target_hint(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        config = FrameworkConfig.load(
            project_root / "config" / "cpython_urllib_auto_target.yaml",
            project_root,
        )
        self.assertEqual(config.target_mode, "auto")
        self.assertIsNone(config.target_file)
        self.assertIsNone(config.target_symbol)
        self.assertEqual(config.editable_files, ())
        self.assertIsNotNone(config.hotspot_discovery)

    def test_discovery_injects_target_and_profiler_context(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        config = FrameworkConfig.load(
            project_root / "config" / "more_itertools_triplewise_auto_e2e.yaml",
            project_root,
        )
        framework = OptimizationFramework(
            project_root=project_root,
            config=config,
            agents=MagicMock(),
            evaluator=MagicMock(),
            model_name="test-model",
        )

        def checkout(destination: Path, _ref: str | None) -> str:
            source = destination / "more_itertools" / "recipes.py"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(
                "def triplewise(iterable):\n    return iterable\n", encoding="utf-8"
            )
            return "baseline-sha"

        framework.repositories.checkout = MagicMock(side_effect=checkout)

        def sandbox_run(**kwargs: object) -> SandboxResult:
            output = Path(str(kwargs["output"]))
            output.mkdir(parents=True, exist_ok=True)
            (output / "profile.prof").write_bytes(b"profile-placeholder")
            return SandboxResult(
                command=("docker", "run"),
                return_code=0,
                stdout="",
                stderr="",
                timed_out=False,
                output_truncated=False,
            )

        report = {
            "profile_format": "cProfile",
            "ranking_metric": "self_time_seconds",
            "total_profiled_self_time_seconds": 1.0,
            "hotspots": [
                {
                    "rank": 1,
                    "file": "more_itertools/recipes.py",
                    "qualified_name": "more_itertools.recipes.triplewise",
                    "self_time_seconds": 0.8,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temporary:
            experiment = Path(temporary)
            with (
                patch("src.framework.pipeline.run_in_docker", side_effect=sandbox_run),
                patch("src.framework.pipeline.parse_cprofile", return_value=report),
            ):
                framework._discover_target(experiment)

            self.assertEqual(
                framework.config.target_file, Path("more_itertools/recipes.py")
            )
            self.assertEqual(
                framework.config.target_symbol,
                "more_itertools.recipes.triplewise",
            )
            self.assertEqual(
                framework.config.editable_files,
                (Path("more_itertools/recipes.py"),),
            )
            self.assertTrue((experiment / "target_discovery" / "hotspots.json").is_file())
            self.assertFalse((experiment / "target_discovery" / "workspace").exists())

            context_workspace = experiment / "context"
            source = context_workspace / "more_itertools" / "recipes.py"
            source.parent.mkdir(parents=True)
            source.write_text(
                "def triplewise(iterable):\n    return iterable\n", encoding="utf-8"
            )
            tests = context_workspace / "tests" / "test_recipes.py"
            tests.parent.mkdir(parents=True)
            tests.write_text(
                "def test_triplewise():\n    pass\n", encoding="utf-8"
            )
            routed = framework._collect_profiler_evidence(
                experiment,
                context_workspace,
                {
                    "task_type": "cpu_bound",
                    "selected_profilers": [{"name": "cprofile"}],
                },
                None,
                None,
            )
            self.assertEqual(routed["status"], "COMPLETE")
            self.assertTrue(routed["execution_applied"])
            self.assertEqual(routed["executed"][0]["source"], "target_discovery_reuse")
            _source_context, tests_context = framework._contexts(context_workspace)
            self.assertIn("Profiler evidence", tests_context)
            self.assertIn("Routed profiler evidence", tests_context)
            self.assertIn("self_time_seconds", tests_context)
            self.assertNotIn("validation_expected_symbol", tests_context)


if __name__ == "__main__":
    unittest.main()
