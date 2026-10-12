#!/usr/bin/env python3
"""Read-only experiment inspection; write a stage-separated report, not new runs."""
import argparse
from collections import Counter
import json
from pathlib import Path

import run_benchllm_agent_first as common

FIRST = 'agent-first64-20261011T113000Z'
RETRY = 'agent-first64-timeout-retry-20261012T032000Z'
COMPARE = 'three-versions-batch18-20261012T033600Z'


def read(path, fallback=None):
    return json.loads(path.read_text()) if path.exists() else fallback


def cause(status, text, stage):
    if status == 'TimeoutExpired':
        return ('测试时间上限' if stage == 'verify' else 'JMH测量时间上限')
    rules = [('Unable to acquire the JMH lock', 'JMH共享全局锁冲突：调度/隔离问题，非性能失败'),
             ('need to be run from the root', 'Kafka JMH入口/工作目录或wrapper条件不满足'),
             ('gradlew: No such file', 'Gradle wrapper入口缺失'),
             ('GnuTLS', 'Git源码下载TLS连接异常'),
             ('private access in NetUtil', '原版生产API与共用benchmark访问要求不兼容'),
             ('internalRefCnt', '部分源码回退后API不兼容：internalRefCnt缺失'),
             ('expected [null] but found [NaN]', '功能断言失败：期望null，实际NaN；不修改断言迁就原版'),
             ('ExceptionInInitializer', '类初始化异常，源码/环境根因尚未确定'),
             ('Could not initialize class', '类初始化异常，源码/环境根因尚未确定'),
             ('NullPointerException', '功能测试空指针异常；是否由共用修复版fixture引起尚未确定'),
             ('Compilation failure', '原生构建/编译失败，详见日志；不能直接归为模型答错'),
             ('There are test failures', '现有功能测试失败，详见断言/异常'),
             ('unable to access', 'Git源码获取失败')]
    for needle, reason in rules:
        if needle in text:
            return reason
    return '原生命令失败；具体根因未确认，保留日志，不继续盲目尝试'


def native_failure(batch, item, stage):
    repo, task = item['repository'], item['task']
    out = batch / 'tasks' / repo / task
    plan = read(out / 'native-plan.json', {})
    workspace = Path(plan.get('workspace', str(batch / 'workspaces' / (repo + '-' + task))))
    files = sorted(workspace.glob('.benchllm-results/' + stage + '-*/commands.log'))
    log = files[-1] if files else out / ('native-' + stage + '.log')
    text = log.read_text(errors='replace') if log.exists() else ''
    return dict(repository=repo, task=task, stage=stage, status=item.get(stage),
                reason=cause(item.get(stage), text, stage), evidence=str(log))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--shared-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--remeasure-dir', type=Path)
    args = parser.parse_args()
    base = args.shared_root.resolve() / 'artifacts/benchllmrealse'
    output = args.output_dir.resolve()
    if not output.is_relative_to(base):
        raise ValueError('Report output must remain inside experiment artifacts')
    first, retry, compare = [base / name for name in (FIRST, RETRY, COMPARE)]
    initial = read(first / 'summary.json', [])
    first_native = read(first / 'native-summary.json', [])
    retried = read(retry / 'summary.json', [])
    retry_native = read(retry / 'native-summary.json', [])
    compared = read(compare / 'summary.json', [])
    remeasured = read(args.remeasure_dir / 'summary.json', []) if args.remeasure_dir else []
    key = lambda x: (x['repository'], x['task'])
    first_index, retry_index = [{key(x): x for x in values} for values in (first_native, retried)]
    retry_native_index = {key(x): x for x in retry_native}
    comparison_index = {key(x): x for x in compared}
    remeasure_index = {key(x): x for x in remeasured}
    matched = {key(x) for x in compared if x['outcome']=='succeeded'} | {key(x) for x in remeasured if x['outcome']=='succeeded'}
    ledger = []
    for row in initial:
        k = key(row)
        legacy = row['outcome'] == 'reused_prior_attempt'
        ledger.append(dict(repository=k[0], task=k[1], legacy_protocol=legacy,
              first_agent_outcome=row.get('prior_outcome') if legacy else row['outcome'],
              first_agent_started=bool(legacy or row.get('new_agent_started')),
              first_source_patch=row.get('has_source_patch'),
              first_native=first_index.get(k), retry=retry_index.get(k), retry_native=retry_native_index.get(k),
              three_version=comparison_index.get(k), three_version_remeasure=remeasure_index.get(k),
              effective_matched_comparison=k in matched))
    failures = []
    for name, batch, values in [('首轮', first, first_native), ('Agent补跑后验收', retry, retry_native)]:
        for item in values:
            for stage in ('verify', 'benchmark'):
                if item.get(stage) in ('passed', None) or str(item.get(stage)).startswith('not_run'):
                    continue
                failures.append(dict(cohort=name, **native_failure(batch, item, stage)))
    for name, batch, values in [('首轮', first, initial), ('第二次Agent尝试', retry, retried)]:
        for row in values:
            if row.get('outcome') == 'timeout':
                failures.append(dict(cohort=name, repository=row['repository'], task=row['task'], stage='agent',
                     status='timeout', reason='Agent会话600秒上限；有无补丁与后续验收单独统计',
                     evidence=str(batch / 'tasks' / row['repository'] / row['task'] / 'result.json')))
            elif row.get('outcome') == 'task_error':
                log = batch / 'tasks' / row['repository'] / row['task'] / 'fetch.log'
                text = log.read_text(errors='replace') if log.exists() else row.get('error', '')
                reason = '源码下载120秒超时，未调用模型' if row.get('error_type')=='TimeoutExpired' else cause(row.get('error_type'), text, 'source')
                failures.append(dict(cohort=name, repository=row['repository'], task=row['task'], stage='source',
                     status=row['outcome'], reason=reason, evidence=str(log)))
    for item in compared:
        if item['outcome'] == 'succeeded':
            continue
        case = Path(item['case_dir'])
        for v in read(case / 'summary.json', []):
            for stage in ('verify', 'benchmark'):
                if v.get(stage) in ('passed', None) or str(v.get(stage)).startswith('not_run'):
                    continue
                files = sorted((case / 'workspaces' / v['version']).glob('.benchllm-results/' + stage + '-*/commands.log'))
                log = files[-1] if files else case / 'versions' / (v['version'] + '-' + stage + '.log')
                text = log.read_text(errors='replace') if log.exists() else ''
                failures.append(dict(cohort='三版本对照', repository=item['repository'], task=item['task'],
                     version=v['version'], stage=stage, status=v[stage], reason=cause(v[stage], text, stage), evidence=str(log)))
    new = [x for x in initial if x['outcome'] != 'reused_prior_attempt']
    for item in failures:
        if item['cohort'] == '三版本对照' and (item['repository'],item['task']) in matched:
            item['resolution'] = '首次失败保留；后续合格无模型补测已取得完整三版本数据'
    progress = dict(checked=common.now(), unique_tasks=len(initial), actual_agent_tasks=sum(x['first_agent_started'] for x in ledger),
         legacy_reused=len(initial)-len(new), first_new_outcomes=dict(Counter(x['outcome'] for x in new)),
         first_source_patches=sum(bool(x.get('has_source_patch')) for x in new),
         first_native=dict(tested=len(first_native), test_passed=sum(x['verify']=='passed' for x in first_native),
                           jmh_passed=sum(x.get('benchmark')=='passed' for x in first_native)),
         retry_outcomes=dict(Counter(x['outcome'] for x in retried)),
         retry_native=dict(tested=len(retry_native), test_passed=sum(x['verify']=='passed' for x in retry_native),
                           jmh_passed=sum(x.get('benchmark')=='passed' for x in retry_native)),
         comparison=dict(processed=len(compared), matched=sum(x['outcome']=='succeeded' for x in compared),
                         effective_matched=len(matched),
                         status=(compare / 'status.txt').read_text().strip()),
         remeasure=remeasured,
         limitations=['历史与新协议不混合为同协议成绩', '首次与重试分开，不把重复调用当新任务',
                      '命令/环境失败不自动计为模型错误', '一次JMH对照不是稳定加速或显著性结论'])
    common.write(output / 'progress.json', progress)
    common.write(output / 'task-statuses-64.json', ledger)
    common.write(output / 'failure-catalog.json', failures)
    matched_data = []
    for k in sorted(matched):
        recovered = remeasure_index.get(k)
        if recovered and recovered['outcome']=='succeeded':
            file = args.remeasure_dir / 'tasks' / k[0] / k[1] / 'comparison.json'
        else:
            file = Path(comparison_index[k]['case_dir']) / 'comparison.json'
        matched_data.append(dict(repository=k[0], task=k[1], evidence=str(file), rows=read(file, [])))
    common.write(output / 'matched-comparisons.json', matched_data)
    lines = ['# BenchLLMRealSE 实验进度与失败说明', '', '更新：' + progress['checked'], '',
             '## 当前边界', '', '仅继续具备三版本对照资格的无模型补测；其他失败先归档，不再新增付费Agent或盲目重跑。', '',
             '## 全量覆盖', '',
             f'64题全部处理，{progress["actual_agent_tasks"]}题实际进入过Agent；21题为历史协议复用，43题为新增处理。',
             '新增28次正常结束、14次Agent超时、1题源码拉取超时，41个生产补丁。',
             f'首次独立验收：{progress["first_native"]["test_passed"]}题功能测试通过、{progress["first_native"]["jmh_passed"]}题正式JMH通过。', '',
             '## 第二次尝试', '', json.dumps(progress['retry_outcomes'], ensure_ascii=False),
             '13个工作区验收，7个测试通过；0个JMH通过，包含锁冲突、入口失败等，不能全归为模型问题。', '',
             '## 三版本对照', '',
             f'已处理{len(compared)}/18题；首次{progress["comparison"]["matched"]}题完整，合格补测后累计{len(matched)}个不同任务具备完整三版本测量。',
             '合格补测使用首轮冻结补丁，不将第二次Agent尝试替换进来，也不把首次失败证据删除。',
             '只有三个版本均通过功能测试且缺失测量仅因JMH锁冲突的任务进入一次串行补测。', '',
             '## 失败证据（分阶段，不能把行数当不同任务数）', '',
             '| 阶段 | 任务 | 版本/环节 | 原因 |', '|---|---|---|---|']
    for f in failures:
        lines.append('| ' + f['cohort'] + ' | ' + f['repository'] + '/' + f['task'] + ' | ' +
                     f.get('version', '') + ' ' + f['stage'] + ' | ' + f['reason'] +
                     ('（后续无模型补测已解决）' if item_resolved(f) else '') + ' |')
    lines += ['', '原始日志路径见failure-catalog.json；逐题台账见task-statuses-64.json。', '',
              '不改测试/断言或额外生产代码迁就原版；不绕过JMH锁保护；不自动充值；首次和补跑数据均保留。',
              '对照一次测量只能报告观察到的加速/退化，不能直接称稳定性能提升。', '']
    (output / 'PROGRESS_ZH.md').write_text('\n'.join(lines))
    print(json.dumps(progress, ensure_ascii=False))


def item_resolved(item):
    return bool(item.get('resolution'))


if __name__ == '__main__':
    main()
