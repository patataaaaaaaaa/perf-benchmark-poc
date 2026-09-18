import subprocess
import tempfile
import unittest
from pathlib import Path

from src.framework.agents import extract_python_code
from src.framework.config import FrameworkConfig
from src.framework.evaluator import _robust_rsd_percent
from src.framework.generated_benchmark import (
    sha256_file,
    validate_generated_benchmark,
)
from src.framework.patching import (
    apply_safe_patch,
    canonicalize_hunk_locations,
    extract_symbol_context,
    extract_unified_diff,
    patch_paths,
)
from src.framework.pipeline import decide_candidate


class FrameworkTests(unittest.TestCase):
    def test_extract_python_code_from_fence(self) -> None:
        response = "```python\nvalue = 1\n```"
        self.assertEqual(extract_python_code(response), "value = 1\n")

    def test_accept_requires_functional_and_performance_improvement(self) -> None:
        self.assertEqual(decide_candidate(True, True, 8.0, 3.0), "ACCEPT")
        self.assertEqual(
            decide_candidate(False, True, 8.0, 3.0), "REJECT_FUNCTIONAL"
        )
        self.assertEqual(
            decide_candidate(True, True, 1.0, 3.0), "REJECT_PERFORMANCE"
        )
        self.assertEqual(
            decide_candidate(
                True,
                True,
                8.0,
                3.0,
                significant=False,
                require_significance=True,
            ),
            "REJECT_NOT_SIGNIFICANT",
        )

    def test_robust_rsd_resists_one_outlier(self) -> None:
        value = _robust_rsd_percent([0.099, 0.100, 0.100, 0.101, 0.140])
        self.assertIsNotNone(value)
        self.assertLess(value or 100.0, 2.0)

    def test_demo_config_loads(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        config = FrameworkConfig.load(
            project_root / "config" / "framework_demo.yaml", project_root
        )
        self.assertEqual(config.target_symbol, "center_values")
        self.assertTrue(config.source_path.is_file())

    def test_more_itertools_config_pins_historical_commits(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        config = FrameworkConfig.load(
            project_root / "config" / "more_itertools_triplewise.yaml",
            project_root,
        )
        self.assertEqual(config.experiment_runs, 3)
        self.assertEqual(config.max_iterations, 3)
        self.assertEqual(config.primary_benchmark, "triplewise_large")
        self.assertEqual(
            config.baseline_commit,
            "b87f67bbbfa488cf56bd86e7b64eb3e8118c34bc",
        )

    def test_generated_benchmark_config_does_not_require_fixed_command(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        config = FrameworkConfig.load(
            project_root / "config" / "more_itertools_triplewise_e2e.yaml",
            project_root,
        )
        self.assertEqual(config.benchmark_mode, "generated")
        self.assertEqual(config.benchmark_command, ())
        self.assertTrue(config.benchmark_fast_mode)

    def test_sha256_file_changes_with_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "benchmark.py"
            path.write_text("value = 1\n", encoding="utf-8")
            first = sha256_file(path)
            path.write_text("value = 2\n", encoding="utf-8")
            self.assertNotEqual(first, sha256_file(path))

    def test_generated_benchmark_executes_target_and_repeats_workload(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            (repository / "targetmod.py").write_text(
                "def target(values):\n    return [value * 2 for value in values]\n",
                encoding="utf-8",
            )
            benchmark = repository / "benchmark.py"
            benchmark.write_text(
                """from pathlib import Path
import sys
import pyperf
sys.path.insert(0, str(Path.cwd()))
from targetmod import target
TARGET_SYMBOL = "targetmod.target"
WORKLOAD_DESCRIPTION = "double and sum 1000 integers"
PRIMARY_BENCHMARK = "target_large"
def workload():
    return sum(target(range(1000)))
def get_cases():
    return {"target_large": (workload, 999000)}
def main():
    runner = pyperf.Runner()
    for name, (callback, _) in get_cases().items():
        runner.bench_func(name, callback)
if __name__ == "__main__":
    main()
""",
                encoding="utf-8",
            )
            validation = validate_generated_benchmark(
                benchmark_path=benchmark,
                result_path=repository / "result.json",
                workspace=repository,
                python=str(project_root / ".venv" / "bin" / "python"),
                target_symbol="targetmod.target",
                project_root=project_root,
                timeout_seconds=30,
                fast_mode=True,
            )
            self.assertTrue(validation.passed, validation.to_dict())
            self.assertEqual(validation.primary_benchmark, "target_large")

    def test_unified_diff_is_limited_to_allowlist(self) -> None:
        response = """```diff
diff --git a/allowed.py b/allowed.py
--- a/allowed.py
+++ b/allowed.py
@@ -1 +1 @@
-value = 1
+value = 2
```"""
        patch_text = extract_unified_diff(response)
        self.assertEqual(patch_paths(patch_text), {Path("allowed.py")})
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            subprocess.run(["git", "init"], cwd=repository, check=True, capture_output=True)
            (repository / "allowed.py").write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "allowed.py"], cwd=repository, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@localhost",
                    "commit",
                    "-m",
                    "initial",
                ],
                cwd=repository,
                check=True,
                capture_output=True,
            )
            apply_safe_patch(repository, patch_text, (Path("allowed.py"),))
            self.assertEqual(
                (repository / "allowed.py").read_text(encoding="utf-8"),
                "value = 2\n",
            )

    def test_wrong_model_hunk_line_is_recomputed_from_context(self) -> None:
        patch_text = """--- a/allowed.py
+++ b/allowed.py
@@ -200,1 +200,1 @@
-value = 1
+value = 2
"""
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            (repository / "allowed.py").write_text(
                "heading = 0\nvalue = 1\n", encoding="utf-8"
            )
            canonical = canonicalize_hunk_locations(repository, patch_text)
            self.assertIn("@@ -2,1 +2,1 @@", canonical)

    def test_patch_cannot_read_or_modify_parent_path(self) -> None:
        patch_text = """--- a/../secret.py
+++ b/../secret.py
@@ -1,1 +1,1 @@
-secret = 1
+secret = 2
"""
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "Unsafe patch path"):
                canonicalize_hunk_locations(Path(temporary), patch_text)

    def test_symbol_context_does_not_include_unrelated_functions(self) -> None:
        source = "import math\n\ndef target(x):\n    return math.sqrt(x)\n\ndef other():\n    return 1\n"
        context = extract_symbol_context(source, "module.target")
        self.assertIn("def target", context)
        self.assertNotIn("def other", context)


if __name__ == "__main__":
    unittest.main()
