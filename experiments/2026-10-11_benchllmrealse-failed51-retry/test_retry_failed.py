import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

PHASE = Path(__file__).resolve().parents[1] / "2026-10-11_benchllmrealse-coverage-unpaid-isolated"
sys.path.insert(0, str(PHASE / "server-validation"))
sys.path.insert(0, str(PHASE / "diagnostics"))
import retry_failed as retry


def historical_rows():
    full = [dict(repository="netty", task=str(i), outcome="succeeded" if i < 9 else "infrastructure_failed") for i in range(64)]
    seven = [dict(repository="netty", task=str(i), outcome="succeeded" if i < 13 else "benchmark_failed") for i in range(9, 16)]
    prep = [dict(repository="netty", task=str(i), outcome="preparable" if i < 16 else "infrastructure_failed") for i in range(9, 64)]
    return full, prep, seven


class RetryTests(unittest.TestCase):
    def test_partition_excludes_successes_and_reuses_only_existing_failed_patches(self):
        finished, prep, replay = retry.select_retry_sets(*historical_rows())
        self.assertEqual([len(finished), len(prep), len(replay)], [13, 48, 3])
        self.assertFalse(finished & prep)
        self.assertFalse(finished & replay)

    def test_changed_historical_counts_fail_closed(self):
        full, prep, seven = historical_rows()
        seven[0]["outcome"] = "benchmark_failed"
        with self.assertRaises(ValueError):
            retry.select_retry_sets(full, prep, seven)

    def test_overlapping_historical_partition_rejected(self):
        full, prep, seven = historical_rows()
        prep[-1]["task"] = "0"
        with self.assertRaises(ValueError):
            retry.select_retry_sets(full, prep, seven)

    def test_paid_gate_requires_both_successful_references(self):
        good = {"outcome": "succeeded"}
        bad = {"outcome": "reference_evaluation_failed"}
        self.assertFalse(retry.references_ready({"original": good}))
        self.assertFalse(retry.references_ready({"original": good, "developer": bad}))
        self.assertTrue(retry.references_ready({"original": good, "developer": good}))

    def test_credentials_are_data_not_shell_instructions(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {}, clear=True):
            root = Path(tmp)
            (root / "codex-home").mkdir()
            (root / "codex-home/config.toml").write_text('env_key = "BENCHLLM_TEST_KEY"\n')
            (root / "secrets.env").write_text('export BENCHLLM_TEST_KEY="literal $(echo forbidden)"\n')
            retry.load_provider_environment(root)
            self.assertEqual(os.environ["BENCHLLM_TEST_KEY"], "literal $(echo forbidden)")

    def test_workspace_inspection_failure_does_not_abort_the_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / ".git").mkdir()
            record = {}
            full = mock.Mock()
            full.git.side_effect = RuntimeError("partial clone")
            retry.finalize_workspace(full, ws, record)
            self.assertEqual(record["workspace_inspection_error"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
