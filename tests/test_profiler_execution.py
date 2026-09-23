import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

from src.framework.config import FrameworkConfig, ProfilerCallbackConfig
from src.framework.evaluator import Evaluator
from src.framework.pipeline import OptimizationFramework


class ProfilerExecutionTests(unittest.TestCase):
    def test_reuses_tracemalloc_target_discovery_under_correct_name(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        config = FrameworkConfig.load(
            project_root / "config" / "framework_demo.yaml", project_root
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            framework = OptimizationFramework(
                project_root=project_root,
                config=config,
                agents=MagicMock(),
                evaluator=MagicMock(),
                model_name="test-model",
            )
            memory_report = {
                "profile_format": "tracemalloc_snapshot",
                "hotspots": [{"qualified_name": "target.allocate"}],
            }
            framework.hotspot_summary = memory_report
            evidence = framework._collect_profiler_evidence(
                root / "experiment",
                workspace,
                {
                    "task_type": "memory",
                    "selected_profilers": [{"name": "tracemalloc"}],
                },
                None,
                None,
            )
            self.assertIs(evidence["reports"]["tracemalloc"], memory_report)
            self.assertNotIn("cprofile", evidence["reports"])
            self.assertEqual(
                evidence["executed"],
                [{"name": "tracemalloc", "source": "target_discovery_reuse"}],
            )
            framework.evaluator.run.assert_not_called()

    def test_pipeline_executes_memory_callback_and_parses_hotspot(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        base = FrameworkConfig.load(
            project_root / "config" / "framework_demo.yaml", project_root
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "target.py").write_text(
                "def allocate():\n"
                "    return [bytearray(4096) for _ in range(64)]\n",
                encoding="utf-8",
            )
            callback = root / "callback.py"
            callback.write_text(
                "from target import allocate\n"
                "def prepare_workload(): return None\n"
                "def run_workload(_prepared): return allocate()\n"
                "def validate_workload(result):\n"
                "    assert len(result) == 64\n"
                "    return {'entries': len(result)}\n",
                encoding="utf-8",
            )
            config = replace(
                base,
                profiler_callback=ProfilerCallbackConfig(
                    module=callback,
                    limit=5,
                    frames=10,
                ),
            )
            framework = OptimizationFramework(
                project_root=project_root,
                config=config,
                agents=MagicMock(),
                evaluator=Evaluator(timeout_seconds=60),
                model_name="test-model",
            )
            evidence = framework._collect_profiler_evidence(
                root / "experiment",
                workspace,
                {
                    "task_type": "memory",
                    "selected_profilers": [{"name": "tracemalloc"}],
                },
                None,
                None,
            )

            self.assertEqual(evidence["status"], "COMPLETE")
            self.assertTrue(evidence["execution_applied"])
            report = evidence["reports"]["tracemalloc"]
            names = [item["qualified_name"] for item in report["hotspots"]]
            self.assertIn("target.allocate", names)
            self.assertIn("tracemalloc", evidence["model_context"]["reports"])
            callback = evidence["model_context"]["callback_measurement"]
            self.assertTrue(callback["passed"])
            self.assertGreater(callback["tracemalloc_peak_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
