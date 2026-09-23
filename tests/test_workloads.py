import tempfile
import unittest
from pathlib import Path

from src.framework.workloads import (
    WorkloadSpec,
    assess_workload_fidelity,
    discover_workload_candidates,
    extract_test_scenarios,
    workload_script_sha256,
)


class WorkloadDiscoveryTests(unittest.TestCase):
    def test_discovers_and_orders_repository_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            benchmark = repository / "benchmarks" / "bench_speed.py"
            benchmark.parent.mkdir()
            benchmark.write_text(
                "def main():\n    return 1\n\n"
                "if __name__ == '__main__':\n    main()\n",
                encoding="utf-8",
            )
            test = repository / "tests" / "test_feature.py"
            test.parent.mkdir()
            (test.parent / "__init__.py").write_text("", encoding="utf-8")
            test.write_text(
                "import unittest\n\n"
                "class TestFeature(unittest.TestCase):\n"
                "    def test_value(self):\n        self.assertEqual(1, 1)\n",
                encoding="utf-8",
            )
            example = repository / "examples" / "example_api.py"
            example.parent.mkdir()
            example.write_text(
                "if __name__ == '__main__':\n    print('example')\n",
                encoding="utf-8",
            )

            report = discover_workload_candidates(repository)
            self.assertEqual(report["candidate_count"], 3)
            candidates = report["candidates"]
            self.assertEqual(
                [item["source"] for item in candidates],
                ["existing_benchmark", "existing_test", "example"],
            )
            self.assertTrue(candidates[0]["directly_runnable"])
            self.assertFalse(candidates[0]["requires_adaptation"])
            self.assertTrue(candidates[1]["requires_adaptation"])
            self.assertEqual(
                candidates[1]["command"],
                ["{python}", "-m", "unittest", "tests.test_feature"],
            )

    def test_ignores_ordinary_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            (repository / "module.py").write_text("value = 1\n", encoding="utf-8")
            report = discover_workload_candidates(repository)
            self.assertEqual(report["candidate_count"], 0)

    def test_extracts_only_test_scenario_that_calls_query(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            tests = repository / "tests" / "test_recipes.py"
            tests.parent.mkdir()
            tests.write_text(
                "import unittest\nimport package as api\n\n"
                "class TriplewiseTests(unittest.TestCase):\n"
                "    def test_basic(self):\n"
                "        actual = list(api.triplewise([1, 2, 3]))\n"
                "        self.assertEqual(actual, [(1, 2, 3)])\n\n"
                "class OtherTests(unittest.TestCase):\n"
                "    def test_other(self):\n"
                "        self.assertEqual(api.other(), 1)\n",
                encoding="utf-8",
            )

            scenarios = extract_test_scenarios(
                repository,
                Path("tests/test_recipes.py"),
                "package.triplewise",
            )
            self.assertEqual(len(scenarios), 1)
            self.assertEqual(scenarios[0].source_symbol, "TriplewiseTests")
            self.assertEqual(scenarios[0].called_names, ("api.triplewise", "list", "self.assertEqual"))
            self.assertEqual(scenarios[0].assertion_count, 1)
            self.assertIn("[(1, 2, 3)]", scenarios[0].source_code)
            self.assertIn("api.triplewise", scenarios[0].referenced_names)

    def test_workload_spec_serializes_command_and_hashes_script(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / "workload.py"
            script.write_text("print('workload')\n", encoding="utf-8")
            digest = workload_script_sha256(script)
            spec = WorkloadSpec(
                workload_id="test-derived-1",
                source="existing_test+llm_adapted",
                source_path="tests/test_recipes.py",
                source_symbol="TriplewiseTests",
                script_path="generated_workload.py",
                command=("python", "generated_workload.py"),
                target_symbol="package.triplewise",
                input_description="Scaled deterministic input",
                expected_behavior="Returns the expected checksum",
                confidence="medium",
                adaptation_type="scale_only",
                fidelity_status="PASS",
                llm_adapted=True,
                automatic_validation_passed=True,
                human_confirmed=False,
                experiment_locked=True,
                frozen=False,
                script_sha256=digest,
            )
            payload = spec.to_dict()
            self.assertEqual(payload["command"], ["python", "generated_workload.py"])
            self.assertEqual(payload["script_sha256"], digest)
            self.assertTrue(payload["experiment_locked"])
            self.assertFalse(payload["frozen"])

    def test_fidelity_requires_review_when_constructor_is_replaced(self) -> None:
        result = assess_workload_fidelity(
            "def test():\n    value = AtomicFields()\n    attrs.asdict(value)\n",
            "def workload():\n    value = Bundle()\n    return asdict(value)\n",
        )
        self.assertEqual(result.adaptation_type, "structure_changed")
        self.assertEqual(result.fidelity_status, "REVIEW_REQUIRED")
        self.assertEqual(result.missing_in_generated, ("AtomicFields",))

    def test_fidelity_passes_scale_only_adaptation(self) -> None:
        result = assess_workload_fidelity(
            "def test():\n    value = AtomicFields()\n    attrs.asdict(value)\n",
            "def workload():\n    value = AtomicFields()\n    return asdict(value)\n",
        )
        self.assertEqual(result.adaptation_type, "scale_only")
        self.assertEqual(result.fidelity_status, "PASS")

    def test_selects_one_existing_benchmark_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            benchmark = repository / "bench" / "test_benchmarks.py"
            benchmark.parent.mkdir()
            benchmark.write_text(
                "import api\n\n"
                "def test_asdict_simple():\n    api.asdict(object())\n\n"
                "def test_asdict_atomic():\n"
                "    operation = api.asdict\n"
                "    operation(object())\n",
                encoding="utf-8",
            )
            scenarios = extract_test_scenarios(
                repository,
                Path("bench/test_benchmarks.py"),
                "asdict",
                source_kind="existing_benchmark",
                scenario_symbol="test_asdict_atomic",
            )
            self.assertEqual(len(scenarios), 1)
            self.assertEqual(scenarios[0].source, "existing_benchmark")
            self.assertEqual(scenarios[0].source_symbol, "test_asdict_atomic")
            self.assertIn("api.asdict", scenarios[0].referenced_names)


if __name__ == "__main__":
    unittest.main()
