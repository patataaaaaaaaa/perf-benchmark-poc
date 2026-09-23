import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.framework.agents import extract_python_code
from src.framework.config import FrameworkConfig
from src.framework.evaluator import _robust_rsd_percent, compare_memory
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
    repository_diff,
    restore_patch,
)
from src.framework.pipeline import (
    OptimizationFramework,
    classify_baseline_evidence,
    decide_candidate,
)
from src.framework.repository import RepositoryManager
from src.framework.replay import reconstruct_frozen_workspaces


class FrameworkTests(unittest.TestCase):
    def test_extract_python_code_from_fence(self) -> None:
        response = "```python\nvalue = 1\n```"
        self.assertEqual(extract_python_code(response), "value = 1\n")

    def test_accept_requires_functional_and_performance_improvement(self) -> None:
        self.assertEqual(decide_candidate(True, True, 8.0, 3.0), "ACCEPT")
        self.assertEqual(
            decide_candidate(False, True, 8.0, 3.0), "REJECT_FUNCTIONAL"
        )

    def test_baseline_classification_prefers_original_workload_and_is_observe_only(
        self,
    ) -> None:
        workload = SimpleNamespace(
            passed=True,
            to_dict=lambda: {
                "command": {
                    "metrics": {
                        "wall_seconds": 1.0,
                        "user_cpu_seconds": 0.91,
                        "system_cpu_seconds": 0.04,
                        "cpu_to_wall_ratio": 0.95,
                        "peak_rss_bytes": 10_000_000,
                        "read_bytes": 0,
                        "write_bytes": 0,
                        "read_count": 10,
                        "write_count": 0,
                    }
                }
            },
        )
        resources = SimpleNamespace(
            passed=True,
            to_dict=lambda: {
                "command": {
                    "metrics": {
                        "wall_seconds": 1.0,
                        "user_cpu_seconds": 0.1,
                        "system_cpu_seconds": 0.0,
                        "cpu_to_wall_ratio": 0.1,
                    }
                }
            },
        )

        result = classify_baseline_evidence(resources, workload)

        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["mode"], "observe_only")
        self.assertFalse(result["routing_applied"])
        self.assertEqual(result["sample_source"], "original_workload")
        self.assertEqual(result["classification"]["task_type"], "cpu_bound")
        self.assertIn("observation-only profiler plan", result["limitations"][1])

    def test_baseline_classification_handles_missing_evidence(self) -> None:
        result = classify_baseline_evidence(None, None)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertFalse(result["routing_applied"])
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

    def test_accept_requires_original_workload_improvement_when_configured(self) -> None:
        self.assertEqual(
            decide_candidate(
                True,
                True,
                8.0,
                3.0,
                workload_passed=True,
                workload_improvement_percent=5.0,
                minimum_workload_percent=3.0,
            ),
            "ACCEPT",
        )
        self.assertEqual(
            decide_candidate(
                True,
                True,
                8.0,
                3.0,
                workload_passed=True,
                workload_improvement_percent=1.0,
                minimum_workload_percent=3.0,
            ),
            "REJECT_WORKLOAD",
        )

    def test_memory_objective_accepts_reduction_with_small_runtime_regression(self) -> None:
        self.assertEqual(
            decide_candidate(
                True,
                True,
                -5.0,
                3.0,
                workload_passed=True,
                workload_improvement_percent=-8.0,
                optimization_objective="memory",
                memory_passed=True,
                memory_reduction_percent=60.0,
                minimum_memory_reduction_percent=10.0,
                max_runtime_regression_percent=10.0,
            ),
            "ACCEPT",
        )

    def test_memory_objective_rejects_insufficient_reduction(self) -> None:
        self.assertEqual(
            decide_candidate(
                True,
                True,
                2.0,
                3.0,
                optimization_objective="memory",
                memory_passed=True,
                memory_reduction_percent=5.0,
                minimum_memory_reduction_percent=10.0,
                max_runtime_regression_percent=10.0,
            ),
            "REJECT_MEMORY",
        )

    def test_memory_objective_rejects_runtime_regression(self) -> None:
        self.assertEqual(
            decide_candidate(
                True,
                True,
                -12.0,
                3.0,
                optimization_objective="memory",
                memory_passed=True,
                memory_reduction_percent=60.0,
                minimum_memory_reduction_percent=10.0,
                max_runtime_regression_percent=10.0,
            ),
            "REJECT_RUNTIME_REGRESSION",
        )

    def test_compare_memory_uses_peak_reduction(self) -> None:
        baseline = SimpleNamespace(tracemalloc_peak_bytes=10_000_000)
        candidate = SimpleNamespace(tracemalloc_peak_bytes=2_500_000)
        comparison = compare_memory(baseline, candidate)
        self.assertEqual(comparison.metric, "tracemalloc_peak_bytes")
        self.assertEqual(comparison.reduction_percent, 75.0)
        self.assertEqual(
            decide_candidate(
                True,
                True,
                8.0,
                3.0,
                workload_passed=False,
                workload_improvement_percent=None,
            ),
            "REJECT_WORKLOAD",
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
        self.assertEqual(config.optimization_objective, "runtime")

    def test_auto_target_config_omits_manual_target(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        config = FrameworkConfig.load(
            project_root / "config" / "more_itertools_triplewise_auto_e2e.yaml",
            project_root,
        )
        self.assertEqual(config.target_mode, "auto")
        self.assertIsNone(config.target_file)
        self.assertIsNone(config.target_symbol)
        self.assertEqual(config.editable_files, ())
        self.assertIsNotNone(config.hotspot_discovery)
        self.assertIsNotNone(config.execution_sandbox)
        self.assertIsNotNone(config.original_workload_command)
        self.assertEqual(config.min_workload_speedup_percent, 3.0)
        assert config.hotspot_discovery is not None
        self.assertEqual(config.hotspot_discovery.limit, 5)
        assert config.execution_sandbox is not None
        self.assertEqual(
            config.execution_sandbox.image,
            "perf-benchmark-sandbox:py311-v1",
        )
        self.assertEqual(
            config.hotspot_discovery.validation_expected_symbol,
            "more_itertools.recipes.triplewise",
        )

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

    def test_accept_reject_accept_restores_previous_best_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            subprocess.run(["git", "init"], cwd=repository, check=True, capture_output=True)
            target = repository / "allowed.py"
            target.write_text("value = 1\n", encoding="utf-8")
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
                    "baseline",
                ],
                cwd=repository,
                check=True,
                capture_output=True,
            )
            first = """--- a/allowed.py
+++ b/allowed.py
@@ -1 +1 @@
-value = 1
+value = 2
"""
            rejected = """--- a/allowed.py
+++ b/allowed.py
@@ -1 +1 @@
-value = 2
+value = 999
"""
            third = """--- a/allowed.py
+++ b/allowed.py
@@ -1 +1 @@
-value = 2
+value = 3
"""
            apply_safe_patch(repository, first, (Path("allowed.py"),))
            best_after_first = repository_diff(repository)

            apply_safe_patch(repository, rejected, (Path("allowed.py"),))
            restore_patch(repository, best_after_first)
            self.assertEqual(target.read_text(encoding="utf-8"), "value = 2\n")
            self.assertEqual(repository_diff(repository), best_after_first)

            apply_safe_patch(repository, third, (Path("allowed.py"),))
            best_after_third = repository_diff(repository)
            restore_patch(repository, best_after_third)
            self.assertEqual(target.read_text(encoding="utf-8"), "value = 3\n")
            self.assertEqual(repository_diff(repository), best_after_third)

    def test_repository_checkout_is_independent_from_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True)
            (source / "value.py").write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "value.py"], cwd=source, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@localhost",
                    "commit",
                    "-m",
                    "baseline",
                ],
                cwd=source,
                check=True,
                capture_output=True,
            )
            manager = RepositoryManager(SimpleNamespace(repository=source))
            destination = root / "workspace"
            manager.checkout(destination, "HEAD")
            self.assertFalse((destination / ".git/objects/info/alternates").exists())
            self.assertEqual(
                subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=destination,
                    text=True,
                    capture_output=True,
                    check=True,
                ).stdout,
                "",
            )

    def test_workspace_cleanup_preserves_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            experiment = Path(temporary)
            workspace = experiment / "run_01" / "workspace"
            evidence = experiment / "run_01" / "final" / "best.patch"
            workspace.mkdir(parents=True)
            evidence.parent.mkdir(parents=True)
            (workspace / "source.py").write_text("value = 1\n", encoding="utf-8")
            evidence.write_text("patch evidence\n", encoding="utf-8")
            result = OptimizationFramework._remove_experiment_workspaces(experiment)
            self.assertFalse(workspace.exists())
            self.assertTrue(evidence.is_file())
            self.assertEqual(result["removed"], ["run_01/workspace"])

    def test_release_candidate_records_patch_hash_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            experiment = Path(temporary)
            patch_path = experiment / "run_01" / "final" / "best.patch"
            patch_path.parent.mkdir(parents=True)
            patch_path.write_text("--- a/value.py\n+++ b/value.py\n", encoding="utf-8")
            framework = object.__new__(OptimizationFramework)
            framework.config = SimpleNamespace(
                target_file=Path("value.py"), target_symbol="module.value"
            )
            best_run = {
                "run": 1,
                "accepted_iterations": [1],
                "overall_comparison": {"speedup_percent": 10.0},
                "overall_original_workload_comparison": {"speedup_percent": 8.0},
            }
            manifest = framework._write_release_candidate(
                experiment, best_run, "baseline-sha"
            )
            self.assertEqual(manifest["status"], "READY_FOR_REVIEW")
            self.assertTrue((experiment / "release_candidate/best.patch").is_file())
            self.assertTrue(manifest["patch_sha256"])

    def test_cleaned_workspaces_can_be_reconstructed_from_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True)
            target = source / "value.py"
            target.write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "value.py"], cwd=source, check=True)
            commit_args = [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@localhost",
                "commit",
            ]
            subprocess.run(
                [*commit_args, "-m", "baseline"],
                cwd=source,
                check=True,
                capture_output=True,
            )
            baseline = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=source,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
            target.write_text("value = 2\n", encoding="utf-8")
            subprocess.run(["git", "add", "value.py"], cwd=source, check=True)
            subprocess.run(
                [*commit_args, "-m", "human"],
                cwd=source,
                check=True,
                capture_output=True,
            )
            human = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=source,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()

            artifact = root / "artifact"
            release = artifact / "release_candidate"
            release.mkdir(parents=True)
            patch_path = release / "best.patch"
            patch_path.write_text(
                """--- a/value.py
+++ b/value.py
@@ -1 +1 @@
-value = 1
+value = 3
""",
                encoding="utf-8",
            )
            (artifact / "manifest.json").write_text(
                '{"target_discovery": null, "config": {"target_file": "value.py"}}',
                encoding="utf-8",
            )
            (release / "manifest.json").write_text(
                '{"patch_sha256": "' + sha256_file(patch_path) + '"}',
                encoding="utf-8",
            )
            config = SimpleNamespace(
                repository=source,
                baseline_commit=baseline,
                human_fix_commit=human,
            )
            workspaces = reconstruct_frozen_workspaces(
                artifact_dir=artifact,
                config=config,
                destination=root / "reconstructed",
                run_number=1,
            )
            self.assertEqual(
                (workspaces["baseline"] / "value.py").read_text(encoding="utf-8"),
                "value = 1\n",
            )
            self.assertEqual(
                (workspaces["human_fix"] / "value.py").read_text(encoding="utf-8"),
                "value = 2\n",
            )
            self.assertEqual(
                (workspaces["deepseek_fix"] / "value.py").read_text(encoding="utf-8"),
                "value = 3\n",
            )

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

    def test_symbol_context_selects_qualified_class_method(self) -> None:
        source = (
            "class First:\n"
            "    def __next__(self):\n"
            "        return 1\n\n"
            "class Cursor:\n"
            "    def __next__(self):\n"
            "        return 2\n"
        )
        context = extract_symbol_context(source, "pkg.module.Cursor.__next__")
        self.assertIn("# Enclosing symbol: Cursor.__next__", context)
        self.assertIn("return 2", context)
        self.assertNotIn("return 1", context)


if __name__ == "__main__":
    unittest.main()
