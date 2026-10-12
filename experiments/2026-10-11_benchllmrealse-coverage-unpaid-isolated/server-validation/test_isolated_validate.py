import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import isolated_validate as driver


class SnapshotTests(unittest.TestCase):
    def test_snapshot_copies_only_code_not_credentials_or_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared = root / "shared"
            project = shared / "perf-benchmark-poc"
            run = root / "run"
            run.mkdir()
            for name in ("scripts", "src", "artifacts", "__pycache__"):
                (project / name).mkdir(parents=True)
            (project / "scripts/tool.py").write_text("print('offline')\n")
            (project / "src/module.py").write_text("VALUE = 1\n")
            (project / "secrets.env").write_text("must not be copied")
            (project / "artifacts/result.txt").write_text("must not be copied")
            (project / "src/__pycache__").mkdir()
            (project / "src/__pycache__/module.pyc").write_bytes(b"old-cache")
            dest = driver.snapshot_runner(shared, run)
            self.assertTrue((dest / "scripts/tool.py").is_file())
            self.assertFalse((dest / "secrets.env").exists())
            self.assertFalse((dest / "artifacts").exists())
            self.assertFalse((dest / "src/__pycache__").exists())
            hashes = json.loads((run / "runner-snapshot-sha256.json").read_text())
            self.assertEqual(hashes["src/module.py"], hashlib.sha256(b"VALUE = 1\n").hexdigest())

    def test_only_two_requested_representative_tasks(self):
        self.assertEqual(driver.TASKS, (("netty", "2791f0f"), ("presto", "000fa29")))

    def test_export_fix_is_explicit_and_does_not_change_build_or_tests(self):
        original = ["mvn", "-Dair.check.skip-all=true", "dependency:build-classpath", "-DincludeScope=test"]
        result = driver.classpath_export_command(original)
        self.assertEqual(result[-2:], ["-Dair.check.skip-dependency=false", "-Dmdep.skip=false"])
        self.assertEqual(len(original), 4)
        build = ["mvn", "-Dair.check.skip-all=true", "-DskipTests", "install"]
        self.assertEqual(driver.classpath_export_command(build), build)
        verify = ["codex", "sandbox", "--", "python3", "tools.py", "verify"]
        self.assertEqual(driver.classpath_export_command(verify), verify)


if __name__ == "__main__":
    unittest.main()
