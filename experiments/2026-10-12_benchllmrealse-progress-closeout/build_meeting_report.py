#!/usr/bin/env python3
"""Read frozen results, validate accounting, emit an apply_patch document patch.

No SSH, API, experiment execution, credential access, or direct filesystem writes.
Generated Markdown and JSON are applied with the normal apply_patch tool.
"""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = HERE / 'results'
GITHUB_BLOB_BASE = 'https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent'


def load(path):
    return json.loads(path.read_text())


def link(path, label):
    # Publish browsable links, not paths tied to the report author's laptop.
    relative = quote(path.resolve().relative_to(REPO).as_posix(), safe='/')
    return f'[{label}]({GITHUB_BLOB_BASE}/{relative})'


def table(headers, rows):
    def cell(x):
        return str(x).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(cell, row)) + ' |' for row in rows])


def fmt(x):
    return f'{x:.6g}'


def ratio(x):
    return f'{x:.4f}' if x < 1000 else f'{x:.4g}'


def key(row):
    return row['benchmark'], tuple(sorted(row.get('params', {}).items()))


tasks = load(RESULTS / 'task-statuses-64.json')
matched = load(RESULTS / 'matched-comparisons.json')
failures = load(RESULTS / 'failure-catalog.json')
progress = load(RESULTS / 'progress.json')
runtime = load(HERE / 'report-runtime-evidence.json')
first = load(REPO / 'experiments/2026-10-11_benchllmrealse-agent-first64/results/summary.json')
retry = load(REPO / 'experiments/2026-10-12_benchllmrealse-timeout-retry14/results/summary.json')
assert len(tasks) == len({(x['repository'], x['task']) for x in tasks}) == 64
new = [x for x in tasks if not x['legacy_protocol']]
assert len(new) == 43 and sum(x['first_agent_started'] for x in new) == 42
assert sum(bool(x['first_source_patch']) for x in new) == 41
assert sum((x['first_native'] or {}).get('verify') == 'passed' for x in new) == 34
assert sum((x['first_native'] or {}).get('benchmark') == 'passed' for x in new) == 18
assert Counter(x['first_agent_outcome'] for x in new) == {
    'agent_completed': 25, 'agent_completed_with_environment_changes': 3, 'timeout': 14, 'task_error': 1}
assert len(retry) == 14 and sum(bool(x.get('new_agent_started')) for x in retry) == 13
assert sum(bool(x.get('has_source_patch')) for x in retry) == 12
assert sum((x['retry_native'] or {}).get('verify') == 'passed' for x in tasks) == 7
assert sum((x['retry_native'] or {}).get('benchmark') == 'passed' for x in tasks) == 0
assert len(matched) == 14 and sum(len(x['rows']) for x in matched) == 63
assert {(x['repository'], x['task']) for x in matched} == {
    (x['repository'], x['task']) for x in tasks if x['effective_matched_comparison']}

raw_files, raw_lookup = {}, {}
for task in matched:
    repo, tid = task['repository'], task['task']
    eligible = RESULTS / 'eligible-comparisons/tasks' / repo / tid
    base = eligible if eligible.is_dir() else RESULTS / 'initial-comparisons/cases' / f'three-versions-{repo}-{tid}' / 'versions'
    for version in ('original', 'developer', 'agent'):
        file = base / f'{version}-jmh.json'
        raw_files[repo, tid, version] = file
        rows = load(file)
        indexed = {key(row): row for row in rows}
        assert len(indexed) == len(rows) == len(task['rows'])
        for row in task['rows']:
            actual = indexed[key(row)]
            assert actual['mode'] == row['mode']
            assert actual['primaryMetric']['scoreUnit'] == row['unit']
            assert math.isclose(actual['primaryMetric']['score'], row['scores'][version], rel_tol=1e-12)
            assert actual['warmupIterations'] == 10 and actual['measurementIterations'] == 50 and actual['forks'] == 1
            assert actual['warmupTime'] == actual['measurementTime'] == '1 s'
            raw_lookup[repo, tid, version, key(row)] = actual
    for row in task['rows']:
        for version in ('developer', 'agent'):
            expected = (row['scores'][version] / row['scores']['original'] if row['mode'] == 'thrpt'
                        else row['scores']['original'] / row['scores'][version])
            assert math.isclose(expected, row['speedup_vs_original'][version], rel_tol=1e-12)

flat = [r for t in matched for r in t['rows']]
faster_original = sum(r['speedup_vs_original']['agent'] > 1 for r in flat)
faster_developer = sum(r['speedup_vs_original']['agent'] > r['speedup_vs_original']['developer'] for r in flat)
assert faster_original == 40 and faster_developer == 30
assert all(r['speedup_vs_original']['agent'] != 1 for r in flat)
assert all(r['speedup_vs_original']['agent'] != r['speedup_vs_original']['developer'] for r in flat)


def performance_order(row):
    """Order point estimates by performance, not by numeric runtime magnitude."""
    scores = row['scores']
    assert len(set(scores.values())) == 3, 'Exact ties require a separate category'
    labels = {'agent': 'Agent', 'developer': '开发者', 'original': '原版'}
    order = sorted(scores, key=scores.get, reverse=row['mode'] == 'thrpt')
    return ' ＞ '.join(labels[name] for name in order)


orders = ['Agent ＞ 开发者 ＞ 原版', 'Agent ＞ 原版 ＞ 开发者',
          '开发者 ＞ Agent ＞ 原版', '开发者 ＞ 原版 ＞ Agent',
          '原版 ＞ Agent ＞ 开发者', '原版 ＞ 开发者 ＞ Agent']
order_counts = Counter(performance_order(row) for row in flat)
order_by_mode = {mode: Counter(performance_order(row) for row in flat if row['mode'] == mode)
                 for mode in ('avgt', 'thrpt')}
assert [order_counts[order] for order in orders] == [16, 5, 19, 8, 9, 6]
assert sum(order_counts.values()) == 63
ordering_table = table(['三版本性能排序', '对照组合数', '占比'],
                       [[order, order_counts[order], f'{order_counts[order] / 63:.1%}'] for order in orders] +
                       [['合计', 63, '100%']])
ordering_metric_table = table(['三版本性能排序', '平均耗时（43组）', '吞吐量（20组）', '合计'],
                              [[order, order_by_mode['avgt'][order], order_by_mode['thrpt'][order],
                                order_counts[order]] for order in orders] + [['合计', 43, 20, 63]])
secondary_keys = sorted({name for row in raw_lookup.values() for name in row.get('secondaryMetrics', {})})
assert not secondary_keys, 'Revisit the reported metric coverage if secondary metrics are present'
project_rows = []
for repo in ('kafka', 'netty', 'presto', 'RoaringBitmap'):
    group = [x for x in tasks if x['repository'] == repo]
    fresh = [x for x in group if not x['legacy_protocol']]
    project_rows.append([repo, len(group), sum(x['first_agent_started'] for x in group),
                         sum(x['legacy_protocol'] for x in group),
                         sum(x['first_agent_started'] for x in fresh),
                         sum(bool(x['first_source_patch']) for x in fresh),
                         sum((x['first_native'] or {}).get('verify') == 'passed' for x in fresh),
                         sum((x['first_native'] or {}).get('benchmark') == 'passed' for x in fresh),
                         sum(x['effective_matched_comparison'] for x in group)])
project_rows.append(['合计', 64, 63, 21, 42, 41, 34, 18, 14])
project_table = table(['项目', '题数', '累计进入Agent', '历史复用', '新进入Agent', '新生产补丁', '新测试通过', '新JMH通过', '完整三版'], project_rows)

task_rows = []
for task in matched:
    rows = task['rows']
    values = [r['speedup_vs_original']['agent'] for r in rows]
    developer = [r['speedup_vs_original']['developer'] for r in rows]
    task_rows.append([f"{task['repository']}/{task['task']}", len(rows),
                      sum(x > 1 for x in values), sum(a > d for a, d in zip(values, developer)),
                      f'{ratio(min(values))}–{ratio(max(values))}',
                      f'{ratio(min(developer))}–{ratio(max(developer))}',
                      '极大倍率待复核' if max(values) > 1000 else '一次点估计'])
task_table = table(['任务', '场景', 'Agent快于原版', 'Agent快于开发者', 'Agent/原版速比范围', '开发者/原版速比范围', '备注'], task_rows)

groups = Counter()
for task in matched:
    values = [r['speedup_vs_original']['agent'] for r in task['rows']]
    groups['全部场景点估计快于原版' if all(v > 1 for v in values) else
           '全部场景点估计慢于原版' if all(v < 1 for v in values) else '快慢混合'] += 1
known_usage = {}
for name, records in [('首轮新增', first), ('超时第二次尝试', retry)]:
    called = [r for r in records if r.get('new_agent_started')]
    known = [r for r in called if (r.get('usage') or {}).get('total_tokens') is not None]
    known_usage[name] = dict(actual_calls=len(called), records_with_usage=len(known),
                            logged_tokens={k: sum((r.get('usage') or {}).get(k) or 0 for r in known)
                                           for k in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')})

methods = f'''# 评测方法与批次统计口径（备查）

统计冻结：2026-10-12，包含当天16:30完成的最后一批补测。数据来自实际运行台账和本地保存的原始JMH JSON；本次整理没有新增模型调用或实验。

## 1. 文件用途

供复核模型配置、执行参数、批次差异及统计分母；面向组会的汇报正文见{link(HERE / 'MEETING_REPORT_ZH.md', '组会报告')}。本文保留过程口径，不作为开场讲稿。

## 2. 本周到底改了什么

以前：Python脚本直接调用LLM → 解析模型文本补丁 → 应用补丁 → 脚本按固定流程测试。

现在：Python调度器启动Codex CLI → Agent在工作区自主读代码/改代码/调用命令 → 从Git工作区收集真实修改 → 外部独立验收。

这次接入完成在Java benchmark专用入口，**并非仓库所有LLM调用都已迁移**；原有Python实验入口和直接LLM客户端仍保留。本轮不额外生成Python microbenchmark，不重新发现性能问题，任务、测试和性能负载由benchmark提供。也没有新增“直接LLM”对照组，因此暂不能证明Agent优于直接LLM。

### 这个benchmark提供什么

本次使用PerfOpt的真实性能修复案例，来自Kafka16题、Netty18题、Presto25题、RoaringBitmap5题。每题以开发者修复提交标识，关联待优化源码、问题描述、已有测试与JMH负载；开发者最终实现可作为参考。因此不是只有“问题”而没有答案，但开发者实现不是唯一正确答案，也不保证在我们每个测量场景都最快。

Original是未优化的目标源码状态，不是另一个LLM生成的“baseline补丁”。我们评测的是在已给定问题与负载下，Agent能否产生可验收的性能修改，而不是自动从整个仓库发现未知性能问题。

## 3. 第一阶段实际架构

```text
官方任务元数据 + P4提示 + 任务源码
                  ↓
Python任务队列：独立工作区、权限、时间上限、失败续跑、记录
                  ↓
Codex CLI（每题一个有界Agent会话）
  自主读取代码 ↔ 修改源码 ↔ 执行构建/测试/快速JMH并读取结果
                  ↓
生产源码补丁 + 环境配置补丁 + JSONL事件/最终消息/用量/状态
                  ↓  全部新Agent尝试结束后
独立原生验收：Maven/Gradle选定测试 → 正式JMH
                  ↓  18题具备Agent版测试/JMH结果
原版 / 开发者版 / 首轮Agent版：同测试、同负载、同测量配置
                  ↓
14题完整对照 + 其余失败原因归档 → 组会统计
```

CLI自身通过配置的Responses兼容远程provider访问模型；Python与CLI则通过进程stdin/stdout通信，不是Python直接调用模型SDK。模型配置名是`deepseek-v4-pro`，不是OpenAI Codex模型；provider真实底层型号/实现未经独立核验，不能据此称DeepSeek官方原生支持Responses。

### 输入、输出与下一步判断

- 输入：官方P4（性能问题、源码、单元测试、目标benchmark函数）＋Agent实验约束＋原生测试/快速测量命令＋已有准备失败的诊断信息。P4包含负载信息，不能称为未见负载泛化评测。
- 输出：Agent直接修改工作区；脚本导出`source.patch`与`environment.patch`，保留`codex_events.jsonl`、`codex_stderr.log`、最终消息和`result.json`。不是只相信Agent口头说“优化成功”。
- Agent内部自己决定何时执行工具、如何处理失败。外部流程依据进程结束/超时、实际Git修改、测试返回码与新报告、完整JMH JSON推进；没有强制“修改—测试—反馈”三轮循环。
- 每题`--ephemeral`启动独立会话，本批没有跨进程resume续聊；运行ID、目录、预算和状态台账是我们的调度器管理，不是新增用户数据库系统。
- 移除了“构建/测试/参考版本先成功才能进入Agent”的门槛，只保留源码与提示可获得等必要准备。Agent可以诊断和调整许可范围内构建配置；修改测试、断言、benchmark、负载或非目标生产源码不被接受。
- 正式验收由我们的适配/调度代码启动成熟的项目原生测试与JMH。Agent可通过shell调用相同测试工具并看日志；**当前没有MCP server或新测试生成模块**。

## 4. 实验配置与参数

| 配置项 | 实际设置 |
| --- | --- |
| 数据集范围 | BenchLLMRealSE的PerfOpt，64题、4项目；未运行SCAT/EffiBench-X |
| 本轮Prompt | 固定官方P4，不是P1–P4四种Prompt全量比较；额外附加Agent执行规则 |
| Agent | Codex CLI 0.161.0，`codex exec --json --ephemeral --cd <workspace>` |
| 模型/provider | 配置名`deepseek-v4-pro`，provider=`deepseek`，`wire_api=responses`；不是Claude Code/GLM实验 |
| 推理参数 | 配置请求`model_reasoning_effort=high`；未核实provider是否实际按该参数执行，未显式统一temperature/seed |
| 单题Agent上限 | 600秒；外部不强制修复循环；14题超时后各安排一次独立第二尝试 |
| 源码下载 | 缺失Git对象的拉取上限120秒；失败记录后继续 |
| 沙箱/权限 | 批次专用`agent_eval`工作区写入权限；允许依赖网络/本地测试服务；限制凭据、参考源码和其他批次目录；不是完全断网或全权限运行 |
| 源码约束 | 目标生产文件可改；许可构建配置单独保存；测试/断言/JMH与负载不改 |
| 测试 | 项目原生Maven/Gradle，按元数据选定测试；需要新生成、实际执行的非零测试报告；不等于全部项目测试套件 |
| 独立测试上限 | 首轮/第二尝试验收180秒；三版本对照每版本600秒 |
| 正式JMH | `-wi 10 -i 50 -f 1 -w 1s -r 1s -foe true -rf json`；不默认截断参数网格 |
| 正式JMH上限 | 每题/每版本900秒；部分JSON或截断结果不计通过；三版本单案例调度上限5400秒 |
| Agent探索测量 | 预热1、测量2、fork0；不是正式证据，受Agent会话和工具时间预算限制 |
| Java工具链 | JDK8/11/17；Netty/Presto用JDK8，Kafka按历史Gradle版本选择；私有Maven/Gradle缓存 |
| 服务器 | `ssh lab-server`；i9-13900K，24物理核/32逻辑CPU，约125.5GiB RAM；Python3.10.12；模型远程API推理 |
| 对照资源 | CPU0、1（同一个P核的两个SMT线程），串行版本测量；并行Agent补跑阶段临时分配CPU2–31；其他用户/内存/IO未完全隔离 |
| JMH锁修正 | 合格补测设置每版本独立`java.io.tmpdir`，保留锁保护；CPU分开本身不能隔离`/tmp/jmh.lock` |
| 失败策略 | 普通单题失败/超时记录后继续；公共凭据/计费问题停止付费队列；余额保留阈值2元，不自动充值；没有硬性总消费上限 |
| 成本解释 | 超时可能已有付费调用且缺最终usage；本批准确总费用未完整留档，不能用缺失usage推断0元 |

### 三版本如何构造

使用修复版本作为公共fixture，仅将元数据指定的生产源码回退到修复前内容，得到Original；不是完整父提交checkout。Developer把同一批目标源码替换为实际开发者修复；Agent使用**首轮**冻结的生产改动，不从第二次尝试挑最好结果替换。

三版本的其他文件（测试、JMH、非目标源码、构建配置）做SHA256一致性检查；若接受了Agent构建配置修复，会同样应用到三版本。正式比较重新测量三个版本，不拿不同协议/不同批次的原分数拼成对照。

对照编排曾调整：初版逐版本测试/测量；后续未开始案例改为三版测试全通过再测JMH，运行中的案例不中断。3题合格补测重新测了全部三版，不混用旧的局部成功数值。

## 5. 概括结果：先区分处理、调用、验收、比较

| 指标 | 数量与口径 |
| --- | --- |
| 全量处理覆盖 | 64/64（100%），表示都有终态记录，不等于全部成功 |
| 实际进入过Agent的不同题 | 63/64（98.4%）＝历史21＋新42；Presto/9e010a7源码下载失败未调用 |
| 新任务 | 43：28会话正常结束、14达到600秒上限、1源码失败 |
| 新生产补丁 | 41/42实际调用（97.6%）；补丁存在不等于功能/性能正确 |
| 新独立测试通过 | 34/42工作区（81.0%）；测试超时4、测试/构建命令失败4 |
| 新正式JMH通过 | 18/34测试通过（52.9%），或18/42实际调用（42.9%）；JMH命令失败8、超时8 |
| 完整三版本 | 14/18候选（77.8%）；首次11＋无模型合格补测3；另4题不满足完整对照条件 |
| 完整对照场景 | 63个benchmark名称×参数组合；不是63道独立题 |

64题互斥归档为：历史21＋新增测试/JMH均通过18＋新增测试通过但JMH失败/超时16＋新增测试失败/超时8＋未调用的源码失败1＝64。超时14题是上述类别的子集，不能再加14凑总数。

### 按项目统计

{project_table}

“新”列仅指最新Agent优先批次。历史21题为18个旧协议`succeeded`、3个旧协议`benchmark_failed`；旧版采用完整parent/overlay及预热5、测量10、fork2等设置，未在新协议重新评测，不能与新18题相加发布统一成功率。Kafka的新正式测量没有通过，RoaringBitmap本轮全部是历史复用；最终对照只有Netty3题和Presto11题，存在样本选择偏差。

### 14题超时补跑，单独统计

14题第二尝试：13实际进入Agent，6会话正常结束，7再次超时，1下载TLS失败；12生产补丁、7独立测试通过，正式JMH新增通过0。JMH失败中有入口和锁等执行障碍，不能全部当模型答错。补跑没有增加不同题数量，也没有替换首轮对照补丁；不会自动第三次调用Agent。

首轮14次超时中13次留下补丁，7题测试通过，Netty/dd69a81及Presto/fdb7611两题正式JMH也通过。**会话超时不等于没有成果；正常结束也不等于通过验收。**

## 6. 三版本性能对照结果

统一定义速比：吞吐量用`Variant / Original`，耗时用`Original / Variant`。大于1表示该场景点估计更快，小于1更慢；Agent与Developer比较用两者对Original速比之比。

63场景中：Agent快于Original **40/63（63.5%）**、慢于Original **23/63**；快于Developer **30/63（47.6%）**、慢于Developer **33/63**。按任务看，3题所有场景点估计更快、1题全部更慢、10题快慢混合，不定义“某题只要一行快就算成功”。29个场景的Agent/Original速比落在0.95–1.05，仅描述接近1，不是显著性判断阈值。

{task_table}

这张表是全部匹配负载的范围，不只挑最快的一行，也不把它当任务的代表性最终分数。63组原始分数、模式、单位、参数、JMH误差字段及原始文件链接见详细附录。

本轮统计是我们从匹配的原始JMH分数计算速比，尚未运行官方`normalize_score.py`/`final_score.py`及完整RQ分析，不应把这些速比直接标成论文的代表性最终分数或声称复现了论文表格。

可展示的正反案例：Netty/9abeaf1三场景速比1.0103–1.6037；Presto/53aa7f6单场景1.0805；Presto/60a5a5c两场景0.8993–0.9759。Presto/bfb18d6的极大倍率来自原始耗时分数接近零，须进一步检查补丁语义、benchmark状态与测量是否合理，暂不能把“百万倍加速”当已证实成果。

## 7. 未完成完整对照的原因

| 任务 | 已观察的障碍 | 处理 |
| --- | --- | --- |
| Presto/20dcaed | Original的testSTMax/testSTMin期望null、实际NaN | 保留失败，不修改断言迁就原版 |
| Netty/7b91edd | Original的getIPv6ByName接口为private，共用benchmark不能访问 | 基线/API资格问题，不归为Agent性能失败 |
| Presto/8d7f587 | Original的testSTEnvelope空指针；具体根因仍需确认 | 保留日志，本阶段不继续尝试 |
| Netty/e542a2c | Original部分回退后internalRefCnt缺失/override编译失败 | 共用fixture/API不兼容，不额外改原版源码凑比较 |

前三版首次测量中的锁冲突，只有Presto/290f5be、Netty/ab8c4f2、Netty/dd69a81满足“全部测试通过、缺失测量仅锁冲突”资格。三题无模型补测全部通过，失败证据未删除。其他题即使也遇到锁错误，因仍有基线障碍，不纳入完整比较。

前期覆盖不足不全是benchmark问题：我们曾加了过严的Agent前构建/测试门槛，使用统一overlay/classpath，与官方选择性回退及原生入口有差异；后期已经纠正。并发测量的全局JMH锁问题也是我们的隔离/调度问题。现有“命令失败”只说明某环节未完成，未经日志根因确认，不能一概称Agent修改导致功能错误。

## 8. 可以得出的结论与组会讨论点

已完成：Agent接入、64题全量处理与63题真实调用覆盖、补丁/轨迹保存、失败分层、14题同配置三版本对照。观察到性能改善和退化并存，且收益依赖负载。

尚不能得出：Agent优于直接LLM/Claude Code/GLM、全64题稳定优化成功、全负载功能正确、严格复现论文全部RQ。当前选定原有测试通过仅为plausibility，不是完整正确性证明；单轮JMH、fork1和共享宿主负载不足以支持跨运行稳定性/显著性结论。场景不是独立任务，不能把63行直接当63独立样本做模型成功率检验。

本阶段不再扩展付费实验。建议组会只确认两个下一步选择：剩余源码/入口/基线兼容失败是否按官方路线继续补齐；对已有14题是否需要独立重复测量和额外功能/负载验证。它们是待批准后续工作，**不是本周完成接入和全量尝试的前置要求**。

## 9. 交付与可追溯证据

- {link(HERE / 'MEETING_DETAILS_ZH.md', '详细附录：64题台账、63场景原始分数与逐阶段失败')}。
- {link(RESULTS / 'meeting-statistics.json', '机器可读汇总与输入文件哈希')}；{link(RESULTS / 'task-statuses-64.json', '64题原始台账')}；{link(RESULTS / 'matched-comparisons.json', '14题对照数据')}；{link(RESULTS / 'failure-catalog.json', '失败日志位置')}。
- {link(HERE / 'report-runtime-evidence.json', '只读核对的CLI/硬件/provider配置证据')}。服务器benchmark副本没有`.git`，不能提供未经记录的源码版本指纹；已有{link(REPO / 'experiments/2026-10-11_benchllmrealse-failed51-retry/OFFICIAL_PIPELINE_AUDIT_ZH.md', '官方路线审计')}包含相关脚本哈希。
- 实现入口：{link(REPO / 'scripts/run_benchllm_agent_first.py', 'Agent批调度')}、{link(REPO / 'src/benchllmrealse/codex_cli.py', 'CLI进程封装')}、{link(REPO / 'scripts/benchllm_native.py', '原生测试/JMH')}、{link(REPO / 'scripts/run_benchllm_three_versions.py', '三版本一致性与比较')}、{link(REPO / 'scripts/remeasure_eligible_comparisons.py', '合格补测')}。
- 所有过程文件按`experiments/YYYY-MM-DD_阶段/`归档；完整工作区/Agent轨迹/测试日志留在服务器`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/`。本次仅整理，不修改生产补丁或测试，不充值、不启动新实验、不commit/push。
'''

final_project_table = table(['项目', '任务总数', '已进入Agent的任务', '完整三版本对照任务'],
                            [[row[0], row[1], row[2], row[-1]] for row in project_rows])
main = f'''# 本周工作汇报：Agent Pipeline接入与Java性能优化评测

汇报日期：2026年10月12日。

## 一、本周完成的工作

本周主要完成了两项工作：一是将Java性能优化实验中的直接LLM补丁生成环节替换为Codex CLI，使Agent能够自主读取项目、修改源码和执行构建测试；二是在BenchLLMRealSE上完成全量任务处理，并获得原版、开发者版和Agent版的性能对照数据。Agent框架采用Codex CLI，底层模型配置为DeepSeek。

Benchmark包含Kafka、Netty、Presto和RoaringBitmap四个项目，共64个真实性能优化任务。全量队列已结束，63个任务实际进入Agent，另1个任务因源码下载失败未进入Agent。在统一配置的对照阶段，14个任务完成了三版本功能测试和性能测量，共获得63组可比较的性能场景。

## 二、最终实验结果

### 1. 全量任务覆盖与完整对照

{final_project_table}

“完整三版本对照”指原版、开发者版和Agent版均完成对应测试与正式JMH，并具有一致的benchmark及参数覆盖。最终对照数据来自Netty3题、Presto11题；Kafka与RoaringBitmap未纳入本次统一配置的完整三版本结果。任务进入Agent仅表示实际尝试，不表示补丁通过验收。

### 2. 性能比较

对14个任务，按benchmark函数及其固定输入参数分别比较性能，共获得63组对照数据。每组包含原版、开发者版和Agent版在相同负载与JMH配置下的分数；63组不是63道任务，也不是将三个版本重复计数。

按三版本的整体性能排序统计，每组只归入以下六种排序中的一种。“＞”表示左侧版本性能优于右侧：平均耗时更低，或吞吐量更高，并非耗时数值更大。

{ordering_table}

从本轮分数看，Agent在21组中排名第一，开发者版在27组中排名第一，原版在15组中排名第一。排序描述三者的相对位置，具体优化幅度仍需结合各组原始分数与速比判断。

本次有两类性能指标：43组测量平均耗时（`ns/op`、`us/op`、`ms/op`，越低越好），20组测量吞吐量（`ops/s`，越高越好）。统计的是各组内的相对排序，不将不同单位的原始分数相加或平均。原始JMH没有内存、对象分配、GC、CPU利用率等指标；本轮未启用相应的额外采集，不能据此报告这些方面的提升。这里的耗时是代码每次操作的耗时，不是Agent处理任务的用时。

按任务观察：3题的所有已测场景均快于原版，1题的所有场景均慢于原版，10题在不同场景下有快有慢。

代表案例：

- Netty/9abeaf1：3个场景均快于原版，速比为1.0103–1.6037。
- Presto/53aa7f6：单场景速比1.0805，开发者版对应速比1.0478。
- Presto/60a5a5c：2个场景均慢于原版，速比为0.8993–0.9759。

速比大于1表示更快：吞吐量按优化版/原版计算，耗时按原版/优化版计算。当前结果说明Agent已经能够完成部分Java性能优化，但收益具有负载差异，不能将“某个场景加速”视为整题普遍成功。

上述快慢依据本轮JMH分数判断，尚未做独立重复运行的显著性检验。部分几何运算场景出现极大倍率，暂保留为待复核数据，不作为已证实的优化幅度展示。全部逐题结果和原始分数见{link(HERE / 'MEETING_DETAILS_ZH.md', '详细附录')}。

## 三、测量方法、实验配置与数据记录

### 1. JMH测量什么

JMH（Java Microbenchmark Harness）是OpenJDK的JVM代码性能测量工具。在本实验中，它重复执行benchmark提供的固定负载，测量原版、开发者版和Agent版的执行性能；功能是否符合预期则由项目已有的单元测试检查。JMH运行成功本身不证明功能正确，也不代表整个系统所有负载都更快。[JMH官方说明](https://github.com/openjdk/jmh)

本轮使用两种测量模式：平均耗时`avgt`回答“完成一次benchmark操作平均需要多久”，吞吐量`thrpt`回答“单位时间能完成多少次benchmark操作”。一次操作的工作量由benchmark代码定义，可能包含多次函数调用或循环，不能将`ops/s`直接解释成整个Kafka/Presto系统的业务QPS。[JMH官方模式示例](https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_02_BenchmarkModes.java)

每个版本先预热10轮，再正式测量50轮，每轮1秒，在1个独立JVM进程中运行。预热不计入正式分数；50轮是同一负载的测量迭代，不是50道任务，也不等于50次独立实验。本轮统一比较的是相同函数、参数、模式和单位下的三版分数。

### 2. 执行配置

以下为本次统一对照结果及对应Agent运行的配置。早期接入试点的设置单独留档，不混入这14题的性能比较。

| 项目 | 设置 |
| --- | --- |
| 任务与提示 | BenchLLMRealSE / PerfOpt，固定官方P4：问题描述、源码、单元测试、目标JMH代码 |
| Agent与模型 | Codex CLI 0.161.0；模型配置名`deepseek-v4-pro`；请求推理强度`high` |
| Agent执行方式 | 每题独立工作区、独立会话；600秒上限；无固定外层修复循环 |
| 功能验收 | 项目原生Maven/Gradle，运行元数据指定的测试；检查返回码与实际执行的测试报告 |
| 正式性能测量 | JMH预热10轮、测量50轮、fork1；每轮1秒；保留完整参数网格 |
| 验收时间预算 | Agent版独立测试180秒；三版本对照测试每版600秒；正式JMH每版900秒 |
| 测量环境 | 实验室服务器i9-13900K，约125.5GiB内存；三版本CPU亲和性均为0、1 |
| 版本控制 | 三版共用测试、JMH与构建配置；仅目标生产源码不同；非目标文件哈希检查 |
| 数据记录 | 保留生产补丁、构建配置补丁、Agent调用轨迹、测试日志与JMH原始JSON |

原版按照benchmark的选择性回退方式构造：目标生产文件使用修复前内容，其余文件保留修复版fixture。开发者版使用实际修复源码，Agent版使用冻结的首轮修改。测量结果未使用超时第二尝试择优替换。

### 3. 本次记录与统计了哪些数据

| 数据类别 | 已记录内容 | 本次用途 |
| --- | --- | --- |
| 全量任务状态 | 项目、题号、是否进入Agent、会话结果、补丁是否存在、测试/JMH状态及失败阶段 | 64题覆盖与逐题进度统计 |
| 平均耗时 | 43组负载，每组三版分数；单位为ns/op、us/op或ms/op | 比较同一操作的执行耗时，越低越好 |
| 吞吐量 | 20组负载，每组三版分数；单位为ops/s | 比较同一负载的处理能力，越高越好 |
| JMH原始测量 | benchmark名称、输入参数、mode、scoreUnit、score、scoreError、scoreConfidence、rawData与测量设置 | 复核数值、测量波动和配置一致性 |
| 三版本比较 | 三版原始分数、对原版的速比、Agent对开发者的速比、六种性能排序 | 统计63组对照，并展示收益与退化 |
| 功能验收 | 所选测试、执行结果、失败断言/异常及实际执行的测试报告 | 判断候选补丁在已有用例下是否通过 |
| Agent过程与修改 | 输入提示、工具调用事件、最终消息、生产补丁、构建/依赖配置改动 | 追踪Agent如何修改及如何处理环境问题 |
| 运行效率与用量 | 起止时间、Agent执行耗时、超时、已返回的input/cached-input/output token字段 | 分析执行成本与预算；不参与代码性能排序 |
| 失败证据 | 失败阶段、错误类型、已确认原因、原始日志位置及补测处理 | 区分下载、环境、功能测试、测量与会话失败 |

最终性能统计使用14题×3版本＝42份完整JMH JSON，共63组×3版本＝189条版本级性能分数。每份JSON可包含多个函数/参数组合，里面的`rawData`还保留各轮测量值。

未采集代码的内存占用、分配量、GC开销、CPU利用率和能耗，也未开展业务请求P95/P99延迟评测。现有JMH误差与置信区间是运行报告字段，尚未用独立重复实验验证版本间差异；不能把报告中的分数分位数直接当成业务请求尾延迟。Agent的耗时/token是优化过程开销，不是优化后代码的性能指标；部分超时调用缺最终usage，不能按零成本计算。

## 四、实验过程中遇到的问题与流程调整

### 1. 第一阶段：小规模验证Agent链路

首先在RoaringBitmap的3个任务上进行了10次Agent运行，覆盖位移计算（34bce1b）、容器元素数量查询（b5b4af6）和checkedAdd（53ba593），验证“读取任务—修改代码—执行测试—输出性能结果”能够跑通。该阶段使用P1–P4不同输入/工具组合，是接入试点，不计入本报告的14题统一配置对照。

试点中观察到部分性能收益，同时补充检查发现个别缓存补丁在共享缓冲区场景存在功能回归。这说明现有测试和JMH通过只能证明当前用例下可运行，不能覆盖全部功能语义。

### 2. 扩展全量时：Agent前置门槛过多

最初的pipeline要求项目构建、选定测试以及部分参考版本准备成功后，才允许进入Agent修改阶段。首次全64题队列只有9题进入Agent，55题在调用模型前被环境准备挡住。

主要障碍包括历史JDK/Gradle与依赖配置、沙箱网络限制，以及我们自行组装overlay/classpath与项目原生构建方式不一致。因此当时的失败主要反映环境和适配问题，而不是Agent已经尝试后无法修改代码。

### 3. 调整适配：回到项目原生入口

针对失败进行了分类诊断，将统一overlay执行方式改为项目原生Maven/Gradle入口，并调整源码fixture，使其与官方选择性回退方式一致。同时允许依赖下载和本地测试服务，保留对凭据、参考答案及其他工作区的访问限制。

这一步解决了部分准备障碍，但如果仍要求所有参考测试/测量都先通过，剩余任务依旧会被挡在Agent之前。

### 4. 调整顺序：先完成Agent尝试，再独立验收

随后移除了Agent前的构建、测试和参考测量成功门槛。只要能获得源码和任务提示，就允许Agent启动；已有环境错误作为诊断信息提供给Agent，允许它调整指定范围内的构建/依赖配置，并将环境改动与生产补丁分开保存。

构建成功从“启动条件”变为Agent可以处理的问题，最终验收标准并未降低：Agent仍不能修改测试、断言或性能负载，补丁仍需接受外部测试和JMH。普通单题错误或超时只记录该题状态，然后继续下一题，不阻塞整批。

调整后完成了全64题处理。对14个达到Agent时间上限的任务又进行了独立第二次尝试：6次正常结束、7次再次超时、1次源码下载失败，未增加已确认的正式JMH通过任务。首轮和第二次尝试分别保存，不覆盖原补丁。

### 5. 最后完成三版本对照，并记录剩余障碍

统一配置的三版本对照阶段纳入18个具有Agent版测试/JMH结果的任务。首次11题取得完整对照；另3题三版测试已通过，但测量受到共享`/tmp/jmh.lock`干扰。为每版本配置独立Java临时目录后，3题补测均完成，最终得到14题完整对照。

剩余4题的对照障碍为：

| 任务 | 障碍 |
| --- | --- |
| Presto/20dcaed | 原版测试期望null，实际得到NaN |
| Presto/8d7f587 | 原版testSTEnvelope出现空指针异常 |
| Netty/7b91edd | 原版方法为private，共用benchmark无法访问 |
| Netty/e542a2c | 部分源码回退后API不兼容，internalRefCnt缺失及override编译错误 |

这些问题已保留源码状态和日志，没有通过修改断言或额外更改原版源码使其强行通过。其他未完成正式评测的任务也按下载、会话超时、构建/测试和JMH阶段记录原因。

## 五、当前架构

```text
任务元数据 + P4 + 独立源码工作区
                    ↓
Python队列：权限、时间预算、失败续跑、记录
                    ↓
Codex CLI / DeepSeek
  自主读代码 ↔ 修改 ↔ 调用测试与快速JMH，读取反馈
                    ↓
冻结补丁与环境改动
                    ↓
外部独立功能验收 → 正式JMH
                    ↓
原版 / 开发者版 / Agent版同配置比较
                    ↓
逐题结果、性能场景及失败证据归档
```

当前Agent通过shell调用提供的测试和快速JMH命令；正式验收由外部脚本执行。Agent内部自主安排修改与工具调用，外部队列只负责调度、资源约束和最终结果记录，不强制固定优化轮数。

## 六、后续方向：工具反馈驱动的Agent优化

可以进一步将现有测试和性能测量封装为统一工具；需要跨Agent复用时，再通过MCP暴露接口。测试工具返回失败用例与日志，性能工具返回各场景分数、相对原版的变化及测量错误。

```text
Agent修改 → 调用测试/性能工具 → 读取结构化反馈
    ↑                                  ↓
    └──── 在给定预算内自主决定继续优化 ────┘

Agent提交最终补丁 → 外部独立正式验收与三版本评分
```

工具封装复用现有Maven/Gradle和JMH，不重新设计测试框架。正式测量需要单独安排时间与调用预算；开发者参考实现和最终评分过程保留在外部，避免向Agent泄露答案。

下一步可在相同任务、模型和预算下，对比当前流程与结构化性能反馈工具流程，观察功能通过率、性能变化、耗时及调用开销。本阶段数据保持冻结，新流程单独开展实验。

## 七、如何查看具体实验数据

本次汇报材料集中在仓库的`experiments/2026-10-12_benchllmrealse-progress-closeout/`，建议先读汇报正文，再按问题进入下面的文件。

```text
2026-10-12_benchllmrealse-progress-closeout/
├── MEETING_REPORT_ZH.md                 汇报正文
├── MEETING_DETAILS_ZH.md                逐题结果与原始分数的阅读入口
├── METHODS_AND_ACCOUNTING_ZH.md         完整执行参数与统计口径
├── report-runtime-evidence.json         CLI、硬件和非敏感模型配置核对
└── results/
    ├── meeting-statistics.json          最终计数、六种排序及文件哈希
    ├── task-statuses-64.json            64题逐题执行状态
    ├── matched-comparisons.json         14题、63组的三版本分数与速比
    ├── failure-catalog.json             分阶段失败原因及服务器日志路径
    ├── initial-comparisons/cases/       首次三版本的分数、状态和参数
    └── eligible-comparisons/tasks/      3题合格补测的最终三版本数据
```

### 1. 根据问题选择文件

| 想查看什么 | 从哪里看 |
| --- | --- |
| 哪些题运行过，哪些测试或测量失败 | {link(HERE / 'MEETING_DETAILS_ZH.md', '详细附录A节')}；机器记录为{link(RESULTS / 'task-statuses-64.json', 'task-statuses-64.json')} |
| 三版本六种排序，以及按耗时/吞吐分开的计数 | {link(HERE / 'MEETING_DETAILS_ZH.md', '详细附录B节')}；汇总为{link(RESULTS / 'meeting-statistics.json', 'meeting-statistics.json')} |
| 某题某个函数/参数下，三版具体是多少 | {link(HERE / 'MEETING_DETAILS_ZH.md', '详细附录C节')}，按题号查找；统一整理的完整精度数据见{link(RESULTS / 'matched-comparisons.json', 'matched-comparisons.json')} |
| 每轮测量值、分数误差与置信区间 | 附录C节每题的original/developer/agent链接，打开对应`*-jmh.json`，查看`primaryMetric` |
| 具体失败原因和原始日志在哪里 | {link(HERE / 'MEETING_DETAILS_ZH.md', '详细附录D节')}与{link(RESULTS / 'failure-catalog.json', 'failure-catalog.json')}，按题号、阶段和版本找`evidence`路径 |
| Agent执行耗时、token和运行轨迹 | 附录E/F节给出用量与批次路径；完整单次`result.json`和JSONL事件保留在服务器 |
| 模型、时间预算、权限和不同阶段设置 | {link(HERE / 'METHODS_AND_ACCOUNTING_ZH.md', '方法文档')}、各实验目录的`config.json`及{link(HERE / 'report-runtime-evidence.json', '运行配置核对')} |
| Agent究竟修改了哪些源码 | 服务器对应任务的`source.patch`、`environment.patch`及工作区；本地归档没有复制所有补丁/测试日志 |

### 2. 示例：查看Netty/9abeaf1

在附录C节搜索`netty/9abeaf1`，可看到三个benchmark函数的三版分数与排序。继续打开{link(raw_files['netty', '9abeaf1', 'agent'], 'Agent原始JMH')}，定位`benchmark`名称末尾为`executeMulti`的记录：`mode=thrpt`、单位`ops/s`、`score≈703131.35`；对应原版约438437.26、开发者版约688511.48，因此该组为Agent ＞ 开发者 ＞ 原版。

`primaryMetric.score`是性能分数，`scoreError`与`scoreConfidence`是JMH报告的误差及区间，`rawData`是各轮测量值。测试是否通过查看{link(RESULTS / 'initial-comparisons/cases/three-versions-netty-9abeaf1/summary.json', '该题三版本状态')}，测量预算/CPU/预热等查看{link(RESULTS / 'initial-comparisons/cases/three-versions-netty-9abeaf1/protocol.json', '该题protocol.json')}。

Netty/ab8c4f2、Netty/dd69a81、Presto/290f5be的最终值来自`eligible-comparisons/tasks/`。附录C节已链接最终文件；首次失败/局部数据仍在`initial-comparisons/`，不混入最终统计。

### 3. 查看完整Agent过程与补丁

具备实验室服务器权限并配置SSH别名后，通过`ssh lab-server`查看。以Netty/9abeaf1为例，完整任务目录为：

```text
/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/
  agent-first64-20261011T113000Z/tasks/netty/9abeaf1/
  ├── source.patch                  Agent生产源码修改
  ├── environment.patch             构建/依赖配置修改（可为空）
  ├── result.json                   任务结果、用量、修改范围等
  ├── native-plan.json              源码、所选测试与工作区位置
  ├── native-evaluation.json        独立测试/JMH验收结果
  └── agent/
      ├── prompt.txt                实际输入提示
      ├── codex_events.jsonl        模型消息、工具调用与输出事件
      ├── codex_stderr.log           CLI错误输出
      ├── last_message.txt          Agent最终说明
      └── result.json               CLI返回码、耗时、状态与用量
```

测试和JMH完整命令日志保留在对应工作区的`.benchllm-results/`下；工作区路径可从`native-plan.json`查找。单元测试XML报告保留在相应模块的Maven/Gradle测试结果目录。其他题/阶段以附录F节批次路径及`failure-catalog.json`中的`evidence`定位，不假设所有题都在同一个批次。
'''

status_names = {'passed': '通过', 'CalledProcessError': '命令失败', 'TimeoutExpired': '超时',
                'agent_completed': '正常结束', 'agent_completed_with_environment_changes': '正常/许可配置修改',
                'timeout': '600秒超时', 'task_error': '源码失败', 'succeeded': '旧协议通过',
                'benchmark_failed': '旧协议JMH失败'}


def status(value):
    if value is None:
        return '—'
    if str(value).startswith('not_run'):
        return '未运行'
    return status_names.get(value, value)


ledger_rows = []
for task in sorted(tasks, key=lambda x: (x['repository'], x['task'])):
    native = task['first_native'] or {}
    second = task['retry'] or {}
    second_native = task['retry_native'] or {}
    second_text = '—' if not second else (f"{status(second.get('outcome'))}；补丁{'有' if second.get('has_source_patch') else '无'}；"
                                          f"测试{status(second_native.get('verify'))}/JMH{status(second_native.get('benchmark'))}")
    comparison = '完整（补测）' if task['three_version_remeasure'] else '完整' if task['effective_matched_comparison'] else '不完整' if task['three_version'] else '未纳入'
    ledger_rows.append([f"{task['repository']}/{task['task']}", '历史' if task['legacy_protocol'] else '新增',
                        status(task['first_agent_outcome']),
                        '旧档另见' if task['legacy_protocol'] else '有' if task['first_source_patch'] else '无',
                        status(native.get('verify')), status(native.get('benchmark')), second_text, comparison])
ledger_table = table(['任务', '协议分组', '首轮/历史状态', '生产补丁', '新独立测试', '新正式JMH', '第二次尝试（独立统计）', '三版本'], ledger_rows)
detail = f'''# 组会详细附录：BenchLLMRealSE

统计冻结2026-10-12。概括、架构及参数见{link(HERE / 'MEETING_REPORT_ZH.md', '主报告')}。本附录从JSON台账自动生成，核对64个不同任务、14个完整对照任务、63个匹配场景，以及三版本42份原始JMH文件的分数与10/50/1、每轮1秒参数。

## A. 按项目与逐题进度

{project_table}

历史组的测试/JMH“—”表示本批未重新验收，不表示从未测过或本次失败。第二次Agent尝试不是新增任务；历史21题的生产补丁未在本台账统一计数，因此不发布跨协议总补丁数。

{ledger_table}

## B. 三版本逐题摘要

### 三版本整体排序（按性能指标分开）

{ordering_metric_table}

“＞”表示性能优于：`avgt`耗时越低越好，`thrpt`吞吐量越高越好。六种排序互斥且覆盖全部63组；每组是一个benchmark函数及固定参数组合。按原始分数点估计排序，未检验排序差异的统计显著性；本批没有完全相等的分数，接近的结果仍可能受测量波动影响。42份匹配JMH文件没有额外secondaryMetrics，因此本次无内存/分配/GC/CPU利用率结果。

### 逐题速比范围

{task_table}

Agent/Original大于1才是该行更快。速比范围不是代表性分数；一次点估计不是统计显著性。详细比较覆盖全部匹配行，没有选择每题最好的负载。

## C. 63个场景的三版本原始分数

分数保留6位有效数字供阅读，完整精度见链接JSON。`thrpt`单位为吞吐，越大越好；`avgt`为耗时，越小越好。时间速比用Original/Variant，吞吐速比用Variant/Original。JMH的scoreError是报告内的误差字段，不是我们重新做的跨版本显著性检验；rawData/scoreConfidence保存在原始文件中。
'''
for task in matched:
    repo, tid = task['repository'], task['task']
    detail += f'\n### {repo}/{tid}\n\n'
    detail += '原始数据：' + '；'.join(link(raw_files[repo, tid, v], v) for v in ('original', 'developer', 'agent')) + '。\n\n'
    rows = []
    error_rows = []
    for i, row in enumerate(task['rows'], 1):
        params = json.dumps(row['params'], ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        a = row['speedup_vs_original']['agent']; d = row['speedup_vs_original']['developer']
        rows.append([i, row['benchmark'], params, row['mode'], row['unit'],
                     *[fmt(row['scores'][v]) for v in ('original', 'developer', 'agent')],
                     performance_order(row), ratio(a), ratio(d), ratio(a / d)])
        error_rows.append([i, *[fmt(raw_lookup[repo, tid, v, key(row)]['primaryMetric']['scoreError']) for v in ('original', 'developer', 'agent')]])
    detail += table(['行', 'benchmark', 'params', 'mode', '单位', 'Original', 'Developer', 'Agent', '三版本性能排序', 'Agent/Original速比', 'Developer/Original速比', 'Agent/Developer速比'], rows) + '\n\n'
    detail += table(['行', 'Original scoreError', 'Developer scoreError', 'Agent scoreError'], error_rows) + '\n'

detail += '\n## D. 失败目录（历史事件，不是互斥任务数）\n\n'
detail += '同一题可在会话、测试、JMH以及不同版本多次出现；下表77条不能称77题失败，也不能当最终失败率。已解决的锁冲突保留旧证据并标明补测结果。每条对应的完整服务器日志路径见' + link(RESULTS / 'failure-catalog.json', 'failure-catalog.json') + '。\n\n'
detail += table(['证据序号', '批次/阶段', '任务', '版本', '环节', '原因与后续处理'],
                [[i, x['cohort'], f"{x['repository']}/{x['task']}", x.get('version', '—'), x['stage'],
                  ('首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留' if x.get('resolution') else x['reason'])]
                 for i, x in enumerate(failures, 1)])
detail += '\n\n## E. 用量与次数口径\n\n'
detail += '本轮新调用42题＋超时第二尝试13题＝55个实际启动Agent的题次；一个Agent会话通常包含多次模型API请求，55不是API请求总数，也不包括历史21题及此前其他批次的请求。\n\n'
detail += table(['批次', '实际Agent题次', '有total_tokens记录', '日志input_tokens合计', '其中cached_input_tokens', '日志output_tokens合计', '日志total_tokens合计'],
                [[name, x['actual_calls'], x['records_with_usage'],
                  *[x['logged_tokens'][k] for k in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')]]
                 for name, x in known_usage.items()])
detail += '\n\n这些只是已记录usage字段的合计，不是完整费用账单；首轮含一条超时会话留下的usage，其他超时多缺最终记录。cached_input_tokens是input_tokens的子集，不能再次相加；未知usage不能按零计算，也不能用日志token和未经核验的单价猜本批费用。\n'
detail += '\n## F. 批次路径与完成时间（北京时间）\n\n'
detail += table(['批次', 'Agent结束', '评测/测量结束', '服务器artifact目录名'], [
    ['Agent优先全64台账', '10-12 01:01:34', '10-12 04:58:13', 'agent-first64-20261011T113000Z'],
    ['14超时第二尝试', '10-12 13:19:35', '10-12 13:53:40', 'agent-first64-timeout-retry-20261012T032000Z'],
    ['18题三版本', '不调用模型', '10-12 15:45:26', 'three-versions-batch18-20261012T033600Z'],
    ['3题合格三版本补测', '不调用模型', '10-12 16:30:12', 'three-versions-eligible-20261012T061300Z']])
detail += '\n\n服务器artifact共同前缀：`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/`；通过`ssh lab-server`只读查看。最后3题补测完成后本阶段全部队列结束，不应再用旧PID当仍运行。完整Agent事件、最终消息、patch及环境patch留在各批次`tasks/<项目>/<题号>/`，三版本日志在对应`cases/`或补测`tasks/`。\n'

inputs = [RESULTS / name for name in ('progress.json', 'task-statuses-64.json', 'matched-comparisons.json', 'failure-catalog.json')]
inputs += [HERE / 'report-runtime-evidence.json', REPO / 'experiments/2026-10-11_benchllmrealse-agent-first64/results/summary.json',
           REPO / 'experiments/2026-10-12_benchllmrealse-timeout-retry14/results/summary.json']
statistics = dict(frozen_date='2026-10-12', unique_tasks=64, unique_actual_agent_tasks=63,
                  legacy_reused=21, new_processed=43, new_actual_agent_tasks=42, new_patches=41,
                  new_test_passes=34, new_jmh_passes=18, complete_comparison_tasks=14,
                  matched_scenarios=63, agent_faster_original_scenarios=40,
                  agent_slower_original_scenarios=23, agent_faster_developer_scenarios=30,
                  agent_slower_developer_scenarios=33, task_point_estimate_patterns=dict(groups),
                  validated_raw_jmh_files=len(raw_files), project_table=project_rows,
                  logged_usage_only=known_usage, modes=dict(Counter(r['mode'] for r in flat)),
                  three_version_order_counts=dict(order_counts),
                  three_version_order_counts_by_mode={mode: dict(counts) for mode, counts in order_by_mode.items()},
                  metric_units=dict(Counter(r['unit'] for r in flat)), secondary_metric_keys=secondary_keys,
                  raw_jmh_sha256={str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in raw_files.values()},
                  input_sha256={str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  limitations=progress['limitations'])
documents = {HERE / 'MEETING_REPORT_ZH.md': main, HERE / 'METHODS_AND_ACCOUNTING_ZH.md': methods,
             HERE / 'MEETING_DETAILS_ZH.md': detail,
             RESULTS / 'meeting-statistics.json': json.dumps(statistics, ensure_ascii=False, indent=2) + '\n'}
print('*** Begin Patch')
for path, content in documents.items():
    print('*** Add File: ' + str(path))
    for line in content.splitlines():
        print('+' + line)
print('*** End Patch')
