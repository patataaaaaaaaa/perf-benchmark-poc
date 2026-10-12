#!/usr/bin/env python3
"""Only remeasure test-passed triples blocked solely by JMH's shared lock."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

import run_benchllm_agent_first as common
from run_benchllm_three_versions import compare_rows


def last_log(case, version, mode):
    paths = sorted((case / 'workspaces' / version).glob('.benchllm-results/' + mode + '-*/commands.log'))
    return paths[-1].read_text(errors='replace') if paths else ''


def eligible(versions, logs):
    if {x['version'] for x in versions} != {'original', 'developer', 'agent'}:
        return False
    if any(x.get('verify') != 'passed' for x in versions):
        return False
    failed = [x for x in versions if x.get('benchmark') != 'passed']
    return bool(failed) and all(x.get('benchmark') == 'CalledProcessError' and
            'Unable to acquire the JMH lock' in logs.get(x['version'], '') for x in failed)


def selection(previous):
    accepted, excluded = [], []
    for item in json.loads((previous / 'summary.json').read_text()):
        if item['outcome'] == 'succeeded':
            continue
        case = Path(item['case_dir'])
        versions = json.loads((case / 'summary.json').read_text()) if (case / 'summary.json').exists() else []
        logs = {x['version']: last_log(case, x['version'], 'benchmark') for x in versions}
        value = dict(repository=item['repository'], task=item['task'], prior_case=str(case))
        if eligible(versions, logs):
            accepted.append(value)
        else:
            value['versions'] = [{k: x.get(k) for k in ('version', 'verify', 'benchmark')} for x in versions]
            value['reason'] = 'not all three tests passed, or a non-lock benchmark failure; no further attempt'
            excluded.append(value)
    return accepted, excluded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-batch', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    args = parser.parse_args()
    previous, root = args.from_batch.resolve(), args.run_root.resolve()
    if root.parent != previous.parent or not root.name.startswith('three-versions-eligible-'):
        raise ValueError('Unexpected remeasurement directory')
    if (root / 'protocol.json').exists():
        raise ValueError('Do not restart or overwrite an existing remeasurement')
    root.mkdir(exist_ok=True)
    os.sched_setaffinity(0, {0, 1})
    common.write(root / 'pid.json', dict(pid=os.getpid(), started=common.now()))
    common.write(root / 'protocol.json', dict(started=common.now(), predecessor=str(previous), model_calls=0,
         eligibility='All three native tests passed; every failed JMH version failed solely on the shared lock',
         cpus=[0, 1], test_seconds=600, benchmark_seconds=900,
         jmh=dict(warmup=10, measurement=50, forks=1, seconds=1),
         temp_policy='Private per-version java.io.tmpdir; do not disable JMH locking',
         policy='Wait for existing comparisons; one remeasurement per eligible task, serial; preserve originals'))
    summary = []
    try:
        queued, excluded = selection(previous)
        common.write(root / 'queue.json', queued)
        common.write(root / 'excluded.json', excluded)
        (root / 'status.txt').write_text(f'waiting for predecessor; {len(queued)} currently eligible\n')
        pid = json.loads((previous / 'pid.json').read_text())['pid']
        while not (previous / 'completion.json').exists():
            cmdline = Path('/proc') / str(pid) / 'cmdline'
            if not cmdline.exists() or str(previous).encode() not in cmdline.read_bytes():
                raise RuntimeError('Predecessor exited without completion; do not silently start overlapping measurements')
            time.sleep(15)
        queued, excluded = selection(previous)
        common.write(root / 'queue.json', queued)
        common.write(root / 'excluded.json', excluded)
        common.write(root / 'summary.json', summary)
        for item in queued:
            case = Path(item['prior_case'])
            out = root / 'tasks' / item['repository'] / item['task']
            out.mkdir(parents=True)
            result = dict(**item, started=common.now(), attempt_kind='unpaid measurement retry', versions=[])
            rows = {}
            for version in ('original', 'developer', 'agent'):
                plan = json.loads((case / 'versions' / (version + '-plan.json')).read_text())
                workspace = Path(plan['workspace'])
                # Frozen source snapshots, tests and harness must remain unchanged.
                if common.command(['git', 'diff', '--name-only', 'HEAD'], cwd=workspace):
                    raise RuntimeError('Previously frozen source files changed; refuse remeasurement')
                temp = workspace / '.benchllm-results' / ('isolated-java-temp-' + str(time.time_ns()))
                temp.mkdir(parents=True)
                env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ('API_KEY', 'TOKEN', 'SECRET'))}
                env['CODEX_HOME'] = str(case / 'codex-home')
                env['JAVA_TOOL_OPTIONS'] = env.get('JAVA_TOOL_OPTIONS', '') + ' -Djava.io.tmpdir=' + str(temp)
                value = dict(version=version, private_java_temp=str(temp), started=common.now())
                for mode, limit in [('verify', 600), ('benchmark', 900)]:
                    (root / 'status.txt').write_text(f'remeasure {len(summary)}/{len(queued)}; {item["repository"]}/{item["task"]}: {version} {mode}\n')
                    try:
                        common.command(['/downloads/patataWJY/.local/bin/codex', 'sandbox', '--permission-profile', 'agent_eval',
                            '--cd', workspace, '--', sys.executable, Path(__file__).with_name('benchllm_native.py'), mode,
                            '--plan', case / 'versions' / (version + '-plan.json')], env=env,
                            log=out / (version + '-' + mode + '.log'), timeout=limit)
                        value[mode] = 'passed'
                        if mode == 'benchmark':
                            reports = sorted(workspace.glob('.benchllm-results/benchmark-*/result.json'))
                            report = json.loads(reports[-1].read_text())
                            file = Path(report['result'])
                            rows[version] = json.loads(file.read_text())
                            common.write(out / (version + '-jmh.json'), rows[version])
                    except Exception as exc:
                        value[mode] = type(exc).__name__
                        value[mode + '_error'] = str(exc)
                    if mode == 'verify' and value[mode] != 'passed':
                        value['benchmark'] = 'not_run_test_failed'
                        break
                value['ended'] = common.now()
                result['versions'].append(value)
                common.write(out / 'result.json', result)
            result['outcome'] = 'version_failure'
            if len(rows) == 3:
                try:
                    common.write(out / 'comparison.json', compare_rows(rows))
                    result['outcome'] = 'succeeded'
                except Exception as exc:
                    result.update(outcome='coverage_or_metric_mismatch', error=str(exc))
            result['ended'] = common.now()
            common.write(out / 'result.json', result)
            summary.append(result)
            common.write(root / 'summary.json', summary)
        common.write(root / 'completion.json', dict(ended=common.now(), processed=len(summary),
                       comparisons_passed=sum(x['outcome']=='succeeded' for x in summary)))
        (root / 'status.txt').write_text(f'complete; {len(summary)} eligible remeasurements processed; no further retries\n')
    except Exception as exc:
        common.write(root / 'queue-error.json', dict(error_type=type(exc).__name__, error=str(exc), ended=common.now()))
        (root / 'error.log').write_text(traceback.format_exc())
        (root / 'status.txt').write_text('queue_failed\n')
        raise


if __name__ == '__main__':
    main()
