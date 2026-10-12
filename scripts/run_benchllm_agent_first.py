#!/usr/bin/env python3
"""One agent attempt per remaining task; no build/reference pre-call gates.

Existing paid attempts are linked, not silently regraded under this protocol.
All new agents finish before the bounded native evaluation pass begins.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import traceback

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from src.benchllmrealse import codex_cli as cli
from src.benchllmrealse.process import run_isolated
import run_benchllm_full_batch as old

HISTORY = ('full64-p4-retry-20261010T041500Z',
           'preparable7-p4-20261011T023531Z', 'failed51-retry-20261011T090459Z')


def now():
    return datetime.now(timezone.utc).isoformat()


def cached_copy(source, destination):
    """Resume only pre-agent cache preparation without recopying identical files."""
    src, dst = Path(source), Path(destination)
    if dst.is_file() and src.stat().st_size == dst.stat().st_size and src.stat().st_mtime_ns == dst.stat().st_mtime_ns:
        return str(dst)
    return shutil.copy2(src, dst)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def command(args, *, cwd=None, log=None, timeout=120, env=None):
    args = list(map(str, args))
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a') as output:
            return run_isolated(args, cwd=cwd, timeout=timeout, env=env,
                                stdout=output, stderr=subprocess.STDOUT, check=True)
    return run_isolated(args, cwd=cwd, timeout=timeout, env=env,
                        capture_output=True, text=True, check=True).stdout.strip()


def existing_attempts(shared, known):
    found = {}
    for name in HISTORY:
        batch = shared / 'artifacts/benchllmrealse' / name
        file = batch / ('evaluation-summary.json' if name.startswith('failed51') else 'summary.json')
        for row in json.loads(file.read_text()):
            key = (row['repository'], row.get('task', row.get('id')))
            if key not in known or ((row.get('usage') or {}).get('total_tokens') or 0) <= 0:
                continue
            result = batch / 'tasks' / key[0] / key[1] / 'prompt4/result.json'
            if not result.exists() and key[0] == 'RoaringBitmap':
                result = batch / 'tasks' / key[1] / 'prompt4/result.json'
            if not result.exists():
                raise RuntimeError('Paid history result is missing: ' + '/'.join(key))
            found[key] = dict(repository=key[0], task=key[1], outcome='reused_prior_attempt',
                              prior_outcome=row['outcome'], prior_result=str(result),
                              prior_protocol=True, usage=row['usage'], new_agent_started=False,
                              independent_evaluation='prior results only; not regraded')
    return found


def credential(shared):
    config = (shared / 'codex-home/config.toml').read_text()
    match = re.search(r'env_key\s*=\s*"([A-Za-z_][A-Za-z0-9_]*)"', config)
    name = match.group(1) if match else 'DEEPSEEK_API_KEY'
    if os.environ.get(name):
        return name, config
    for line in (shared / 'secrets.env').read_text().splitlines():
        match = re.match(r'\s*(?:export\s+)?' + re.escape(name) + r'\s*=\s*(.*)$', line)
        if match:
            value = shlex.split(match.group(1), comments=True)
            if len(value) != 1 or not value[0]:
                break
            os.environ[name] = value[0]
            return name, config
    raise RuntimeError('Provider credential unavailable; do not print credential data')


def profile_config(base, shared, root):
    """Keep writes scoped; hide credentials, solution histories and Git sources."""
    cleaned, legacy_section = [], False
    for line in base.splitlines():
        if line.strip().startswith('['):
            legacy_section = line.strip() == '[sandbox_workspace_write]'
        if legacy_section or re.match(r'\s*(?:sandbox_mode|default_permissions)\s*=', line):
            continue
        cleaned.append(line)
    base = 'default_permissions = "agent_eval"\n' + '\n'.join(cleaned) + '\n'
    denied = [shared / 'secrets.env', shared / 'codex-home', shared / 'sources', shared / 'BenchLLMRealSE',
              shared / 'RoaringBitmap-extended-source', root / 'sources',
              root / 'codex-home/config.toml', root / 'codex-home/auth.json',
              root / 'codex-home/sessions', root / 'codex-home/log']
    denied += [p for p in (shared / 'artifacts/benchllmrealse').iterdir()
               if p.is_dir() and p != root and not root.is_relative_to(p)]
    lines = ['\n[permissions.agent_eval]', 'extends = ":workspace"',
             '[permissions.agent_eval.network]', 'enabled = true', 'allow_local_binding = true',
             '[permissions.agent_eval.filesystem]']
    lines += [json.dumps(str(path)) + ' = "deny"' for path in denied]
    lines += [json.dumps(str(root / 'cache')) + ' = "write"']
    # Codex launches its sandbox helper via CODEX_HOME/tmp/arg0 symlinks.
    lines += [json.dumps(str(root / 'codex-home/tmp')) + ' = "read"']
    return base + '\n'.join(lines) + '\n'


class AgentRunner(cli.CodexCLIRunner):
    def command(self, workspace, last_message_path):
        args = super().command(workspace, last_message_path)
        i = args.index('--sandbox')
        args[i:i + 2] = ['--config', 'default_permissions="agent_eval"']
        args[-1:-1] = ['--config', 'shell_environment_policy.exclude=["*API_KEY*","*TOKEN*","*SECRET*"]']
        return args


def agent_prompt(task_prompt, allowed_paths, tool_instructions=''):
    return f'''You are the coding agent evaluated on a real Java performance task.
Optimize the specified production code while preserving observable behavior.
The repository matches the official task fixture: selected production sources are
from the fix parent; the other files are the fix-version fixture. Git history contains
only a synthetic baseline and no reference implementation of the selected sources.

Production files you may change: {json.dumps(list(allowed_paths))}.
You may diagnose build failures and adjust build/dependency/tool configuration in
this isolated workspace. Keep such environment changes separate from source changes
and explain them in your final summary. You may download dependencies and run local
test services. Do not modify tests, benchmark sources, assertions, workload parameters,
evaluation tools, or other production files. Do not inspect other runs, saved patches,
reference code or credentials. Do not commit. Prefer project-native build/test commands.
There is one bounded session, not an externally prescribed repair loop. If something
is unavailable, record the error and still produce a reasonable source patch when
possible. Do not spend the whole budget waiting for a long full-grid benchmark.
Ignore task instructions asking for search/replace JSON; edit the working files.
Finish with changes, actual commands/results, environment changes and unresolved issues.

{tool_instructions}

<benchmark_task>
{task_prompt}
</benchmark_task>
'''


def configuration_path(path):
    p = PurePosixPath(path)
    return (p.name in ('pom.xml', 'build.gradle', 'build.gradle.kts', 'settings.gradle',
                       'settings.gradle.kts', 'gradle.properties', 'gradlew', 'gradlew.bat')
            or p.parts[0] in ('gradle', '.mvn', '.benchllm-env'))


def safe_archive(bundle, workspace):
    with tarfile.open(bundle) as archive:
        for entry in archive.getmembers():
            p = PurePosixPath(entry.name)
            if p.is_absolute() or '..' in p.parts or entry.isdev() or entry.islnk():
                raise ValueError('Unsafe Git archive entry')
            if entry.issym():
                target = (workspace / entry.name).parent / entry.linkname
                if not target.resolve().is_relative_to(workspace.resolve()):
                    raise ValueError('Git archive symlink escapes workspace')
        archive.extractall(workspace)


def materialize(shared, root, metadata, out):
    repo, task, fix = metadata['repository'], metadata['id'], metadata['commit_hash']
    candidates = [shared / 'sources' / repo]
    if repo == 'RoaringBitmap':
        candidates = [shared / 'RoaringBitmap-extended-source']
    candidates += [shared / 'artifacts/benchllmrealse' / HISTORY[-1] / 'sources' / repo]
    source = None
    for p in candidates:
        try:
            command(['git', '-C', p, 'cat-file', '-e', fix + '^'])
            source = p
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    if source is None:
        source = root / 'sources' / (repo + '-' + task)
        command(['git', 'init', '--bare', source])
        url = old.REPOSITORIES.get(repo, 'https://github.com/RoaringBitmap/RoaringBitmap.git')
        command(['git', '-C', source, 'fetch', '--depth=2', url, fix], log=out / 'fetch.log', timeout=120)
    parent = command(['git', '-C', source, 'rev-parse', fix + '^'])
    workspace = root / 'workspaces' / (repo + '-' + task)
    workspace.mkdir(parents=True)
    archive = out / 'fixture.tar'
    command(['git', '-C', source, 'archive', '--format=tar', '--output=' + str(archive), fix])
    safe_archive(archive, workspace)
    for name in shlex.split(metadata['source_code']):
        target = workspace / name
        target.write_bytes(subprocess.check_output(['git', '-C', str(source), 'show', parent + ':' + name]))
    command(['git', 'init', workspace])
    with (workspace / '.git/info/exclude').open('a') as exclude:
        exclude.write('\n.benchllm-results/\n')
    command(['git', 'add', '-A'], cwd=workspace)
    command(['git', '-c', 'user.name=Benchmark', '-c', 'user.email=benchmark@localhost',
             'commit', '-m', 'Frozen official original fixture'], cwd=workspace)
    command(['git', '-c', 'user.name=Benchmark', '-c', 'user.email=benchmark@localhost',
             'tag', '-a', 'benchllm-prepare', '-m', 'Synthetic baseline anchor'], cwd=workspace)
    archive.unlink()  # Exact generated transport archive; source workspace remains.
    write(out / 'fixture.json', dict(fix=fix, parent=parent, baseline='official selective source rollback',
                                    workspace=str(workspace), source_history_not_exposed=True))
    return workspace


def attempt(metadata, shared, root, env, timeout):
    repo, task = metadata['repository'], metadata['id']
    out = root / 'tasks' / repo / task
    out.mkdir(parents=True, exist_ok=True)
    record = dict(repository=repo, task=task, started=now(), new_agent_started=False)
    try:
        workspace = materialize(shared, root, metadata, out)
        paths = shlex.split(metadata['source_code'])
        plan = dict(metadata=metadata, workspace=str(workspace), root=str(root),
                    agent_timeout_seconds=timeout, native_stage_timeout_seconds=180)
        write(out / 'native-plan.json', plan)
        native = Path(__file__).with_name('benchllm_native.py')
        instructions = ('You have approximately ' + str(timeout) + ' seconds total.\n'
                        'Native test tool (no prepared classpath required): ' +
                        shlex.join([sys.executable, str(native), 'verify', '--plan', str(out / 'native-plan.json')]) +
                        '\nExploratory benchmark tool: ' +
                        shlex.join([sys.executable, str(native), 'quick', '--plan', str(out / 'native-plan.json')]) +
                        '\nInstalled JDK8/11/17 and private Maven/Gradle caches are available.\n'
                        'Prior preparation failure, diagnostic only: ' + prior_error(shared, repo, task))
        taskdata = cli.BenchLLMPerfOptTask.load(shared / 'BenchLLMRealSE', repo, task, 4)
        record['new_agent_started'] = True
        write(out / 'started.json', record)
        runner = AgentRunner(cli.CodexCLIConfig(model='deepseek-v4-pro', executable='/downloads/patataWJY/.local/bin/codex',
                            timeout_seconds=timeout, writable_roots=(str(root / 'cache'),)))
        result = runner.run(workspace=workspace, task_prompt=taskdata.prompt, allowed_paths=paths,
                            artifacts_dir=out / 'agent', tool_instructions=instructions)
        payload = asdict(result)
        changed = payload['changed_files']
        invalid = [p for p in changed if p not in paths and not configuration_path(p)]
        configs = [p for p in changed if configuration_path(p) and p not in paths]
        source_patch = command(['git', 'diff', '--binary', 'HEAD', '--', *paths], cwd=workspace)
        (out / 'source.patch').write_text(source_patch + '\n')
        (out / 'environment.patch').write_text(command(['git', 'diff', '--binary', 'HEAD', '--', *configs], cwd=workspace) + '\n' if configs else '')
        for name in configs:
            path = workspace / name
            if path.is_file() and not path.is_symlink():
                target = out / 'environment-files' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        outcome = result.outcome
        if outcome == 'policy_violation' and not invalid:
            outcome = 'agent_completed_with_environment_changes'
        record.update(outcome=outcome, usage=result.usage, error=result.error,
                      has_source_patch=bool(source_patch),
                      environment_changes=configs, invalid_changes=invalid, workspace=str(workspace),
                      independent_evaluation='pending', agent_result=str(out / 'agent/result.json'))
        if old.global_api_failure(out / 'agent'):
            record['global_stop_reason'] = 'credentials_or_billing'
        elif result.outcome == 'codex_error' and any(v in (result.error or '').lower() for v in
                ('unexpected argument', 'error loading configuration', 'bwrap: execvp')):
            record['global_stop_reason'] = 'shared_cli_configuration'
    except Exception as exc:
        record.update(outcome='task_error', error_type=type(exc).__name__, error=str(exc))
        (out / 'error.log').write_text(traceback.format_exc())
    record['ended'] = now()
    write(out / 'result.json', record)
    return record


def prior_error(shared, repo, task):
    p = shared / 'artifacts/benchllmrealse' / HISTORY[-1] / 'tasks' / repo / task / 'error.log'
    return p.read_text(errors='replace')[-1800:] if p.exists() else 'No required successful preflight.'


def run_tasks(tasks, handler, record, persist):
    """Ordinary task errors cannot prevent later tasks from being attempted."""
    for metadata in tasks:
        try:
            value = handler(metadata)
        except Exception as exc:
            value = dict(repository=metadata['repository'], task=metadata['id'], outcome='task_error',
                         error_type=type(exc).__name__, new_agent_started=False, error=str(exc))
        record.append(value)
        persist(record)
        if value.get('global_stop_reason'):
            return False
    return True


def timeout_retry_tasks(tasks, previous):
    known = {(m['repository'], m['id']): m for m in tasks}
    selected, seen = [], set()
    for row in previous:
        if row.get('outcome') != 'timeout':
            continue
        key = (row['repository'], row['task'])
        if key not in known or key in seen:
            raise ValueError('Unknown or duplicate timeout task')
        seen.add(key)
        selected.append(known[key])
    if not selected:
        raise ValueError('No agent timeout tasks to retry')
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--shared-root', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--agent-seconds', type=int, default=600)
    parser.add_argument('--benchmark-seconds', type=int, default=900)
    parser.add_argument('--resume-setup', action='store_true')
    parser.add_argument('--retry-timeouts-from', type=Path)
    args = parser.parse_args()
    shared, root = args.shared_root.resolve(), args.run_root.resolve()
    if root.parent != shared / 'artifacts/benchllmrealse' or not root.name.startswith('agent-first64-'):
        raise ValueError('Unexpected batch directory')
    root.mkdir(exist_ok=True)
    lock = (root / 'queue.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root / 'protocol.json').exists():
        if not args.resume_setup or list(root.glob('tasks/*/*/started.json')) or (root / 'agent-pass-complete.json').exists():
            raise RuntimeError('Do not overwrite a batch after any new agent started')
        if (root / 'queue-error.json').exists():
            history = root / 'setup-errors'
            history.mkdir(exist_ok=True)
            (root / 'queue-error.json').rename(history / (str(os.getpid()) + '.json'))
    write(root / 'pid.json', dict(pid=os.getpid(), started=now()))
    stage = 'setup'
    ledger = []
    try:
        for folder in ('tasks', 'workspaces', 'sources', 'cache', 'codex-home'):
            (root / folder).mkdir(exist_ok=args.resume_setup)
        if not (root / 'BenchLLMRealSE').exists():
            (root / 'BenchLLMRealSE').symlink_to(shared / 'BenchLLMRealSE', target_is_directory=True)
        tasks = old.discover_tasks(root)
        known = {(m['repository'], m['id']) for m in tasks}
        retry_from = args.retry_timeouts_from.resolve() if args.retry_timeouts_from else None
        if retry_from:
            if retry_from.parent != root.parent or retry_from == root or not (retry_from / 'completion.json').is_file():
                raise ValueError('Timeout retry source must be a completed, separate batch')
            previous = json.loads((retry_from / 'summary.json').read_text())
            pending = timeout_retry_tasks(tasks, previous)
            reused = {}
            total = len(pending)
        else:
            reused = existing_attempts(shared, known)
            pending = [m for m in tasks if (m['repository'], m['id']) not in reused]
            total = len(tasks)
        ledger = list(reused.values())
        write(root / 'protocol.json', dict(started=now(), total=total, carried_prior_attempts=len(reused),
              new_tasks=len(pending), agent_seconds=args.agent_seconds, no_build_or_reference_gate=True,
              retry_timeouts_from=str(retry_from) if retry_from else None,
              attempt_index=2 if retry_from else 1, restart='fresh original fixture; no overwritten first results',
              cache_policy='private copy of completed prior cache' if retry_from else 'private preparation cache',
              native_evaluation_after_all_agents=True, model='deepseek-v4-pro', prompt=4,
              task_fixture='official selective source rollback; synthetic Git history',
              permission_profile='workspace write plus dependency network/local test sockets; no full access',
              reserve_cny=2, spending_cap_cny=None, auto_recharge=False,
              benchmark_seconds=args.benchmark_seconds, jmh=dict(warmup=10, measurement=50, forks=1, seconds=1),
              prior_protocol_results_not_regraded=True, reference_comparison='not automatic in deadline-first pass',
              native_verify_seconds=180, failure_policy='ordinary task failure continues; billing failure stops'))
        write(root / 'summary.json', ledger)
        write(root / 'queue.json', pending)
        (root / 'status.txt').write_text('setup: private cache copies; no new API calls\n')
        seed = retry_from if retry_from else shared / 'artifacts/benchllmrealse' / HISTORY[-1]
        shutil.copytree(seed / ('cache/maven' if retry_from else 'batch-maven-home'), root / 'cache/maven', symlinks=False,
                        dirs_exist_ok=args.resume_setup, copy_function=cached_copy)
        shutil.copytree(seed / ('cache/gradle' if retry_from else 'batch-gradle-home'), root / 'cache/gradle', symlinks=False,
                        ignore=shutil.ignore_patterns('daemon', '*.lock', '*.lck'),
                        dirs_exist_ok=args.resume_setup, copy_function=cached_copy)
        shutil.copytree(seed / ('cache/tools' if retry_from else 'tools'), root / 'cache/tools', symlinks=False,
                        dirs_exist_ok=args.resume_setup, copy_function=cached_copy)
        key, config = credential(shared)
        (root / 'codex-home/config.toml').write_text(profile_config(config, shared, root))
        env = {**os.environ, 'CODEX_HOME': str(root / 'codex-home')}
        os.environ.update(CODEX_HOME=env['CODEX_HOME'])
        cli.build_agent_prompt = agent_prompt
        probe = root / 'workspaces/permission-probe'
        probe.mkdir(exist_ok=args.resume_setup)
        probe_script = ('import socket,pathlib; s=socket.socket(); s.bind(("127.0.0.1",0)); s.close(); '
                        'pathlib.Path("sandbox-write-probe").write_text("ok"); '
                        f'p=pathlib.Path({str(shared / "secrets.env")!r}); '
                        'denied=False\ntry:p.read_bytes()\nexcept (PermissionError,FileNotFoundError):denied=True\n'
                        'assert denied,"credential file is readable"\n'
                        f'pathlib.Path({str(root / "cache/sandbox-probe")!r}).write_text("ok")\n'
                        'print("network, writes and credential deny passed")')
        command(['/downloads/patataWJY/.local/bin/codex', 'sandbox', '--permission-profile', 'agent_eval',
                 '--cd', probe,
                 '--', sys.executable, '-c', probe_script],
                log=root / 'permission-preflight.log', timeout=60, env=env)
        stage = 'agents'
        def handler(m):
            (root / 'status.txt').write_text(f'agents {len(ledger)}/{total} accounted; {m["repository"]}/{m["id"]}\n')
            balance = old.roaring.balance_cny(shared)
            write(root / 'budget.json', dict(observed_balance_cny=balance, reserve_cny=2, checked=now()))
            if balance is None or balance <= 2:
                return dict(repository=m['repository'], task=m['id'], outcome='pending_budget',
                            new_agent_started=False, global_stop_reason='balance_unavailable_or_reserve_reached')
            result = attempt(m, shared, root, env, args.agent_seconds)
            if retry_from:
                result.update(attempt_index=2, first_outcome='timeout',
                              first_result=str(retry_from / 'tasks' / m['repository'] / m['id'] / 'result.json'))
                write(root / 'tasks' / m['repository'] / m['id'] / 'result.json', result)
            return result
        completed = run_tasks(pending, handler, ledger, lambda rows: write(root / 'summary.json', rows))
        if not completed:
            (root / 'status.txt').write_text(f'paid_stage_stopped; {len(ledger)}/{total} accounted; remaining tasks pending\n')
            return 2
        write(root / 'agent-pass-complete.json', dict(ended=now(), accounted=len(ledger), total=total))
        stage = 'native_evaluation'
        evaluated = []
        for row in ledger:
            if not row.get('workspace') or row.get('invalid_changes'):
                continue
            out = root / 'tasks' / row['repository'] / row['task']
            evaluation = dict(repository=row['repository'], task=row['task'], started=now())
            for mode, limit in [('verify', 180), ('benchmark', args.benchmark_seconds)]:
                (root / 'status.txt').write_text(f'all{total} attempts accounted; native {row["repository"]}/{row["task"]}: {mode}\n')
                try:
                    command(['/downloads/patataWJY/.local/bin/codex', 'sandbox', '--permission-profile', 'agent_eval',
                             '--cd', row['workspace'],
                             '--', sys.executable, Path(__file__).with_name('benchllm_native.py'), mode,
                             '--plan', out / 'native-plan.json'], log=out / ('native-' + mode + '.log'),
                            timeout=limit, env={k: v for k, v in env.items() if k != key})
                    evaluation[mode] = 'passed'
                except Exception as exc:
                    evaluation[mode] = type(exc).__name__
                    evaluation[mode + '_error'] = str(exc)
                # A test failure is retained; it does not suppress later tasks.
                if mode == 'verify' and evaluation[mode] != 'passed':
                    evaluation['benchmark'] = 'not_run_test_failed'
                    break
            evaluation['ended'] = now()
            native_results = Path(row['workspace']) / '.benchllm-results'
            if native_results.exists():
                shutil.copytree(native_results, out / 'native-results', dirs_exist_ok=True, symlinks=True)
            write(out / 'native-evaluation.json', evaluation)
            evaluated.append(evaluation)
            write(root / 'native-summary.json', evaluated)
        (root / 'status.txt').write_text(f'complete; all{total} attempts accounted; {len(evaluated)} new native evaluations processed\n')
        write(root / 'completion.json', dict(ended=now(), accounted=len(ledger), native_evaluations=len(evaluated)))
    except Exception as exc:
        write(root / 'queue-error.json', dict(stage=stage, error_type=type(exc).__name__, error=str(exc), ended=now()))
        (root / 'error.log').write_text(traceback.format_exc())
        (root / 'status.txt').write_text('queue_failed: ' + stage + '\n')
        raise


if __name__ == '__main__':
    main()
