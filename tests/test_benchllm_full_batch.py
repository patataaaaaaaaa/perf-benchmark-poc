import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import run_benchllm_full_batch as batch
from benchllm_project_tools import SCALA_LANGUAGE_FLAGS, java_command, result_keys
from src.benchllmrealse.process import run_isolated


class FullBatchTests(unittest.TestCase):
    def test_configuration_home_is_explicit_and_parent_env_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(RuntimeError, 'config is missing'):
                batch.experiment_codex_env(root)
            (root / 'codex-home').mkdir()
            (root / 'codex-home/config.toml').write_text('model_provider="deepseek"')
            with patch.dict(batch.os.environ, {'CODEX_HOME': '/wrong-user-default'}):
                env = batch.experiment_codex_env(root)
                self.assertEqual(str(root / 'codex-home'), env['CODEX_HOME'])
                self.assertEqual('/wrong-user-default', batch.os.environ['CODEX_HOME'])

    def test_cached_preparation_never_reuses_an_agent_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old, new = root / 'old', root / 'new'
            support = old / 'support/34bce1b'
            support.mkdir(parents=True)
            classes = root / 'baseline-classes'
            classes.mkdir()
            (support / 'manifest.json').write_text(json.dumps(dict(task='34bce1b',
                 parent='parent', fix='fix', runtime_classpath=[str(classes)])))
            (support / 'harness.jar').write_bytes(b'harness')
            (new / 'workspaces').mkdir(parents=True)
            metadata = dict(id='34bce1b', repository='RoaringBitmap', commit_hash='fix')
            with patch.object(batch, 'ensure_source', return_value=root / 'source'), \
                    patch.object(batch, 'clone_at') as clone:
                _, workspace, prepared, _ = batch.prepare_cached(root, new, metadata, old)
            self.assertTrue(str(workspace).startswith(str(new)))
            clone.assert_called_once_with(root / 'source', 'parent', workspace)
            self.assertTrue((prepared / 'harness.jar').exists())

    def test_complete_manifest_and_prompts_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for repo, count in [('RoaringBitmap', 5), ('netty', 18), ('kafka', 16), ('presto', 25)]:
                for i in range(count):
                    task = f'{i:07x}'
                    metadata = root / 'BenchLLMRealSE/Dataset/PerfOpt' / repo / (task + '.json')
                    metadata.parent.mkdir(parents=True, exist_ok=True)
                    metadata.write_text(json.dumps(dict(repository=repo, id=task,
                        source_code='m/src/main/java/X.java', unittest='m/src/test/java/TestX.java',
                        jmh_case='m/src/test/java/BenchmarkX.run')))
                    prompt = root / 'BenchLLMRealSE/Prompts' / repo / task / 'prompt4.txt'
                    prompt.parent.mkdir(parents=True, exist_ok=True)
                    prompt.write_text('optimize')
            tasks = batch.discover_tasks(root)
            self.assertEqual(64, len(tasks))
            self.assertEqual(['netty', 'kafka', 'presto'], [d['repository'] for d in tasks[5:8]])
            prompt.unlink()
            with self.assertRaisesRegex(RuntimeError, 'Missing P4'):
                batch.discover_tasks(root)

    def test_benchmark_method_is_not_source_extension(self):
        self.assertEqual('jmh/src/main/java/p/Bench.java',
                         batch.benchmark_path('jmh/src/main/java/p/Bench.measure'))

    def test_billing_error_stops_batch_but_build_error_does_not(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            (path / 'codex_stderr.log').write_text('HTTP 401 invalid_api_key')
            self.assertTrue(batch.global_api_failure(path))
            (path / 'codex_stderr.log').write_text('javac failed: symbol not found')
            self.assertFalse(batch.global_api_failure(path))

    def test_missing_and_duplicate_metrics_are_rejected(self):
        row = dict(benchmark='p.Bench.run', params=dict(n='1'), primaryMetric=dict(score=1.2))
        self.assertEqual([('p.Bench.run', (('n', '1'),))], result_keys([row]))
        for rows in ([], [row, row]):
            with self.assertRaises(RuntimeError):
                result_keys(rows)

    def test_process_tree_timeout(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / 'leaked'
            child = f"import time,pathlib; time.sleep(1); pathlib.Path({str(marker)!r}).touch()"
            parent = f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(10)"
            with self.assertRaises(subprocess.TimeoutExpired):
                run_isolated([sys.executable, '-c', parent], timeout=0.2)
            subprocess.run([sys.executable, '-c', 'import time; time.sleep(1.1)'], check=True)
            self.assertFalse(marker.exists())

    def test_gradle_version_comes_from_wrapper_or_build_script(self):
        wrapper = 'distributionUrl=https\\://services.gradle.org/distributions/gradle-6.6-all.zip\n'
        self.assertEqual('6.6', batch.gradle_version_from_project(wrapper, ''))
        self.assertEqual('3.5', batch.gradle_version_from_project('', "gradleVersion = '3.5'\n"))
        with self.assertRaisesRegex(RuntimeError, 'not declared'):
            batch.gradle_version_from_project('', 'no version')

    def test_truncated_gradle_archive_is_resumed_until_valid(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, 'w') as archive:
            archive.writestr('gradle-9.9.9/bin/gradle', '#!/bin/sh\n')
        data = payload.getvalue()
        part, rest = data[:24], data[24:]
        calls = []

        class Response:
            def __init__(self, status, body):
                self.status = status
                self.body = body
            def read(self, size=-1):
                if size is None or size < 0 or size >= len(self.body):
                    chunk, self.body = self.body, b''
                else:
                    chunk, self.body = self.body[:size], self.body[size:]
                return chunk
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        def opener(request, timeout):
            calls.append(request.headers.get('Range'))
            return Response(200 if len(calls) == 1 else 206, part if len(calls) == 1 else rest)

        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'gradle-9.9.9-bin.zip'
            batch.download_verified_archive('https://example.test/gradle.zip', archive, opener=opener)
            self.assertEqual([None, 'bytes=%d-' % len(part)], calls)
            self.assertTrue(batch.archive_is_complete(archive))

    def test_unrelated_broken_test_can_be_excluded_but_requested_test_cannot(self):
        log = ('/work/transport/src/test/java/io/netty/channel/PendingWriteQueueTest.java:'
               '[262,8] error: reference to assertEquals is ambiguous')
        self.assertEqual(['**/PendingWriteQueueTest.java'], batch.unrelated_test_excludes(
            log, ['codec-http/src/test/java/io/netty/handler/codec/http/HttpRequestEncoderTest.java']))
        self.assertIsNone(batch.unrelated_test_excludes(
            log, ['transport/src/test/java/io/netty/channel/PendingWriteQueueTest.java']))
        self.assertIsNone(batch.unrelated_test_excludes(
            '/work/src/main/java/Foo.java:[1,1] error: cannot find symbol', ['TestFoo.java']))
        pom = batch.pom_with_unrelated_test_excludes('<project>\n</project>\n',
                                                    ['**/PendingWriteQueueTest.java'])
        self.assertIn('benchllm.excludeTests', pom)
        self.assertTrue(pom.rstrip().endswith('</project>'))
        existing = '<project><profiles><profile><id>release</id></profile></profiles></project>'
        merged = batch.pom_with_unrelated_test_excludes(existing, ['**/PendingWriteQueueTest.java'])
        self.assertEqual(1, merged.count('<profiles>'))
        self.assertIn('<id>release</id>', merged)

    def test_source_fetch_retries_then_raises(self):
        attempts = []

        def fail(command, **kwargs):
            attempts.append(command)
            raise subprocess.CalledProcessError(1, command)

        with patch.object(batch, 'run', fail):
            with self.assertRaises(subprocess.CalledProcessError):
                batch.fetch_parent(Path('/source'), 'kafka', 'abc', Path('/tmp/fetch.log'))
        self.assertEqual(3, len(attempts))
        self.assertIn('https://github.com/apache/kafka.git', attempts[0])

    def test_prepare_flags_skip_old_maven_plugins_and_sandbox_jvm_can_preload_mockito(self):
        self.assertIn('-Dfindbugs.skip=true', batch.maven_prepare_flags(Path('/root')))
        self.assertEqual(['-language:postfixOps'], SCALA_LANGUAGE_FLAGS)
        command = java_command('java', '/deps/byte-buddy-agent-1.10.jar:/deps/junit.jar', 'org.junit.Main')
        self.assertEqual('java', command[0])
        self.assertTrue(command[1].startswith('-javaagent:/deps/byte-buddy-agent-'))
        self.assertIn('org.junit.Main', command)

    def test_unpaid_prepare_skips_successes_and_never_starts_agent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            previous = root / 'old-summary.json'
            previous.write_text(json.dumps([
                dict(repository='netty', task='aaaaaaa', outcome='infrastructure_failed'),
                dict(repository='netty', task='bbbbbbb', outcome='succeeded'),
            ]))
            new = root / 'prepare-batch'
            tasks = [dict(repository='netty', id=task, commit_hash='c') for task in ('aaaaaaa', 'bbbbbbb')]
            calls = []

            def fake_prepare(*args, **kwargs):
                return Path('source'), root / 'workspace', root / 'support', {}

            def fake_run(command, **kwargs):
                calls.append([str(part) for part in command])

            with patch.object(batch, 'prepare_project', fake_prepare), patch.object(batch, 'run', fake_run):
                self.assertEqual(0, batch.prepare_unpaid_failures(
                    root, new, tasks, previous, 'codex', {}))
            self.assertEqual(1, len(calls))
            self.assertNotIn('run_benchllm_codex.py', ' '.join(calls[0]))
            self.assertIn('sandbox', calls[0])
            summary = json.loads((new / 'summary.json').read_text())
            self.assertEqual(['aaaaaaa'], [item['task'] for item in summary])
            self.assertFalse(summary[0]['agent_started'])
            self.assertEqual('preparable', summary[0]['outcome'])

    def test_only_tasks_keeps_requested_order_and_rejects_unknown(self):
        tasks = [dict(repository='netty', id='aaaaaaa'), dict(repository='kafka', id='bbbbbbb')]
        selected = batch.select_tasks(tasks, 'kafka/bbbbbbb,netty/aaaaaaa')
        self.assertEqual(['bbbbbbb', 'aaaaaaa'], [item['id'] for item in selected])
        with self.assertRaisesRegex(RuntimeError, 'Unknown tasks'):
            batch.select_tasks(tasks, 'presto/ccccccc')

    def test_atomic_summary_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'summary.json'
            batch.write_json(p, [dict(outcome='infrastructure_failed')])
            batch.write_json(p, [dict(outcome='succeeded')])
            self.assertEqual('succeeded', json.loads(p.read_text())[0]['outcome'])
            self.assertFalse(p.with_suffix('.json.tmp').exists())


if __name__ == '__main__':
    unittest.main()
