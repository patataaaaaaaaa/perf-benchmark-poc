import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "java_tools", Path(__file__).resolve().parents[1] / "scripts/benchllm_java_tools.py")
java_tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(java_tools)


class JMHCommandTests(unittest.TestCase):
    def command(self, quick):
        return java_tools.jmh_command(
            "overlay:first:classpath", {"pattern": ".*Benchmark.*", "args": ["-p", "count=1000"]},
            Path("jmh.json"), quick=quick)

    def test_quick_is_socket_free_no_fork(self):
        command = self.command(True)
        self.assertEqual("0", command[command.index("-f") + 1])
        self.assertEqual("1", command[command.index("-wi") + 1])
        self.assertEqual("2", command[command.index("-i") + 1])

    def test_final_keeps_independent_jvms(self):
        command = self.command(False)
        self.assertEqual("2", command[command.index("-f") + 1])
        self.assertEqual("5", command[command.index("-wi") + 1])
        self.assertEqual("10", command[command.index("-i") + 1])

    def test_both_modes_keep_classpath_params_and_failures(self):
        for quick in (False, True):
            command = self.command(quick)
            self.assertEqual("overlay:first:classpath", command[command.index("-cp") + 1])
            self.assertEqual("true", command[command.index("-foe") + 1])
            self.assertEqual(["-p", "count=1000"], command[-2:])


if __name__ == "__main__":
    unittest.main()
