import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_benchllm_three_versions import compare_rows
from run_benchllm_comparison_batch import completed_cases
from remeasure_eligible_comparisons import eligible


def row(score, mode='thrpt', unit='ops/s'):
    return dict(benchmark='Example.bench', params={'size': '100'}, mode=mode,
                primaryMetric=dict(score=score, scoreUnit=unit))


class ComparisonTests(unittest.TestCase):
    def test_only_passed_triples_with_lock_failures_are_remeasured(self):
        versions = [dict(version=v, verify='passed', benchmark='CalledProcessError') for v in ('original', 'developer', 'agent')]
        logs = {v['version']: 'Unable to acquire the JMH lock (/tmp/jmh.lock)' for v in versions}
        self.assertTrue(eligible(versions, logs))
        versions[0]['verify'] = 'CalledProcessError'
        self.assertFalse(eligible(versions, logs))

    def test_mixed_nonlock_failure_and_success_are_not_requeued(self):
        versions = [dict(version=v, verify='passed', benchmark='CalledProcessError') for v in ('original', 'developer', 'agent')]
        logs = {v['version']: 'Unable to acquire the JMH lock' for v in versions}
        logs['original'] = 'Compilation failure: private access in NetUtil'
        self.assertFalse(eligible(versions, logs))
        for v in versions:
            v['benchmark'] = 'passed'
        self.assertFalse(eligible(versions, logs))

    def test_batch_selects_all_valid_completed_patches_including_timeout(self):
        native = [dict(repository='presto', task=str(i), verify='passed', benchmark='passed') for i in range(3)]
        rows = [dict(repository='presto', task='0', has_source_patch=True, outcome='timeout'),
                dict(repository='presto', task='1', has_source_patch=True, outcome='agent_completed'),
                dict(repository='presto', task='2', has_source_patch=False)]
        self.assertEqual([x['task'] for x in completed_cases(native, rows)], ['0', '1'])

    def test_throughput_speedup(self):
        result = compare_rows(dict(original=[row(10)], developer=[row(20)], agent=[row(15)]))[0]
        self.assertEqual(result['speedup_vs_original'], dict(developer=2, agent=1.5))

    def test_time_speedup(self):
        result = compare_rows({k: [row(v, 'avgt', 'ns/op')] for k, v in dict(original=20, developer=10, agent=5).items()})[0]
        self.assertEqual(result['speedup_vs_original']['agent'], 4)

    def test_case_coverage_must_match(self):
        other = row(15)
        other['params'] = {'size': '200'}
        with self.assertRaises(RuntimeError):
            compare_rows(dict(original=[row(10)], developer=[row(20)], agent=[other]))

    def test_units_must_match(self):
        with self.assertRaises(RuntimeError):
            compare_rows(dict(original=[row(10)], developer=[row(20)], agent=[row(15, unit='ns/op')]))


if __name__ == '__main__':
    unittest.main()
