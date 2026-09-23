import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.framework.memory_hotspots import parse_tracemalloc_snapshot


class ProfileCallbackTests(unittest.TestCase):
    def test_snapshot_is_captured_while_result_is_alive(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        runner = project_root / "scripts" / "run_profile_callback.py"
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            target = workspace / "target.py"
            target.write_text(
                "def allocate():\n"
                "    return [bytearray(4096) for _ in range(64)]\n",
                encoding="utf-8",
            )
            helper = workspace / "callback_helper.py"
            helper.write_text("from target import allocate\n", encoding="utf-8")
            callback = workspace / "callback.py"
            callback.write_text(
                "from callback_helper import allocate\n"
                "def prepare_workload(): return None\n"
                "def run_workload(_prepared): return allocate()\n"
                "def validate_workload(result):\n"
                "    assert len(result) == 64\n"
                "    return {'entries': len(result)}\n",
                encoding="utf-8",
            )
            snapshot = workspace / "memory.snapshot"
            metadata = workspace / "metadata.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(runner),
                    "--module",
                    str(callback),
                    "--tracemalloc-output",
                    str(snapshot),
                    "--metadata-output",
                    str(metadata),
                ],
                cwd=workspace,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(metadata.read_text())
            self.assertTrue(payload["passed"])
            self.assertEqual(payload["validation"]["entries"], 64)

            report = parse_tracemalloc_snapshot(snapshot, workspace, limit=5)
            names = [item["qualified_name"] for item in report["hotspots"]]
            self.assertIn("target.allocate", names)


if __name__ == "__main__":
    unittest.main()
