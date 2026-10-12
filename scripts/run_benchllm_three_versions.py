#!/usr/bin/env python3
"""One completed task, three source versions, native tests and matched JMH."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import traceback

import run_benchllm_agent_first as common
from benchllm_project_tools import result_keys


def fingerprint(workspace, excluded):
    result = {}
    names = common.command(['git', 'ls-files', '-z'], cwd=workspace).split('\0')
    for name in names:
        if name and name not in excluded:
            result[name] = hashlib.sha256((workspace / name).read_bytes()).hexdigest()
    return result


def compare_rows(versions):
    keys = {name: result_keys(rows) for name, rows in versions.items()}
    if any(value != keys['original'] for value in keys.values()):
        raise RuntimeError('Three versions have different JMH case/parameter coverage')
    indexed = {name: {(r['benchmark'], tuple(sorted(r.get('params', {}).items()))): r for r in rows}
               for name, rows in versions.items()}
    result = []
    for key in keys['original']:
        rows = {name: mapping[key] for name, mapping in indexed.items()}
        unit = rows['original']['primaryMetric']['scoreUnit']
        mode = rows['original']['mode']
        if mode not in ('thrpt', 'avgt', 'sample', 'ss') or any(
                r['mode'] != mode or r['primaryMetric']['scoreUnit'] != unit for r in rows.values()):
            raise RuntimeError('JMH mode or units are not comparable')
        scores = {name: r['primaryMetric']['score'] for name, r in rows.items()}
        speedups = {name: scores[name] / scores['original'] if mode == 'thrpt'
                    else scores['original'] / scores[name] for name in ('developer', 'agent')}
        result.append(dict(benchmark=key[0], params=dict(key[1]), mode=mode, unit=unit,
                           scores=scores, speedup_vs_original=speedups))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--shared-root', type=Path, required=True)
    parser.add_argument('--from-batch', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--cpus', required=True)
    args = parser.parse_args()
    shared, root, previous = args.shared_root.resolve(), args.run_root.resolve(), args.from_batch.resolve()
    base_dir = shared / 'artifacts/benchllmrealse'
    nested = (root.parent.name == 'cases' and root.parent.parent.name.startswith('three-versions-batch')
              and root.parent.parent.parent == base_dir)
    if (root.parent != base_dir and not nested) or not root.name.startswith('three-versions-'):
        raise ValueError('Unexpected comparison path')
    if (root / 'protocol.json').exists():
        raise ValueError('Refuse to overwrite existing comparison')
    cpus = {int(value) for value in args.cpus.split(',')}
    os.sched_setaffinity(0, cpus)
    root.mkdir(exist_ok=True)
    common.write(root / 'pid.json', dict(pid=os.getpid(), started=common.now()))
    try:
        repo, task = args.task.split('/')
        prior_out = previous / 'tasks' / repo / task
        plan = json.loads((prior_out / 'native-plan.json').read_text())
        metadata, agent_workspace = plan['metadata'], Path(plan['workspace'])
        prior_result = json.loads((prior_out / 'result.json').read_text())
        evaluation = json.loads((prior_out / 'native-evaluation.json').read_text())
        if evaluation.get('benchmark') != 'passed' or not prior_result.get('has_source_patch') or prior_result.get('invalid_changes'):
            raise ValueError('Select a prior passed task with a permitted source patch')
        source_paths = shlex.split(metadata['source_code'])
        config_paths = prior_result.get('environment_changes', [])
        if any(not common.configuration_path(name) for name in config_paths):
            raise ValueError('Unexpected environment change')
        for folder in ('cache', 'codex-home', 'versions'):
            (root / folder).mkdir()
        # Existing paid agents already deny this source prefix, including future
        # directories. Do not expose developer answers in a newly visible batch.
        physical = shared / 'sources/measurement-fixtures' / hashlib.sha256(str(root).encode()).hexdigest()[:16]
        physical.mkdir(parents=True)
        (root / 'workspaces').symlink_to(physical, target_is_directory=True)
        # No provider token is loaded or model API called in this program.
        base = (shared / 'codex-home/config.toml').read_text()
        profile = common.profile_config(base, shared, root)
        profile = profile.replace(json.dumps(str(shared / 'sources')) + ' = "deny"\n', '')
        (root / 'codex-home/config.toml').write_text(profile)
        env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ('API_KEY', 'TOKEN', 'SECRET'))}
        env['CODEX_HOME'] = str(root / 'codex-home')
        common.write(root / 'protocol.json', dict(started=common.now(), repository=repo, task=task,
              source_batch=str(previous), cpu_affinity=sorted(cpus), versions=['original', 'developer', 'agent'],
              test_seconds=600, benchmark_seconds=900, jmh=dict(warmup=10, measurement=50, forks=1, seconds=1),
              orchestration_revision=2, eligibility_gate='all three native tests pass before any JMH',
              model_calls=0, agent_results_remeasured=True, common_environment_changes=config_paths,
              limitations='One measurement round; concurrent host memory/IO load can still affect results'))
        (root / 'status.txt').write_text('setup: private Maven cache copy; no model calls\n')
        shutil.copytree(previous / 'cache/maven', root / 'cache/maven', copy_function=common.cached_copy)
        (root / 'cache/gradle').mkdir()
        (root / 'cache/tools').mkdir()
        fixture = json.loads((prior_out / 'fixture.json').read_text())
        baseline = common.command(['git', 'rev-parse', 'benchllm-prepare^{}'], cwd=agent_workspace)
        if common.command(['git', 'rev-parse', 'HEAD'], cwd=agent_workspace) != baseline:
            raise ValueError('Agent workspace baseline commit was changed')
        candidates = [shared / 'sources' / repo,
                      shared / 'artifacts/benchllmrealse' / common.HISTORY[-1] / 'sources' / repo]
        source = None
        for candidate in candidates:
            try:
                common.command(['git', '-C', candidate, 'cat-file', '-e', fixture['fix'] + ':' + source_paths[0]])
                source = candidate
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        if source is None:
            raise RuntimeError('Developer source object unavailable; do not use generated replacement')
        frozen = None
        for version in ('original', 'developer', 'agent'):
            workspace = root / 'workspaces' / version
            workspace.mkdir()
            archive = root / 'versions' / (version + '.tar')
            common.command(['git', 'archive', '--format=tar', '--output=' + str(archive), baseline], cwd=agent_workspace)
            common.safe_archive(archive, workspace)
            archive.unlink()
            for name in config_paths:
                target = workspace / name
                changed = agent_workspace / name
                if changed.is_symlink():
                    raise ValueError('Environment symlink is not supported')
                if changed.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(changed, target)
                elif target.exists():
                    target.unlink()
            for name in source_paths:
                if version == 'agent':
                    (workspace / name).write_bytes((agent_workspace / name).read_bytes())
                elif version == 'developer':
                    (workspace / name).write_bytes(subprocess.check_output(['git', '-C', str(source), 'show', fixture['fix'] + ':' + name]))
            common.command(['git', 'init', workspace])
            with (workspace / '.git/info/exclude').open('a') as file:
                file.write('\n.benchllm-results/\n')
            common.command(['git', 'add', '-A'], cwd=workspace)
            digest = fingerprint(workspace, set(source_paths))
            if frozen is not None and digest != frozen:
                raise RuntimeError('Non-target files, tests or harness differ between versions')
            frozen = digest
            common.command(['git', '-c', 'user.name=Benchmark', '-c', 'user.email=benchmark@localhost',
                            'commit', '-m', 'Frozen ' + version + ' measurement fixture'], cwd=workspace)
            common.write(root / 'versions' / (version + '-plan.json'),
                         dict(metadata=metadata, workspace=str(workspace), root=str(root), native_stage_timeout_seconds=600))
        common.write(root / 'common-fixture-hashes.json', frozen)
        rows, summary = {}, []
        def measure(record, mode, limit):
            version = record['version']
            workspace = root / 'workspaces' / version
            (root / 'status.txt').write_text(f'{repo}/{task}: {version} {mode}\n')
            common.write(root / 'versions' / (version + '-' + mode + '-host.json'),
                         dict(time=common.now(), cpu_affinity=sorted(os.sched_getaffinity(0)),
                              loadavg=Path('/proc/loadavg').read_text(), meminfo=Path('/proc/meminfo').read_text()))
            try:
                common.command(['/downloads/patataWJY/.local/bin/codex', 'sandbox', '--permission-profile', 'agent_eval',
                     '--cd', workspace, '--', sys.executable, Path(__file__).with_name('benchllm_native.py'), mode,
                     '--plan', root / 'versions' / (version + '-plan.json')], env=env,
                     log=root / 'versions' / (version + '-' + mode + '.log'), timeout=limit)
                record[mode] = 'passed'
                if mode == 'benchmark':
                    reports = sorted(workspace.glob('.benchllm-results/benchmark-*/result.json'))
                    report = json.loads(reports[-1].read_text())
                    result_file = Path(report['result'])
                    rows[version] = json.loads(result_file.read_text())
                    shutil.copyfile(result_file, root / 'versions' / (version + '-jmh.json'))
            except Exception as exc:
                record[mode] = type(exc).__name__
                record[mode + '_error'] = str(exc)
            record['ended'] = common.now()
        for version in ('original', 'developer', 'agent'):
            record = dict(version=version, started=common.now())
            measure(record, 'verify', 600)
            summary.append(record)
            common.write(root / 'summary.json', summary)
        if all(record.get('verify') == 'passed' for record in summary):
            blocked = False
            for record in summary:
                if blocked:
                    record['benchmark'] = 'not_run_reference_measurement_failed'
                else:
                    measure(record, 'benchmark', 900)
                    blocked = record.get('benchmark') != 'passed'
                common.write(root / 'summary.json', summary)
        else:
            for record in summary:
                record['benchmark'] = 'not_run_three_version_test_gate'
            common.write(root / 'summary.json', summary)
        if len(rows) == 3:
            common.write(root / 'comparison.json', compare_rows(rows))
        common.write(root / 'completion.json', dict(ended=common.now(), versions_processed=len(summary),
                      complete_comparison=len(rows) == 3))
        (root / 'status.txt').write_text('complete; matched comparison available\n' if len(rows) == 3 else 'complete; partial/failed versions recorded\n')
    except Exception as exc:
        common.write(root / 'queue-error.json', dict(error_type=type(exc).__name__, error=str(exc), ended=common.now()))
        (root / 'error.log').write_text(traceback.format_exc())
        (root / 'status.txt').write_text('queue_failed\n')
        raise


if __name__ == '__main__':
    main()
