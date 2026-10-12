"""Reference failures must be explicit, not converted into passing scores."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "roaring_batch", Path(__file__).resolve().parents[1] / "scripts/run_roaringbitmap_batch.py")
batch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(batch)


class ReferenceEvaluationTests(unittest.TestCase):
    def evaluate(self, effects):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            with patch.object(batch, "run", side_effect=effects) as run:
                record = batch.evaluate_reference(Path("support"), Path("workspace"), output, "developer")
            self.assertEqual(record, json.loads((output / "result.json").read_text()))
            return record, run.call_count

    def test_success_records_both_stages(self):
        record, calls = self.evaluate([None, None])
        self.assertEqual("succeeded", record["outcome"])
        self.assertEqual(2, calls)

    def test_benchmark_failure_remains_failure(self):
        record, calls = self.evaluate([None, subprocess.CalledProcessError(1, ["java"])])
        self.assertEqual("reference_evaluation_failed", record["outcome"])
        self.assertEqual("benchmark", record["failed_stage"])
        self.assertEqual(2, calls)

    def test_verification_failure_does_not_run_benchmark(self):
        record, calls = self.evaluate([subprocess.CalledProcessError(1, ["javac"])])
        self.assertEqual("verification", record["failed_stage"])
        self.assertEqual(1, calls)

    def test_timeout_is_not_success(self):
        record, _ = self.evaluate([None, subprocess.TimeoutExpired(["java"], 900)])
        self.assertEqual("reference_evaluation_failed", record["outcome"])
        self.assertEqual("TimeoutExpired", record["error_type"])


if __name__ == "__main__":
    unittest.main()
