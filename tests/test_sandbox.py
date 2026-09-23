import unittest
from pathlib import Path

from src.framework.sandbox import SandboxLimits, build_docker_command


class SandboxTests(unittest.TestCase):
    def test_docker_command_enforces_minimum_isolation(self) -> None:
        command = build_docker_command(
            container_name="test-sandbox",
            image="python:3.11-slim",
            workspace=Path("/tmp/workspace"),
            harness=Path("/tmp/harness"),
            output=Path("/tmp/output"),
            inner_command=["python", "workload.py"],
            limits=SandboxLimits(cpus=1.0, memory="256m", pids=32),
        )
        rendered = " ".join(command)
        self.assertIn("--network none", rendered)
        self.assertIn("--user 65534:65534", rendered)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop ALL", rendered)
        self.assertIn("no-new-privileges", rendered)
        self.assertIn("--cpus 1.0", rendered)
        self.assertIn("--memory 256m", rendered)
        self.assertIn("--pids-limit 32", rendered)
        self.assertIn("dst=/workspace,readonly", rendered)
        self.assertIn("dst=/harness,readonly", rendered)
        self.assertIn("PYTHONPATH=/workspace/src:/workspace", rendered)
        self.assertIn("OPENBLAS_NUM_THREADS=1", rendered)
        self.assertIn("OMP_NUM_THREADS=1", rendered)
        self.assertIn("MKL_NUM_THREADS=1", rendered)
        self.assertNotIn("DEEPSEEK", rendered)


if __name__ == "__main__":
    unittest.main()
