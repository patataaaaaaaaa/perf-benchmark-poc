import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from inspect_benchllm_batch import inspect_batch


class MonitorTests(unittest.TestCase):
    def test_requires_real_usage_tests_and_jmh_not_just_summary_success(self):
        with tempfile.TemporaryDirectory() as temp:
            batch = Path(temp)
            output = batch / 'tasks/demo/abc/prompt4'
            output.mkdir(parents=True)
            (batch / 'summary.json').write_text(json.dumps([dict(agent_started=True, outcome='succeeded')]))
            (output / 'agent.patch').write_text('diff --git a/X.java b/X.java')
            (output / 'jmh.json').write_text('[{"benchmark":"p.B.run"}]')
            result = dict(outcome='succeeded', usage=dict(total_tokens=0),
                          verification=dict(returncode=0), benchmark=dict(returncode=0), forbidden_changes=[])
            (output / 'result.json').write_text(json.dumps(result))
            self.assertEqual(0, inspect_batch(batch)['confirmed_successes'])
            result['usage']['total_tokens'] = 12
            (output / 'result.json').write_text(json.dumps(result))
            self.assertEqual(1, inspect_batch(batch)['confirmed_successes'])
            result['verification']['returncode'] = 1
            (output / 'result.json').write_text(json.dumps(result))
            self.assertEqual(0, inspect_batch(batch)['confirmed_successes'])

    def test_build_failure_does_not_count_as_agent_success(self):
        with tempfile.TemporaryDirectory() as temp:
            batch = Path(temp)
            (batch / 'summary.json').write_text(json.dumps([dict(agent_started=False, outcome='infrastructure_failed')]))
            state = inspect_batch(batch)
            self.assertEqual(1, state['processed_tasks'])
            self.assertEqual(0, state['agent_runs_started'])
            self.assertEqual(0, state['confirmed_successes'])

    def test_running_agent_is_counted_before_its_summary_row(self):
        with tempfile.TemporaryDirectory() as temp:
            batch = Path(temp)
            (batch / 'budget.json').write_text('{"agent_runs_started":1}')
            state = inspect_batch(batch)
            self.assertEqual(1, state['agent_runs_started'])
            self.assertEqual(0, state['processed_tasks'])
            self.assertEqual(0, state['confirmed_successes'])


if __name__ == '__main__':
    unittest.main()
