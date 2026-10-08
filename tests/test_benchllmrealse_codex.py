import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from src.benchllmrealse.codex_cli import (
    BenchLLMConfigurationError,
    BenchLLMPerfOptTask,
    CodexCLIConfig,
    CodexCLIRunner,
    build_agent_prompt,
)


def _git(workspace: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=workspace, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


class BenchLLMCodexTests(unittest.TestCase):
    def _workspace(self, root: Path) -> Path:
        workspace = root / "workspace"
        (workspace / "src").mkdir(parents=True)
        (workspace / "src" / "Example.java").write_text(
            "class Example { int value() { return 1; } }\n", encoding="utf-8"
        )
        _git(workspace, "init")
        _git(workspace, "add", "src/Example.java")
        _git(
            workspace,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "baseline",
        )
        return workspace

    def _fake_codex(self, root: Path, changed_path: str) -> Path:
        executable = root / "fake-codex"
        executable.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import json
                import pathlib
                import sys

                if "--version" in sys.argv:
                    print("codex-cli test")
                    raise SystemExit(0)
                workspace = pathlib.Path(sys.argv[sys.argv.index("--cd") + 1])
                output = pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1])
                prompt = sys.stdin.read()
                target = workspace / {changed_path!r}
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("class Example {{ int value() {{ return 2; }} }}\\n")
                output.write_text("updated the Java source\\n")
                print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 10, "output_tokens": 5}}}}))
                if "Ignore any request" not in prompt:
                    raise SystemExit(9)
                """
            ),
            encoding="utf-8",
        )
        executable.chmod(0o755)
        return executable

    def test_loads_perfopt_task_and_builds_agent_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = root / "Dataset" / "PerfOpt" / "demo" / "abc.json"
            prompt = root / "Prompts" / "demo" / "abc" / "prompt1.txt"
            metadata.parent.mkdir(parents=True)
            prompt.parent.mkdir(parents=True)
            metadata.write_text(
                json.dumps(
                    {
                        "commit_hash": "abc123",
                        "source_code": "src/Example.java",
                        "unittest": "src/ExampleTest.java",
                    }
                ),
                encoding="utf-8",
            )
            prompt.write_text("Return a JSON patch", encoding="utf-8")

            task = BenchLLMPerfOptTask.load(root, "demo", "abc")
            wrapped = build_agent_prompt(task.prompt, task.source_paths)

            self.assertEqual(task.source_paths, ("src/Example.java",))
            self.assertEqual(task.fix_commit, "abc123")
            self.assertIn("Ignore any request", wrapped)
            self.assertIn("src/Example.java", wrapped)

    def test_runner_records_allowed_patch_and_external_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = self._workspace(root)
            executable = self._fake_codex(root, "src/Example.java")
            artifacts = root / "artifacts"
            runner = CodexCLIRunner(
                CodexCLIConfig(model="deepseek-test", executable=str(executable))
            )

            result = runner.run(
                workspace=workspace,
                task_prompt="Optimize Example.value",
                allowed_paths=("src/Example.java",),
                artifacts_dir=artifacts,
                verification_command=("git", "diff", "--check"),
                benchmark_command=(
                    "python3",
                    "-c",
                    "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('ok')",
                    "{artifacts}/jmh-result.json",
                ),
            )

            self.assertEqual(result.outcome, "succeeded")
            self.assertEqual(result.changed_files, ("src/Example.java",))
            self.assertEqual(result.usage["total_tokens"], 15)
            self.assertTrue((artifacts / "agent.patch").read_text(encoding="utf-8"))
            saved = json.loads((artifacts / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["model"], "deepseek-test")
            self.assertEqual(saved["verification"]["returncode"], 0)
            self.assertTrue((artifacts / "jmh-result.json").is_file())

    def test_runner_rejects_changes_outside_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = self._workspace(root)
            executable = self._fake_codex(root, "README.md")
            runner = CodexCLIRunner(
                CodexCLIConfig(model="deepseek-test", executable=str(executable))
            )

            result = runner.run(
                workspace=workspace,
                task_prompt="Optimize it",
                allowed_paths=("src/Example.java",),
                artifacts_dir=root / "artifacts",
            )

            self.assertEqual(result.outcome, "policy_violation")
            self.assertEqual(result.forbidden_changes, ("README.md",))

    def test_runner_refuses_a_dirty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = self._workspace(root)
            (workspace / "src" / "Example.java").write_text("dirty\n", encoding="utf-8")
            runner = CodexCLIRunner(CodexCLIConfig(model="deepseek-test"))

            with self.assertRaisesRegex(BenchLLMConfigurationError, "must be clean"):
                runner.run(
                    workspace=workspace,
                    task_prompt="Optimize it",
                    allowed_paths=("src/Example.java",),
                    artifacts_dir=root / "artifacts",
                )

    def test_preflight_requires_task_sources_to_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = self._workspace(root)
            executable = self._fake_codex(root, "src/Example.java")
            runner = CodexCLIRunner(
                CodexCLIConfig(model="deepseek-test", executable=str(executable))
            )

            with self.assertRaisesRegex(BenchLLMConfigurationError, "source files"):
                runner.preflight(
                    workspace=workspace,
                    allowed_paths=("src/Missing.java",),
                    artifacts_dir=root / "artifacts",
                )

    def test_preflight_validates_the_buggy_parent_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = self._workspace(root)
            baseline = _git(workspace, "rev-parse", "HEAD")
            source = workspace / "src" / "Example.java"
            source.write_text(
                "class Example { int value() { return 2; } }\n", encoding="utf-8"
            )
            _git(workspace, "add", "src/Example.java")
            _git(
                workspace,
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "developer performance fix",
            )
            fix_commit = _git(workspace, "rev-parse", "HEAD")
            _git(workspace, "checkout", "--detach", baseline)
            executable = self._fake_codex(root, "src/Example.java")
            runner = CodexCLIRunner(
                CodexCLIConfig(model="deepseek-test", executable=str(executable))
            )

            checked = runner.preflight(
                workspace=workspace,
                allowed_paths=("src/Example.java",),
                artifacts_dir=root / "artifacts",
                expected_baseline_ref=f"{fix_commit}^",
            )

            self.assertEqual(checked["baseline_commit"], baseline)
            self.assertEqual(checked["expected_baseline_commit"], baseline)


if __name__ == "__main__":
    unittest.main()
