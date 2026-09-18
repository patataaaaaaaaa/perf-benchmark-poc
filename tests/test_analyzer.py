import unittest

from src.benchmark.analyzer import summarize


class SummaryTests(unittest.TestCase):
    def test_summary_counts_repair_success(self) -> None:
        results = [
            {
                "generated": True,
                "status": "SUCCESS",
                "initial_syntax_pass": True,
                "initial_import_pass": False,
                "initial_runtime_pass": False,
                "final_runtime_pass": True,
                "final_stability_pass": True,
                "repair_attempts": 1,
                "target_hit": "true",
            },
            {
                "generated": False,
                "status": "SKIPPED",
                "initial_syntax_pass": False,
                "initial_import_pass": False,
                "initial_runtime_pass": False,
                "final_runtime_pass": False,
                "final_stability_pass": False,
                "repair_attempts": 0,
                "target_hit": "unknown",
            },
            {
                "generated": True,
                "status": "EXECUTABLE_UNSTABLE",
                "initial_syntax_pass": True,
                "initial_import_pass": True,
                "initial_runtime_pass": False,
                "final_runtime_pass": True,
                "final_stability_pass": False,
                "repair_attempts": 2,
                "target_hit": "true",
            },
        ]
        summary = summarize(results)
        self.assertEqual(summary["total_targets"], 3)
        self.assertEqual(summary["repair_success_count"], 2)
        self.assertEqual(summary["repair_success_rate"], 1.0)
        self.assertEqual(summary["target_hit_true_count"], 2)


if __name__ == "__main__":
    unittest.main()
