#!/usr/bin/env python3
"""Bounded, module-scoped native tests/JMH; never a prerequisite for an agent."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from benchllm_project_tools import result_keys
from run_benchllm_full_batch import executable_tests


def gradle_version(workspace):
    wrapper = workspace / 'gradle/wrapper/gradle-wrapper.properties'
    if wrapper.exists():
        match = re.search(r'gradle-([0-9.]+)-(?:bin|all)', wrapper.read_text())
        if match:
            return match.group(1)
    for path in (workspace / 'build.gradle', workspace / 'gradle/dependencies.gradle'):
        if path.exists():
            match = re.search(r'(?:gradleVersion|gradle)\s*[:=]\s*[\'"]([0-9.]+)[\'"]', path.read_text())
            if match:
                return match.group(1)
    raise RuntimeError('Gradle version unavailable; inspect project build configuration')


def test_reports(workspace, modules, started):
    count = 0
    for module in modules:
        for folder in ('target/surefire-reports', 'build/test-results/test'):
            for path in (workspace / module / folder).glob('TEST-*.xml'):
                if path.stat().st_mtime < started - 1:
                    continue
                root = ET.parse(path).getroot()
                for suite in ([root] if root.tag == 'testsuite' else root.findall('testsuite')):
                    if int(suite.get('failures', 0)) or int(suite.get('errors', 0)):
                        raise RuntimeError('Failing native test report: ' + str(path))
                    count += int(suite.get('tests', 0)) - int(suite.get('skipped', 0))
    if count <= 0:
        raise RuntimeError('No fresh executed test cases; zero tests is not a pass')
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('verify', 'quick', 'benchmark'))
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    workspace, batch = Path(plan['workspace']), Path(plan['root'])
    metadata = plan['metadata']
    repo = metadata['repository']
    output = workspace / '.benchllm-results' / (args.mode + '-' + str(time.time_ns()))
    output.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if not re.search(r'API_KEY|TOKEN|SECRET', k, re.I)}
    env['GRADLE_USER_HOME'] = str(batch / 'cache/gradle')
    version = gradle_version(workspace) if repo in ('kafka', 'RoaringBitmap') else None
    major = int(version.split('.')[0]) if version else None
    jdk = '8' if major is None or major <= 4 else ('17' if tuple(map(int, version.split('.'))) >= (7, 3) else '11')
    env['JAVA_HOME'] = '/usr/lib/jvm/java-' + jdk + '-openjdk-amd64'
    env['PATH'] = env['JAVA_HOME'] + '/bin:' + env.get('PATH', '')
    env['MAVEN_OPTS'] = '-Xmx2g'
    maven = ['mvn', '-B', '-Dmaven.repo.local=' + str(batch / 'cache/maven'),
             '-Dcheckstyle.skip=true', '-Dlicense.skip=true', '-Drat.skip=true',
             '-Dair.check.skip-all=true', '-Dfindbugs.skip=true', '-DskipDocs=true']
    gradle = [str(batch / 'cache/tools' / ('gradle-' + version) / 'bin/gradle'), '--no-daemon'] if version else []
    if version and not Path(gradle[0]).is_file():
        gradle = ['bash', str(workspace / 'gradlew'), '--no-daemon']
    started = time.time()
    def run(command, cwd=workspace):
        print('RUN', shlex.join(list(map(str, command))), flush=True)
        with (output / 'commands.log').open('a') as log:
            subprocess.run(list(map(str, command)), cwd=cwd, env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True,
                           timeout=(900 if args.mode == 'benchmark' else plan.get('native_stage_timeout_seconds', 180)))
    try:
        if args.mode == 'verify':
            requested = shlex.split(metadata['unittest'])
            modules = sorted({p.split('/src/test/', 1)[0] for p in requested})
            selection = {}
            for module in modules:
                classes, expansion = executable_tests(workspace, [p for p in requested if p.startswith(module + '/')])
                if not classes:
                    raise RuntimeError('No selected executable tests in ' + module)
                selection[module] = dict(classes=classes, metadata_expanded=expansion)
            (output / 'selection.json').write_text(json.dumps(selection, indent=2))
            if repo in ('netty', 'presto'):
                run([*maven, '-pl', ','.join(modules), '-am', 'install', '-DskipTests'])
                for module, item in selection.items():
                    run([*maven, '-pl', module, 'test', '-Dtest=' + ','.join(item['classes']),
                         '-DfailIfNoTests=true', '-DskipTests=false'])
            else:
                for module, item in selection.items():
                    run([*gradle, module.replace('/', ':') + ':test', '--rerun-tasks',
                         *[v for cls in item['classes'] for v in ('--tests', cls)]])
            details = dict(executed_tests=test_reports(workspace, modules, started), selection=selection)
        else:
            quick = args.mode == 'quick'
            case = metadata['jmh_case'].rsplit('/', 1)[-1]
            pattern = '.*' + re.escape(case) + '.*'
            result = output / 'jmh.json'
            opts = [pattern, '-wi', str(1 if quick else 10), '-i', str(2 if quick else 50),
                    '-f', str(0 if quick else 1), '-r', '1s', '-w', '1s', '-foe', 'true',
                    '-rf', 'json', '-rff', str(result)]
            if repo == 'kafka':
                run(['bash', workspace / 'jmh-benchmarks/jmh.sh', *opts])
            elif repo in ('netty', 'presto'):
                module = 'microbench' if repo == 'netty' else metadata['jmh_case'].split('/')[0]
                run([*maven, '-pl', module, '-am', 'install', '-DskipTests'])
                cpfile = output / 'classpath.txt'
                run([*maven, '-pl', module, 'dependency:build-classpath', '-DincludeScope=test',
                     '-Dmdep.skip=false', '-Dair.check.skip-dependency=false', '-Dmdep.outputFile=' + str(cpfile)])
                cp = os.pathsep.join([str(workspace / module / 'target/classes'),
                                     str(workspace / module / 'target/test-classes'),
                                     str(workspace / module / 'target/jmh-benchmarks.jar'), cpfile.read_text().strip()])
                # Final JMH's outer controller supplies the whole-grid wall limit.
                run([env['JAVA_HOME'] + '/bin/java', '-cp', cp, 'org.openjdk.jmh.Main', *opts])
            else:
                raise RuntimeError('Native benchmark adapter not available for ' + repo)
            rows = json.loads(result.read_text())
            result_keys(rows)
            details = dict(jmh_rows=len(rows), result=str(result), final_evidence=not quick,
                           warmup=1 if quick else 10, measurement=2 if quick else 50, forks=0 if quick else 1)
        report = dict(outcome='passed', mode=args.mode, output=str(output), **details)
        (output / 'result.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report), flush=True)
        return 0
    except Exception as exc:
        report = dict(outcome='failed', mode=args.mode, error_type=type(exc).__name__, error=str(exc), output=str(output))
        (output / 'result.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report), flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
