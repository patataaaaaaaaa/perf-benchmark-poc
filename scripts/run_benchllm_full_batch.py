#!/usr/bin/env python3
"""All PerfOpt tasks, one P4 agent each, serial and failure isolated."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import traceback
import urllib.request
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from src.benchllmrealse.process import run_isolated
import run_roaringbitmap_batch as roaring
from benchllm_project_tools import result_keys

REPOSITORIES = {'netty': 'https://github.com/netty/netty.git',
                'kafka': 'https://github.com/apache/kafka.git',
                'presto': 'https://github.com/prestodb/presto.git'}


def run(command, *, cwd=None, log=None, timeout=1800, env=None):
    command = [str(p) for p in command]
    print('RUN', shlex.join(command), flush=True)
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        with Path(log).open('w') as output:
            return run_isolated(command, cwd=cwd, stdout=output,
                                stderr=subprocess.STDOUT, timeout=timeout, check=True, env=env)
    return run_isolated(command, cwd=cwd, timeout=timeout, check=True, env=env)


roaring.run = run
git = roaring.git
clone_at = roaring.clone_at


def write_json(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def experiment_codex_env(root):
    """Scope configuration to this experiment; never edit the user's default home."""
    config = root / 'codex-home/config.toml'
    if not config.is_file():
        raise RuntimeError('Experiment Codex config is missing')
    return {**os.environ, 'CODEX_HOME': str(config.parent)}


def prepare_cached(root, batch, metadata, previous):
    """Reuse frozen build products, but create a new parent-only source checkout."""
    repo, task = metadata['repository'], metadata['id']
    relative = Path(task) if repo == 'RoaringBitmap' else Path(repo) / task
    existing = previous / 'support' / relative
    manifest_path = existing / 'manifest.json'
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text())
    if manifest['fix'] != metadata['commit_hash'] or manifest['task'] != task:
        raise RuntimeError('Cached build products use different task metadata')
    runtime = manifest['runtime_classpath']
    if not runtime or any(not Path(p).exists() for p in runtime):
        return None
    if repo == 'RoaringBitmap' and not (existing / 'harness.jar').is_file():
        return None
    support = batch / 'support' / relative
    support.mkdir(parents=True, exist_ok=True)
    for name in ('manifest.json', 'harness.jar', 'gradle-classpaths.json', 'expected-jmh-keys.json'):
        if (existing / name).is_file():
            shutil.copyfile(existing / name, support / name)
    write_json(support / 'reuse.json', dict(source=str(existing), fresh_agent_workspace=True))
    source = ensure_source(root, metadata, support)
    workspace = batch / 'workspaces' / (repo + '-' + task + '-original')
    clone_at(source, manifest['parent'], workspace)
    return source, workspace, support, manifest


def select_tasks(tasks, only):
    requested = []
    for item in only.split(','):
        item = item.strip()
        if not item:
            continue
        if item.count('/') != 1:
            raise ValueError('Task filter must be repository/id')
        requested.append(tuple(item.split('/', 1)))
    known = {(item['repository'], item['id']): item for item in tasks}
    missing = [f'{repo}/{task}' for repo, task in requested if (repo, task) not in known]
    if missing:
        raise RuntimeError('Unknown tasks: ' + ', '.join(missing))
    if len(requested) != len(set(requested)):
        raise RuntimeError('Duplicate task filter')
    return [known[key] for key in requested]


def discover_tasks(root):
    folders = root / 'BenchLLMRealSE/Dataset/PerfOpt'
    groups = {repo: [json.loads(p.read_text()) for p in sorted((folders / repo).glob('*.json'))]
              for repo in ('RoaringBitmap', 'netty', 'kafka', 'presto')}
    # Previously validated adapter first, then interleave the three new projects.
    ordered = list(groups['RoaringBitmap'])
    for i in range(max(len(groups[r]) for r in REPOSITORIES)):
        for repo in REPOSITORIES:
            if i < len(groups[repo]):
                ordered.append(groups[repo][i])
    keys = [(d['repository'], d['id']) for d in ordered]
    if len(keys) != len(set(keys)) or len(keys) != 64:
        raise RuntimeError(f'Expected 64 unique PerfOpt tasks; found {len(keys)}')
    for d in ordered:
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', d['id']):
            raise ValueError('Unsafe task identifier')
        for field in ('source_code', 'unittest', 'jmh_case'):
            for p in shlex.split(d[field]):
                if Path(p).is_absolute() or '..' in Path(p).parts:
                    raise ValueError('Unsafe dataset path')
        if not (root / 'BenchLLMRealSE/Prompts' / d['repository'] / d['id'] / 'prompt4.txt').is_file():
            raise RuntimeError('Missing P4 prompt')
    return ordered


def ensure_source(root, metadata, support):
    repo = metadata['repository']
    if repo == 'RoaringBitmap':
        return root / 'RoaringBitmap-extended-source'
    source = root / 'sources' / repo
    source.parent.mkdir(exist_ok=True)
    if not source.exists():
        run(['git', 'init', '--bare', source])
    fix = metadata['commit_hash']
    try:
        git(source, 'rev-parse', '--verify', fix + '^')
    except subprocess.CalledProcessError:
        fetch_parent(source, repo, fix, support / 'fetch.log')
    return source


def benchmark_path(case):
    base = case.rsplit('/', 1)[-1].split('.', 1)[0]
    return case.rsplit('/', 1)[0] + '/' + base + '.java'


def executable_tests(workspace, requested):
    selected = []
    expansion = []
    for relative in requested:
        path = workspace / relative
        if path.is_dir():
            candidates = sorted([*path.rglob('*.java'), *path.rglob('*.scala')])
        elif path.is_file() and re.search(r'@Test\b', path.read_text()):
            candidates = [path]
        else:
            # Some metadata names a helper (e.g. OrcTester), not a test class.
            # Use actual annotated Test* classes in that module, and record it.
            module = relative.split('/src/test/', 1)[0]
            candidates = sorted((workspace / module / 'src/test').rglob('*Test*.java'))
            expansion.append(relative)
        for candidate in candidates:
            text = candidate.read_text()
            if not re.search(r'@Test\b', text):
                continue
            package = re.search(r'^\s*package\s+([\w.]+)', text, re.M)
            if package:
                selected.append(package.group(1) + '.' + candidate.stem)
    return sorted(set(selected)), expansion


def fetch_parent(source, repo, fix, log, attempts=3):
    error = None
    for _ in range(attempts):
        try:
            run(['git', '-C', source, 'fetch', '--depth=2', REPOSITORIES[repo], fix],
                log=log, timeout=600)
            return
        except subprocess.CalledProcessError as exc:
            error = exc
    raise error


def gradle_version_from_project(wrapper_text, build_text):
    if wrapper_text:
        match = re.search(r'gradle-([0-9.]+)-(?:bin|all)', wrapper_text)
        if not match:
            raise RuntimeError('Unrecognized Gradle wrapper')
        return match.group(1)
    match = re.search(r'''gradleVersion\s*=\s*['"]([0-9.]+)['"]''', build_text or '')
    if not match:
        raise RuntimeError('Gradle version not declared')
    return match.group(1)


def archive_is_complete(path):
    try:
        with zipfile.ZipFile(path) as bundle:
            return any(not info.is_dir() for info in bundle.infolist())
    except (OSError, zipfile.BadZipFile):
        return False


def download_verified_archive(url, archive, attempts=3, opener=None):
    """Resume a distribution download and keep it only when it is a real zip."""
    opener = opener or urllib.request.urlopen
    archive.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(attempts):
        if archive.is_file() and archive_is_complete(archive):
            return archive
        existing = archive.stat().st_size if archive.is_file() else 0
        if existing and archive.read_bytes()[:2] != b'PK':
            archive.unlink()
            existing = 0
        headers = {'Range': 'bytes=%d-' % existing} if existing else {}
        request = urllib.request.Request(url, headers=headers)
        try:
            with opener(request, timeout=60) as response:
                status = getattr(response, 'status', 200)
                with archive.open('ab' if status == 206 and existing else 'wb') as output:
                    shutil.copyfileobj(response, output)
        except Exception:
            if attempt + 1 == attempts and not (archive.is_file() and archive_is_complete(archive)):
                raise
            continue
        if archive_is_complete(archive):
            return archive
    raise RuntimeError('Incomplete Gradle archive ' + archive.name)


def gradle_distribution(root, version, opener=None):
    target = root / 'tools' / ('gradle-' + version)
    binary = target / 'bin/gradle'
    if not binary.is_file():
        archive = root / 'tools' / ('gradle-' + version + '-bin.zip')
        download_verified_archive('https://services.gradle.org/distributions/' + archive.name,
                                  archive, opener=opener)
        with zipfile.ZipFile(archive) as bundle:
            for info in bundle.infolist():
                if Path(info.filename).is_absolute() or '..' in Path(info.filename).parts:
                    raise RuntimeError('Unsafe Gradle archive')
            bundle.extractall(root / 'tools')
        binary.chmod(0o755)
    return binary


def maven_prepare_flags(root):
    return ['mvn', '-B', '-Dmaven.repo.local=' + str(root / 'batch-maven-home'),
            '-DskipTests', '-Dcheckstyle.skip=true', '-Dlicense.skip=true',
            '-Dair.check.skip-all=true', '-Denforcer.skip=true', '-DskipJapicmp=true',
            '-Dxml.skip=true', '-DskipFormat=true', '-Dfindbugs.skip=true',
            '-Dmaven.compiler.source=8', '-Dmaven.compiler.target=8']


def history_plugin_present(workspace, modules):
    candidates = [workspace / 'pom.xml', *(workspace / module / 'pom.xml' for module in modules)]
    return any(path.is_file() and 'git-commit-id-plugin' in path.read_text(errors='replace')
               for path in candidates)


def unrelated_test_excludes(log_text, requested):
    """Exclude unrelated broken tests. A failure in a requested test is not excluded."""
    failed = re.findall(r'([^\s:]+\.java):\[\d+,\d+\] error:', log_text)
    requested_names = {Path(path).name for path in requested}
    excludes = []
    for absolute in failed:
        normalized = absolute.replace('\\', '/')
        if '/src/test/' not in normalized:
            return None
        name = Path(normalized).name
        if name in requested_names:
            return None
        excludes.append('**/' + name)
    return sorted(set(excludes)) or None


def pom_with_unrelated_test_excludes(pom_text, patterns):
    excludes = '\n'.join('            <testExclude>%s</testExclude>' % pattern for pattern in patterns)
    profile = (
        '<profile><id>benchllm-exclude-unrelated-tests</id>'
        '<activation><property><name>benchllm.excludeTests</name></property></activation>'
        '<build><plugins><plugin><groupId>org.apache.maven.plugins</groupId>'
        '<artifactId>maven-compiler-plugin</artifactId><configuration><testExcludes>\n'
        + excludes +
        '\n          </testExcludes></configuration></plugin></plugins></build></profile>'
    )
    if '<profiles>' in pom_text:
        return pom_text.replace('<profiles>', '<profiles>' + profile, 1)
    head, separator, tail = pom_text.rpartition('</project>')
    if not separator:
        raise RuntimeError('Maven POM has no project end')
    return head + '<profiles>' + profile + '</profiles>\n' + separator + tail


def prepare_project(root, batch, metadata):
    repo, task = metadata['repository'], metadata['id']
    support = batch / 'support' / repo / task
    support.mkdir(parents=True, exist_ok=True)
    source = ensure_source(root, metadata, support)
    fix = metadata['commit_hash']
    parent = git(source, 'rev-parse', fix + '^')
    workspace = batch / 'workspaces' / (repo + '-' + task + '-original')
    clone_at(source, parent, workspace)
    source_paths = shlex.split(metadata['source_code'])
    test_paths = shlex.split(metadata['unittest'])
    for p in source_paths:
        if not (workspace / p).is_file():
            raise RuntimeError('Source absent at parent: ' + p)
    bpath = benchmark_path(metadata['jmh_case'])
    bmodule = bpath.split('/src/', 1)[0]
    modules = sorted({p.split('/src/', 1)[0] for p in source_paths + test_paths} | {bmodule})
    env = dict(os.environ)
    changes = {}

    def temporary_file(path, data):
        path = workspace / path
        # A later prepare adjustment must not forget the first original bytes.
        if path not in changes:
            changes[path] = path.read_bytes() if path.exists() else None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    # Added benchmark/test sources are preparation fixtures, not Agent edits.
    for p in [bpath, *test_paths]:
        if not (workspace / p).exists():
            temporary_file(p, subprocess.check_output(['git', '-C', str(source), 'show', fix + ':' + p]))
    try:
        if repo == 'kafka':
            wrapper_path = workspace / 'gradle/wrapper/gradle-wrapper.properties'
            wrapper_text = wrapper_path.read_text() if wrapper_path.is_file() else ''
            build_text = (workspace / 'build.gradle').read_text() if not wrapper_text else ''
            version = gradle_version_from_project(wrapper_text, build_text)
            parts = tuple(int(v) for v in version.split('.')[:2])
            jdk = '8' if parts[0] <= 4 else ('17' if parts >= (7, 3) else '11')
            env['JAVA_HOME'] = '/usr/lib/jvm/java-' + jdk + '-openjdk-amd64'
            env['PATH'] = env['JAVA_HOME'] + '/bin:' + env['PATH']
            gradle = gradle_distribution(root, version)
            dependencies = workspace / 'gradle/dependencies.gradle'
            if dependencies.exists():
                original = dependencies.read_text()
                updated = re.sub(r'(grgit:\s*")[0-9.]+"', r'\g<1>4.1.1"', original)
                if updated != original:
                    temporary_file('gradle/dependencies.gradle', updated.encode())
            selected = [':' + m.replace('/', ':') for m in modules]
            cp_file = support / 'gradle-classpaths.json'
            command = [gradle, '--no-daemon', '--max-workers=2', '-g', root / 'batch-gradle-home',
                       '--init-script', PROJECT / 'scripts/benchllm_full_classpath.gradle',
                       '-Dbenchllm.modules=' + ','.join(selected),
                       '-Dbenchllm.classpath.output=' + str(cp_file),
                       *[m + ':testClasses' for m in selected]]
            run(command, cwd=workspace, log=support / 'prepare.log', timeout=1800, env=env)
            runtime = sorted({p for paths in json.loads(cp_file.read_text()).values() for p in paths})
            # JMH uses runtime classes generated by its annotation processor.
            release = '17' if jdk == '17' else '8'
        else:
            env['JAVA_HOME'] = '/usr/lib/jvm/java-8-openjdk-amd64'
            env['PATH'] = env['JAVA_HOME'] + '/bin:' + env['PATH']
            release = '8'
            if repo == 'netty':
                for p in workspace.rglob('pom.xml'):
                    text = p.read_text()
                    replaced = text.replace('Final-SNAPSHOT', 'Final')
                    if replaced != text:
                        temporary_file(str(p.relative_to(workspace)), replaced.encode())
            common = maven_prepare_flags(root)
            if history_plugin_present(workspace, modules):
                # Tag the parent itself so a shallow clone can satisfy git-describe
                # without fetching any descendant fix commit.
                git(workspace, '-c', 'user.email=benchllm@localhost', '-c', 'user.name=benchllm',
                    'tag', '-f', '-a', 'benchllm-prepare', '-m', 'prepare anchor', 'HEAD')
            try:
                run([*common, '-pl', ','.join(modules), '-am', 'install'], cwd=workspace,
                    log=support / 'prepare.log', timeout=1800, env=env)
            except subprocess.CalledProcessError:
                excludes = unrelated_test_excludes((support / 'prepare.log').read_text(errors='replace'),
                                                   test_paths)
                if not excludes:
                    raise
                temporary_file('pom.xml', pom_with_unrelated_test_excludes(
                    (workspace / 'pom.xml').read_text(), excludes).encode())
                run([*common, '-Dbenchllm.excludeTests=true', '-pl', ','.join(modules), '-am', 'install'],
                    cwd=workspace, log=support / 'prepare-retry.log', timeout=1800, env=env)
            runtime = []
            for module in modules:
                cp_file = support / ('classpath-' + module.replace('/', '_') + '.txt')
                run([*common, '-pl', module, 'dependency:build-classpath', '-DincludeScope=test',
                     '-Dmdep.outputFile=' + str(cp_file)], cwd=workspace,
                    log=support / ('classpath-' + module.replace('/', '_') + '.log'), timeout=300, env=env)
                runtime.extend(cp_file.read_text().strip().split(os.pathsep))
            class_dirs = sorted([p for p in workspace.rglob('*') if p.is_dir() and p.name in
                                 ('classes', 'test-classes') and p.parent.name == 'target'])
            runtime = [str(p) for p in class_dirs] + runtime
        tests, expansion = executable_tests(workspace, test_paths)
        console = batch / 'junit-platform-console-standalone-1.9.3.jar'
        runtime = [str(console), *dict.fromkeys(p for p in runtime if p and Path(p).exists())]
        case = metadata['jmh_case'].rsplit('/', 1)[-1]
        manifest = dict(task=task, repository=repo, parent=parent, fix=fix, source_paths=source_paths,
                        java_home=env['JAVA_HOME'], java_release=release, runtime_classpath=runtime,
                        test_classes=tests, test_metadata_expanded=expansion,
                        test_framework='testng' if repo == 'presto' else 'junit',
                        pattern=r'.*\.' + re.escape(case) + r'(?:\..*)?$',
                        metric_origin='official', original_checkout='entire fix parent',
                        preparation_fixture_paths=[str(p.relative_to(workspace)) for p in changes],
                        measurement_protocol=dict(warmup=5, measurement=10, forks=2, seconds=1))
        write_json(support / 'manifest.json', manifest)
        # Ensure this is a usable JMH harness before spending on an Agent.
        run([str(Path(env['JAVA_HOME']) / 'bin/java'), '-cp', os.pathsep.join(runtime),
             'org.openjdk.jmh.Main', manifest['pattern'], '-l'],
            cwd=workspace, log=support / 'jmh-list.log', timeout=60)
        listed = (support / 'jmh-list.log').read_text().splitlines()
        if not any(re.search(manifest['pattern'], line.strip()) for line in listed if not line.startswith('Benchmarks:')):
            raise RuntimeError('Official JMH target is not registered in prepared harness')
    finally:
        for p, data in changes.items():
            if data is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(data)
    if git(workspace, 'status', '--porcelain'):
        raise RuntimeError('Preparation left changes in isolated original checkout')
    return source, workspace, support, manifest


def tool(repo, mode, support, workspace, output=None):
    if repo == 'RoaringBitmap':
        return roaring.tool(mode, support, workspace, output)
    command = [sys.executable, str(PROJECT / 'scripts/benchllm_project_tools.py'), mode,
               '--support', str(support), '--workspace', str(workspace)]
    if output:
        command += ['--output', str(output)]
    return command


def evaluate(repo, support, workspace, output, label):
    output.mkdir(parents=True, exist_ok=True)
    record = dict(code_version=label)
    stage = 'verification'
    try:
        run(tool(repo, 'verify', support, workspace), log=output / 'verification.log', timeout=600)
        stage = 'benchmark'
        run(tool(repo, 'benchmark', support, workspace, output), log=output / 'benchmark.log', timeout=1800)
        record['outcome'] = 'succeeded'
        if repo != 'RoaringBitmap' and label == 'original':
            write_json(support / 'expected-jmh-keys.json', result_keys(json.loads((output / 'jmh.json').read_text())))
    except Exception as exc:
        record.update(outcome='reference_evaluation_failed', failed_stage=stage,
                      error_type=type(exc).__name__, error=str(exc))
    write_json(output / 'result.json', record)
    return record


def prepare_unpaid_failures(root, batch, tasks, previous_summary, codex, codex_env):
    """Prepare tasks that failed before any Agent call. This never starts a model."""
    previous = json.loads(Path(previous_summary).read_text())
    failed = [(item['repository'], item['task']) for item in previous if item.get('outcome') != 'succeeded']
    known = {(item['repository'], item['id']): item for item in tasks}
    missing = [key for key in failed if key not in known]
    if missing:
        raise RuntimeError('Previous failures are not in the current dataset')
    batch.mkdir(parents=True, exist_ok=True)
    write_json(batch / 'protocol.json', dict(
        mode='unpaid_prepare', paid_agent_calls=False, task_count=len(failed),
        source_summary=str(previous_summary),
        started=datetime.now(timezone.utc).isoformat()))
    summary_path = batch / 'summary.json'
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else []
    done = {(item['repository'], item['task']) for item in summary}
    for key in failed:
        if key in done:
            continue
        metadata = known[key]
        repo, task = key
        output = batch / 'tasks' / repo / task
        output.mkdir(parents=True, exist_ok=True)
        (batch / 'status.txt').write_text(
            f'{len(summary)}/{len(failed)} unpaid prepare; {repo}/{task}\n')
        record = dict(repository=repo, task=task, agent_started=False, paid=False,
                      stage='prepare', started=datetime.now(timezone.utc).isoformat())
        try:
            _, workspace, support, _ = prepare_project(root, batch, metadata)
            record['stage'] = 'sandbox_verify'
            run([codex, 'sandbox', '--permission-profile', ':workspace', '--cd', workspace,
                 '--', *tool(repo, 'verify', support, workspace)],
                log=support / 'sandbox-verify.log', timeout=600, env=codex_env)
            record['outcome'] = 'preparable'
        except Exception as exc:
            record.update(outcome='infrastructure_failed', failed_stage=record['stage'],
                          error_type=type(exc).__name__, error=str(exc))
            (output / 'infrastructure-error.log').write_text(traceback.format_exc())
        record['ended'] = datetime.now(timezone.utc).isoformat()
        write_json(output / 'prepare-result.json', record)
        summary.append(record)
        write_json(summary_path, summary)
    preparable = sum(item.get('outcome') == 'preparable' for item in summary)
    (batch / 'status.txt').write_text(
        f'prepare_complete; {preparable}/{len(failed)} preparable; {len(summary)} checked\n')
    return 0


def global_api_failure(output):
    # Only service-wide credential/billing errors stop later tasks.
    content = ''
    for name in ('codex_stderr.log', 'codex_events.jsonl', 'result.json'):
        p = output / name
        if p.exists():
            content += p.read_text(errors='replace')[-100000:]
    return bool(re.search(r'insufficient[_ ](?:balance|quota)|invalid[_ ]api[_ ]key|'
                          r'authentication_error|account.*(?:disabled|suspended)|'
                          r'HTTP (?:401|402)\b', content, re.I))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--eval-root', type=Path, required=True)
    parser.add_argument('--batch-dir', type=Path, required=True)
    parser.add_argument('--reserve-cny', type=float, default=2)
    parser.add_argument('--agent-timeout-seconds', type=int, default=900)
    parser.add_argument('--prepare-task', help='Unpaid adapter smoke test: repository/id')
    parser.add_argument('--prepare-failed-summary', type=Path,
                        help='Unpaid preparation for previous non-successes. Never starts an Agent.')
    parser.add_argument('--reuse-prepared-batch', type=Path,
                        help='Reuse immutable successful builds, never previous Agent patches/results')
    parser.add_argument('--only-tasks',
                        help='Comma-separated repository/id list. Runs only these paid tasks.')
    args = parser.parse_args()
    root, batch = args.eval_root.resolve(), args.batch_dir.resolve()
    batch.mkdir(parents=True, exist_ok=True)
    lock = (batch / 'queue.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for directory in ('workspaces', 'support', 'tasks'):
        (batch / directory).mkdir(exist_ok=True)
    shutil.copyfile(root / 'junit-platform-console-standalone-1.9.3.jar',
                    batch / 'junit-platform-console-standalone-1.9.3.jar')
    tasks = discover_tasks(root)
    if args.only_tasks:
        tasks = select_tasks(tasks, args.only_tasks)
    task_count = len(tasks)
    # Confirm stable, previously exercised tasks first before cross-project preparation.
    priority = {'34bce1b': 0, '53ba593': 1, '1de6825': 2, 'abdd6ff': 3, 'b5b4af6': 4}
    tasks.sort(key=lambda d: priority.get(d['id'], 5))
    codex = '/downloads/patataWJY/.local/bin/codex'
    codex_env = experiment_codex_env(root)
    # Treat shared configuration faults as a batch failure, not 64 task failures.
    run([codex, 'sandbox', '--permission-profile', ':workspace', '--cd', PROJECT,
         '--', sys.executable, '-c', "print('experiment configuration preflight passed')"],
        env=codex_env, log=batch / 'startup-preflight.log', timeout=60)
    if args.prepare_failed_summary:
        return prepare_unpaid_failures(root, batch, tasks, args.prepare_failed_summary.resolve(),
                                       codex, codex_env)
    if args.prepare_task:
        metadata = next(d for d in tasks if d['repository'] + '/' + d['id'] == args.prepare_task)
        _, workspace, support, _ = prepare_project(root, batch, metadata)
        run(tool(metadata['repository'], 'verify', support, workspace),
            log=support / 'verification-smoke.log', timeout=600)
        return 0
    protocol_path = batch / 'protocol.json'
    if not protocol_path.exists():
        write_json(protocol_path, dict(task_count=task_count, tasks=[dict(repository=d['repository'], task=d['id']) for d in tasks],
                   prompt=4, model='deepseek-v4-pro', agent_timeout_seconds=args.agent_timeout_seconds,
                   outer_optimization_loop=False, failure_isolation=True, reserve_cny=args.reserve_cny,
                   spending_cap_cny=None, balance_guard='between calls, not a hard per-call cap',
                   configuration_home=str(root / 'codex-home'),
                   reused_prepared_batch=str(args.reuse_prepared_batch) if args.reuse_prepared_batch else None,
                   initial_balance_cny=roaring.balance_cny(root),
                   started=datetime.now(timezone.utc).isoformat(),
                   final_jmh=dict(warmup=5, measurement=10, forks=2, seconds=1),
                   quick_jmh=dict(warmup=1, measurement=2, forks=0, seconds=1),
                   scope=f'{task_count} P4 attempts; prep failures retained, no paid call on broken harness',
                   correctness='prepared selected tests plus recompilation of all task-allowed source files; not full suite',
                   benchmark_origin='official except supplemental RoaringBitmap abdd6ff/1de6825'))
    summary_path = batch / 'summary.json'
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else []
    done = {(r['repository'], r['task']) for r in summary}
    count = sum(r.get('agent_started', False) for r in summary)
    for metadata in tasks:
        repo, task = metadata['repository'], metadata['id']
        if (repo, task) in done:
            continue
        output = batch / 'tasks' / repo / task
        output.mkdir(parents=True, exist_ok=True)
        record = dict(repository=repo, task=task, prompt=4, agent_started=False,
                      started=datetime.now(timezone.utc).isoformat(), artifacts=str(output))
        try:
            (batch / 'status.txt').write_text(f'{len(summary)}/{task_count} complete; {repo}/{task}: preparing (unpaid)\n')
            cached = prepare_cached(root, batch, metadata, args.reuse_prepared_batch.resolve()) if args.reuse_prepared_batch else None
            if cached:
                source, original, support, manifest = cached
            elif repo == 'RoaringBitmap':
                original, support, manifest = roaring.prepare(root, batch, task)
                source = root / 'RoaringBitmap-extended-source'
            else:
                source, original, support, manifest = prepare_project(root, batch, metadata)
            # A sandbox-compatible correctness tool is checked before each paid run.
            run([codex, 'sandbox', '--permission-profile', ':workspace', '--cd', original,
                 '--', *tool(repo, 'verify', support, original)],
                log=support / 'sandbox-verify.log', timeout=600, env=codex_env)
            references = {}
            for label in ('original', 'developer'):
                workspace = original
                if label == 'developer':
                    workspace = batch / 'workspaces' / (repo + '-' + task + '-developer')
                    clone_at(source, manifest['fix'], workspace)
                (batch / 'status.txt').write_text(f'{len(summary)}/{task_count} complete; {repo}/{task}: {label} evaluation\n')
                references[label] = evaluate(repo, support, workspace, output / label, label)
            record['references'] = references
            balance = roaring.balance_cny(root)
            write_json(batch / 'budget.json', dict(observed_balance_cny=balance, reserve_cny=args.reserve_cny,
                       agent_runs_started=count, completed_tasks=len(summary)))
            if balance is None or balance <= args.reserve_cny:
                reason = 'balance_unavailable' if balance is None else 'balance_reserve_reached'
                write_json(output / 'pending.json', record)
                (batch / 'status.txt').write_text(f'stopped: {reason}; {len(summary)}/{task_count} complete\n')
                return 2
            workspace = batch / 'workspaces' / (repo + '-' + task + '-prompt4')
            clone_at(source, manifest['parent'], workspace)
            agent_output = output / 'prompt4'
            test = shlex.join(tool(repo, 'verify', support, workspace))
            command = [sys.executable, PROJECT / 'scripts/run_benchllm_codex.py',
                       '--benchmark-root', root / 'BenchLLMRealSE', '--workspace', workspace,
                       '--repo-name', repo, '--commit-id', task, '--prompt-number', '4',
                       '--expected-baseline', manifest['parent'], '--model', 'deepseek-v4-pro',
                       '--codex', codex, '--timeout-seconds', str(args.agent_timeout_seconds),
                       '--command-timeout-seconds', '1800', '--artifacts-dir', agent_output,
                       '--agent-test-command', test, '--verification-command', test,
                       '--agent-benchmark-command', shlex.join(tool(repo, 'quick', support, workspace)),
                       '--benchmark-command', shlex.join(tool(repo, 'benchmark', support, workspace, agent_output))]
            count += 1
            record['agent_started'] = True
            write_json(batch / 'budget.json', dict(observed_balance_cny=balance, reserve_cny=args.reserve_cny,
                       agent_runs_started=count, completed_tasks=len(summary), balance_sample_phase='before_current_agent'))
            (batch / 'status.txt').write_text(f'{len(summary)}/{task_count} complete; {repo}/{task}: P4 agent/evaluation\n')
            try:
                run(command, log=output / 'prompt4.runner.log', timeout=args.agent_timeout_seconds + 3660,
                    env=codex_env)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass
            result_path = agent_output / 'result.json'
            result = json.loads(result_path.read_text()) if result_path.exists() else dict(outcome='runner_failed')
            record.update(outcome=result['outcome'], usage=result.get('usage'))
            if global_api_failure(agent_output):
                record['global_stop_reason'] = 'credentials_or_billing'
        except Exception as exc:
            record.update(outcome='infrastructure_failed', error_type=type(exc).__name__, error=str(exc))
            (output / 'infrastructure-error.log').write_text(traceback.format_exc())
            print('TASK_FAILED_CONTINUING', repo, task, type(exc).__name__, flush=True)
        record['ended'] = datetime.now(timezone.utc).isoformat()
        write_json(output / 'task-result.json', record)
        summary.append(record)
        write_json(summary_path, summary)
        if record.get('global_stop_reason'):
            (batch / 'status.txt').write_text(f"stopped: {record['global_stop_reason']}; {len(summary)}/{task_count} complete\n")
            return 2
    failed = any(r['outcome'] != 'succeeded' or any(v['outcome'] != 'succeeded' for v in
                 r.get('references', {}).values()) for r in summary)
    (batch / 'status.txt').write_text(('complete_with_failures' if failed else 'complete') + f'; {task_count}/{task_count} processed\n')
    write_json(batch / 'final-budget.json', dict(observed_balance_cny=roaring.balance_cny(root),
               agent_runs_started=count, completed_tasks=len(summary), ended=datetime.now(timezone.utc).isoformat()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
