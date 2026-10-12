#!/usr/bin/env python3
"""Freeze all prior passed cases and automatically compare three versions."""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback

import run_benchllm_agent_first as common


def descendants(pid):
    pending, seen = [pid], set()
    while pending:
        value = pending.pop()
        if value in seen:
            continue
        seen.add(value)
        path = Path('/proc') / str(value) / 'task' / str(value) / 'children'
        try:
            pending += [int(s) for s in path.read_text().split()]
        except FileNotFoundError:
            pass
    return seen


def affinity_tree(pid, mask):
    changed = []
    for child in descendants(pid):
        try:
            tasks = list((Path('/proc') / str(child) / 'task').iterdir())
        except FileNotFoundError:
            continue
        for thread in tasks:
            try:
                os.sched_setaffinity(int(thread.name), mask)
                changed.append(int(thread.name))
            except ProcessLookupError:
                pass
    return changed


def completed_cases(native, rows):
    lookup = {(x['repository'], x['task']): x for x in rows}
    return [dict(repository=x['repository'], task=x['task']) for x in native
            if x.get('verify') == 'passed' and x.get('benchmark') == 'passed'
            and lookup[(x['repository'], x['task'])].get('has_source_patch')
            and not lookup[(x['repository'], x['task'])].get('invalid_changes')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--shared-root', type=Path, required=True)
    parser.add_argument('--from-batch', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--cpus', required=True)
    parser.add_argument('--parallel-agent-batch', type=Path, required=True)
    args = parser.parse_args()
    shared, root, source = args.shared_root.resolve(), args.run_root.resolve(), args.from_batch.resolve()
    if root.parent != shared / 'artifacts/benchllmrealse' or not root.name.startswith('three-versions-batch'):
        raise ValueError('Unexpected comparison batch path')
    if (root / 'protocol.json').exists():
        raise ValueError('Refuse duplicate batch')
    cpus = {int(v) for v in args.cpus.split(',')}
    allowed = set(os.sched_getaffinity(0))
    if not cpus or not cpus.issubset(allowed) or not (allowed - cpus):
        raise ValueError('Invalid comparison/agent CPU allocation')
    root.mkdir(exist_ok=True)
    (root / 'cases').mkdir()
    common.write(root / 'pid.json', dict(pid=os.getpid(), started=common.now()))
    retry = args.parallel_agent_batch.resolve()
    pid = json.loads((retry / 'pid.json').read_text())['pid']
    original_mask = None
    summary = []
    try:
        native = json.loads((source / 'native-summary.json').read_text())
        queue = completed_cases(native, json.loads((source / 'summary.json').read_text()))
        if not queue:
            raise ValueError('No completed source patches to compare')
        cmdline = Path('/proc') / str(pid) / 'cmdline'
        if cmdline.exists():
            line = cmdline.read_bytes()
            if b'run_benchllm_agent_first.py' not in line or str(retry).encode() not in line:
                raise ValueError('Agent PID does not match authorized batch')
            original_mask = set(os.sched_getaffinity(pid))
            changed = affinity_tree(pid, allowed - cpus)
            common.write(retry / 'resource-allocation.json', dict(time=common.now(),
                         comparison_batch=str(root), previous_cpus=sorted(original_mask),
                         agent_cpus=sorted(allowed-cpus), comparison_cpus=sorted(cpus),
                         note='Temporary allocation for parallel comparison; time limit remains 600 seconds'))
        else:
            changed = []
        os.sched_setaffinity(0, cpus)
        common.write(root / 'protocol.json', dict(started=common.now(), tasks=len(queue), model_calls=0,
             source_batch=str(source), parallel_agent_batch=str(retry), comparison_cpus=sorted(cpus),
             agent_cpus=sorted(allowed-cpus), changed_agent_threads=changed,
             source_selection='first-pass completed patches frozen; retry results not substituted',
             policy='serial native three-version comparison; failed case continues',
             limitations='Whole SMT core separated from this agent queue; shared memory/IO and other users remain'))
        common.write(root / 'queue.json', queue)
        common.write(root / 'summary.json', summary)
        for item in queue:
            repo, task = item['repository'], item['task']
            case = root / 'cases' / ('three-versions-' + repo + '-' + task)
            (root / 'status.txt').write_text(f'comparisons {len(summary)}/{len(queue)}; {repo}/{task}\n')
            record = dict(repository=repo, task=task, started=common.now(), case_dir=str(case))
            try:
                common.command([sys.executable, Path(__file__).with_name('run_benchllm_three_versions.py'),
                     '--shared-root', shared, '--from-batch', source, '--run-root', case,
                     '--task', repo + '/' + task, '--cpus', args.cpus],
                     log=root / (repo + '-' + task + '.log'), timeout=5400)
                completion = json.loads((case / 'completion.json').read_text())
                record['outcome'] = 'succeeded' if completion['complete_comparison'] else 'version_failure'
            except Exception as exc:
                record.update(outcome='case_error', error_type=type(exc).__name__, error=str(exc))
            record['ended'] = common.now()
            summary.append(record)
            common.write(root / 'summary.json', summary)
        common.write(root / 'completion.json', dict(ended=common.now(), processed=len(summary),
                     comparisons_passed=sum(x['outcome']=='succeeded' for x in summary)))
        (root / 'status.txt').write_text(f'complete; {len(summary)} comparison cases processed\n')
    except Exception as exc:
        common.write(root / 'queue-error.json', dict(error_type=type(exc).__name__, error=str(exc)))
        (root / 'error.log').write_text(traceback.format_exc())
        (root / 'status.txt').write_text('queue_failed\n')
        raise
    finally:
        if original_mask is not None:
            cmdline = Path('/proc') / str(pid) / 'cmdline'
            if cmdline.exists() and str(retry).encode() in cmdline.read_bytes():
                changed = affinity_tree(pid, original_mask)
                common.write(root / 'affinity-restored.json', dict(time=common.now(), cpus=sorted(original_mask), threads=changed))


if __name__ == '__main__':
    main()
