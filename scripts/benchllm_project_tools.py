#!/usr/bin/env python3
"""Offline Java/Scala overlay, selected JUnit/TestNG tests, and frozen official JMH."""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

from benchllm_java_tools import jmh_command

# Old Kafka Scala uses postfix operators such as `count -= 1`.
SCALA_LANGUAGE_FLAGS = ['-language:postfixOps']


def java_command(java, classpath, *args):
    """Load Byte Buddy before tests so Mockito need not self-attach inside the sandbox."""
    command = [java]
    for entry in classpath.split(os.pathsep):
        if Path(entry).name.startswith('byte-buddy-agent'):
            command.append('-javaagent:' + entry)
            break
    command.extend(['-cp', classpath, *args])
    return command


def result_keys(rows):
    keys = [(r['benchmark'], tuple(sorted(r.get('params', {}).items()))) for r in rows]
    if not rows or len(keys) != len(set(keys)):
        raise RuntimeError('Missing or duplicate JMH results')
    for row in rows:
        score = row['primaryMetric']['score']
        if not isinstance(score, (float, int)) or not math.isfinite(score) or score <= 0:
            raise RuntimeError('Invalid JMH score')
    return sorted(keys)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('verify', 'benchmark', 'quick'))
    parser.add_argument('--support', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.support / 'manifest.json').read_text())
    workspace = args.workspace.resolve()
    java = str(Path(manifest['java_home']) / 'bin/java')
    javac = str(Path(manifest['java_home']) / 'bin/javac')
    cp = os.pathsep.join(manifest['runtime_classpath'])
    with tempfile.TemporaryDirectory(prefix='benchllm-project-') as tmp:
        overlay = Path(tmp) / 'classes'
        overlay.mkdir()
        effective = str(overlay) + os.pathsep + cp
        sources = [str(workspace / p) for p in manifest['source_paths']]
        java_sources = [p for p in sources if p.endswith('.java')]
        scala_sources = [p for p in sources if p.endswith('.scala')]
        if java_sources:
            subprocess.run([javac, '-source', manifest['java_release'], '-target',
                            manifest['java_release'], '-proc:none', '-cp', effective,
                            '-d', str(overlay), *java_sources], check=True, cwd=workspace)
        if scala_sources:
            subprocess.run([java, '-cp', cp, 'scala.tools.nsc.Main', '-usejavacp',
                            *SCALA_LANGUAGE_FLAGS, '-classpath', effective, '-d', str(overlay),
                            *scala_sources], check=True, cwd=workspace)
        if args.mode == 'verify':
            if not manifest['test_classes']:
                raise RuntimeError('No executable tests; cannot certify correctness')
            if manifest['test_framework'] == 'testng':
                command = java_command(java, effective, 'org.testng.TestNG', '-usedefaultlisteners',
                                       'true', '-d', str(Path(tmp) / 'testng'), '-testclass',
                                       ','.join(manifest['test_classes']))
            else:
                command = java_command(java, effective, 'org.junit.platform.console.ConsoleLauncher',
                                       '--disable-ansi-colors', '--fail-if-no-tests', '--details=summary',
                                       *[v for c in manifest['test_classes'] for v in ('--select-class', c)])
            return subprocess.run(command, cwd=workspace).returncode
        output = args.output.resolve() if args.output else Path(tmp) / 'results'
        output.mkdir(parents=True, exist_ok=True)
        quick = args.mode == 'quick'
        print('In-process exploratory JMH; not final evidence.' if quick else 'Forked final JMH.', flush=True)
        (output / 'measurement_protocol.json').write_text(json.dumps(dict(
            mode=args.mode, forks=0 if quick else 2, warmup=1 if quick else 5,
            measurement=2 if quick else 10, seconds=1, authoritative=not quick,
            metric_origin='official', parameter_policy='all defaults; no task-specific truncation'), indent=2))
        result = output / 'jmh-0.json'
        command = jmh_command(effective, dict(pattern=manifest['pattern']), result, quick=quick)
        command[0] = java
        subprocess.run(command, check=True, cwd=workspace)
        rows = json.loads(result.read_text())
        keys = result_keys(rows)
        # No silent removal of rows that failed in another compared version.
        expected_path = args.support / 'expected-jmh-keys.json'
        if not quick and expected_path.exists():
            expected = json.loads(expected_path.read_text())
            actual = json.loads(json.dumps(keys))
            if actual != expected:
                raise RuntimeError('JMH coverage differs from the original version')
        (output / 'jmh.json').write_text(json.dumps(rows, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
