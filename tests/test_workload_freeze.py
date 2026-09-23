import json
import tempfile
import unittest
from pathlib import Path

from src.framework.generated_benchmark import sha256_file
from src.framework.workload_freeze import freeze_workload_candidate


class WorkloadFreezeTests(unittest.TestCase):
    def _candidate(self, root: Path) -> tuple[Path, str]:
        candidate = root / "testcase_derived"
        candidate.mkdir()
        script = candidate / "generated_workload.py"
        script.write_text("print('workload')\n", encoding="utf-8")
        digest = sha256_file(script)
        spec = candidate / "workload_spec.json"
        spec.write_text(
            json.dumps(
                {
                    "workload_id": "candidate-1",
                    "script_path": "testcase_derived/generated_workload.py",
                    "automatic_validation_passed": True,
                    "adaptation_type": "scale_only",
                    "fidelity_status": "PASS",
                    "human_confirmed": False,
                    "experiment_locked": True,
                    "frozen": False,
                    "script_sha256": digest,
                }
            ),
            encoding="utf-8",
        )
        return spec, digest

    def test_freezes_exact_reviewed_script_without_mutating_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec, digest = self._candidate(root)
            frozen = freeze_workload_candidate(
                artifact_dir=root,
                spec_path=spec,
                confirmed_sha256=digest,
                reviewer="reviewer@example.com",
                rationale="Matches the reported triplewise scenario.",
            )
            frozen_spec = json.loads(
                (frozen / "workload_spec.json").read_text(encoding="utf-8")
            )
            candidate_spec = json.loads(spec.read_text(encoding="utf-8"))
            self.assertTrue(frozen_spec["human_confirmed"])
            self.assertTrue(frozen_spec["frozen"])
            self.assertFalse(candidate_spec["human_confirmed"])
            self.assertEqual(sha256_file(frozen / "workload.py"), digest)

    def test_rejects_wrong_explicit_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec, _digest = self._candidate(root)
            with self.assertRaisesRegex(RuntimeError, "Explicitly confirmed"):
                freeze_workload_candidate(
                    artifact_dir=root,
                    spec_path=spec,
                    confirmed_sha256="0" * 64,
                    reviewer="reviewer",
                    rationale="Reviewed.",
                )

    def test_rejects_unvalidated_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec, digest = self._candidate(root)
            payload = json.loads(spec.read_text(encoding="utf-8"))
            payload["automatic_validation_passed"] = False
            spec.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "automatic validation"):
                freeze_workload_candidate(
                    artifact_dir=root,
                    spec_path=spec,
                    confirmed_sha256=digest,
                    reviewer="reviewer",
                    rationale="Reviewed.",
                )

    def test_rejects_candidate_requiring_fidelity_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec, digest = self._candidate(root)
            payload = json.loads(spec.read_text(encoding="utf-8"))
            payload["adaptation_type"] = "structure_changed"
            payload["fidelity_status"] = "REVIEW_REQUIRED"
            spec.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "fidelity"):
                freeze_workload_candidate(
                    artifact_dir=root,
                    spec_path=spec,
                    confirmed_sha256=digest,
                    reviewer="reviewer",
                    rationale="Reviewed.",
                )


if __name__ == "__main__":
    unittest.main()
