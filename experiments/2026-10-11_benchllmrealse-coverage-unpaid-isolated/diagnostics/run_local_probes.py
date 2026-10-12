"""Offline probes. All writes stay under this experiment; no SSH or model calls."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile
from coverage_fixes import declared_plugin_in_parent_chain

HERE = Path(__file__).resolve().parent
JDK = Path('/Library/Java/JavaVirtualMachines/temurin-8.jdk/Contents/Home')


def command(label, args, cwd=HERE):
    env = dict(os.environ, LC_ALL='en_US.UTF-8')
    result = subprocess.run([str(x) for x in args], cwd=cwd, env=env,
                            capture_output=True, text=True, timeout=90)
    return dict(label=label, command=[str(x) for x in args], returncode=result.returncode,
                stdout=result.stdout, stderr=result.stderr)


def main():
    records = []
    fixture_pom = HERE / 'fixtures/presto/pom.xml'
    parent_detection = dict(
        project_pom_literal_detection='git-commit-id-plugin' in fixture_pom.read_text(),
        inherited_detection=declared_plugin_in_parent_chain(fixture_pom, HERE / 'fixtures/maven',
            'pl.project13.maven', 'git-commit-id-plugin')) if fixture_pom.exists() else None
    for level in ('6', '7', '8'):
        output = HERE / 'out' / ('source' + level)
        output.mkdir(parents=True, exist_ok=True)
        records.append(command('minimal_netty_source_' + level,
            [JDK / 'bin/javac', '-J-Duser.language=en', '-source', level, '-target', level,
             '-d', output, HERE / 'SourceInferenceProbe.java']))
    plugin_compile = command('compile_actual_plugin_probe', [JDK / 'bin/javac',
        '-J-Duser.language=en', '-cp', str(HERE / 'deps/*'), '-d', HERE / 'out',
        HERE / 'PluginDescribeProbe.java'])
    records.append(plugin_compile)
    if plugin_compile['returncode'] == 0:
        # Empty commits contain no benchmark/source answer. Both clones are synthetic.
        with tempfile.TemporaryDirectory(prefix='shallow-probe-', dir=HERE / 'out') as temp:
            root = Path(temp)
            origin, shallow = root / 'origin', root / 'shallow'
            setup = [(['git', 'init', origin], root),
                     (['git', '-c', 'user.name=Probe', '-c', 'user.email=probe@localhost',
                       'commit', '--allow-empty', '-m', 'parent'], origin),
                     (['git', '-c', 'user.name=Probe', '-c', 'user.email=probe@localhost',
                       'commit', '--allow-empty', '-m', 'head'], origin),
                     (['git', 'clone', '--depth=1', origin.as_uri(), shallow], root)]
            for index, (args, cwd) in enumerate(setup):
                result = command('synthetic_git_setup_' + str(index), args, cwd)
                records.append(result)
                if result['returncode']:
                    raise RuntimeError('Local synthetic Git fixture failed')
            args = [JDK / 'bin/java', '-Duser.language=en', '-cp',
                    str(HERE / 'out') + os.pathsep + str(HERE / 'deps/*'),
                    'PluginDescribeProbe', shallow]
            records.append(command('plugin_shallow_without_tag', args))
            records.append(command('tag_current_parent_only', ['git', '-c', 'user.name=Probe',
                '-c', 'user.email=probe@localhost', 'tag', '-a', 'benchllm-prepare',
                '-m', 'metadata anchor', 'HEAD'], shallow))
            records.append(command('plugin_shallow_with_head_tag', args))
    real_source = HERE / 'real-netty/PendingWriteQueueTest.java'
    if real_source.exists():
        for level in ('7', '8'):
            output = HERE / 'out' / ('real-netty-source' + level)
            output.mkdir(parents=True, exist_ok=True)
            compile_result = command('actual_netty_test_source_' + level,
                [JDK / 'bin/javac', '-J-Duser.language=en', '-source', level, '-target', level,
                 '-cp', str(HERE / 'deps/*'), '-d', output, real_source])
            records.append(compile_result)
            if compile_result['returncode'] == 0:
                records.append(command('actual_netty_test_run_source_' + level,
                    [JDK / 'bin/java', '-Duser.language=en', '-cp',
                     str(output) + os.pathsep + str(HERE / 'deps/*'),
                     'org.junit.runner.JUnitCore', 'io.netty.channel.PendingWriteQueueTest']))
    artifacts = {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in [*sorted((HERE / 'deps').glob('*.jar')),
                              *sorted((HERE / 'real-netty').glob('*.java')),
                              *sorted((HERE / 'fixtures').rglob('*.pom')),
                              *sorted((HERE / 'fixtures').rglob('pom.xml'))]}
    data = dict(scope='local offline diagnostic; not full benchmark preparation',
                java_home=str(JDK), artifacts_sha256=artifacts, records=records,
                actual_presto_parent_detection=parent_detection)
    result_path = HERE / 'out/results.json'
    result_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(results=str(result_path),
        results_summary=[dict(label=r['label'], returncode=r['returncode']) for r in records]), indent=2))
    by_label = {record['label']: record for record in records}
    expected = {'minimal_netty_source_6': 0, 'minimal_netty_source_7': 0,
                'minimal_netty_source_8': 1, 'plugin_shallow_without_tag': 1,
                'plugin_shallow_with_head_tag': 0, 'actual_netty_test_source_7': 0,
                'actual_netty_test_run_source_7': 0, 'actual_netty_test_source_8': 1}
    if any(by_label.get(label, {}).get('returncode') != code for label, code in expected.items()):
        raise RuntimeError('Diagnostic control or candidate did not behave as expected; inspect raw results')
    if parent_detection != dict(project_pom_literal_detection=False, inherited_detection=True):
        raise RuntimeError('Unexpected original Presto parent-model detection')


if __name__ == '__main__':
    main()
