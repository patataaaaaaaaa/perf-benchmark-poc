import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_benchllm_agent_first as batch
import benchllm_native as native


class AgentFirstTests(unittest.TestCase):
    def test_retry_selects_timeouts_not_successes_or_source_errors(self):
        tasks = [dict(repository='netty', id=t) for t in ('a', 'b', 'c')]
        first = [dict(repository='netty', task='a', outcome='timeout'),
                 dict(repository='netty', task='b', outcome='agent_completed'),
                 dict(repository='netty', task='c', outcome='task_error')]
        self.assertEqual(batch.timeout_retry_tasks(tasks, first), [tasks[0]])
        self.assertEqual(first[0]['outcome'], 'timeout')

    def test_retry_duplicate_or_unknown_rejected(self):
        row = dict(repository='netty', task='a', outcome='timeout')
        with self.assertRaises(ValueError):
            batch.timeout_retry_tasks([], [row])
        with self.assertRaises(ValueError):
            batch.timeout_retry_tasks([dict(repository='netty', id='a')], [row, row])

    def test_exec_permission_profile_uses_configuration(self):
        runner = batch.AgentRunner(batch.cli.CodexCLIConfig(model='deepseek-v4-pro'))
        with patch.object(runner, '_resolved_executable', return_value='/bin/codex'):
            command = runner.command(Path('/workspace'), Path('/output/last.txt'))
        self.assertEqual(command[:2], ['/bin/codex', 'exec'])
        self.assertIn('default_permissions="agent_eval"', command)
        self.assertNotIn('--permission-profile', command)
        self.assertNotIn('--sandbox', command)

    def test_failure_does_not_block_next_task(self):
        rows, saved = [], []
        def handler(m):
            if m['id'] == 'bad':
                raise RuntimeError('build failure')
            return {'task': m['id'], 'outcome': 'agent_completed'}
        self.assertTrue(batch.run_tasks([dict(repository='netty', id=i) for i in ('bad', 'good')],
                        handler, rows, lambda r: saved.append(list(r))))
        self.assertEqual([r['outcome'] for r in rows], ['task_error', 'agent_completed'])
        self.assertEqual(len(saved), 2)

    def test_global_billing_error_stops(self):
        rows = []
        self.assertFalse(batch.run_tasks([{}, {}], lambda _: {'global_stop_reason': 'billing'}, rows, lambda _: None))
        self.assertEqual(len(rows), 1)

    def test_environment_allowlist_not_tests(self):
        self.assertTrue(batch.configuration_path('gradle/dependencies.gradle'))
        self.assertTrue(batch.configuration_path('module/pom.xml'))
        self.assertFalse(batch.configuration_path('module/src/test/java/Test.java'))
        self.assertFalse(batch.configuration_path('module/src/main/java/Other.java'))

    def test_prompt_allows_diagnosis_without_prebuild(self):
        prompt = batch.agent_prompt('Optimize foo', ['src/Foo.java'])
        self.assertIn('diagnose build failures', prompt)
        self.assertIn('Do not modify tests', prompt)
        self.assertNotIn('build has passed', prompt)

    def test_archive_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with tarfile.open(root / 'bad.tar', 'w') as archive:
                info = tarfile.TarInfo('../escape')
                info.size = 1
                archive.addfile(info, io.BytesIO(b'x'))
            with self.assertRaises(ValueError):
                batch.safe_archive(root / 'bad.tar', root / 'workspace')

    def test_gradle_variable_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'gradle').mkdir()
            (root / 'build.gradle').write_text('gradleVersion = versions.gradle')
            (root / 'gradle/dependencies.gradle').write_text('versions = [gradle: "5.6.2"]')
            self.assertEqual(native.gradle_version(root), '5.6.2')

    def test_zero_test_reports_not_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(RuntimeError):
                native.test_reports(Path(temp), ['module'], 0)

    def test_profile_hides_reference_and_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            shared = Path(temp)
            (shared / 'artifacts/benchllmrealse/history').mkdir(parents=True)
            config = batch.profile_config('', shared, shared / 'artifacts/benchllmrealse/new')
            self.assertIn('extends = ":workspace"', config)
            self.assertIn('secrets.env" = "deny"', config)
            self.assertIn('history" = "deny"', config)
            self.assertNotIn('danger-full-access', config)

    def test_legacy_sandbox_config_removed_from_private_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'artifacts/benchllmrealse').mkdir(parents=True)
            config = batch.profile_config('sandbox_mode="workspace-write"\n[sandbox_workspace_write]\nnetwork_access=false\n[model_providers.foo]\nenv_key="KEY"\n', root, root / 'artifacts/benchllmrealse/new')
            self.assertNotIn('sandbox_mode=', config)
            self.assertNotIn('[sandbox_workspace_write]', config)
            self.assertIn('[model_providers.foo]', config)
            self.assertTrue(config.startswith('default_permissions'))


if __name__ == '__main__':
    unittest.main()
