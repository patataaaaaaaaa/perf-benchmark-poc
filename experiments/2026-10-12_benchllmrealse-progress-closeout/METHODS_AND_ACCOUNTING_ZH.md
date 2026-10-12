# 评测方法与批次统计口径（备查）

统计冻结：2026-10-12，包含当天16:30完成的最后一批补测。数据来自实际运行台账和本地保存的原始JMH JSON；本次整理没有新增模型调用或实验。

## 1. 文件用途

供复核模型配置、执行参数、批次差异及统计分母；面向组会的汇报正文见[组会报告](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/MEETING_REPORT_ZH.md)。本文保留过程口径，不作为开场讲稿。

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

| 项目 | 题数 | 累计进入Agent | 历史复用 | 新进入Agent | 新生产补丁 | 新测试通过 | 新JMH通过 | 完整三版 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kafka | 16 | 16 | 7 | 9 | 9 | 6 | 0 | 0 |
| netty | 18 | 18 | 9 | 9 | 9 | 9 | 5 | 3 |
| presto | 25 | 24 | 0 | 24 | 23 | 19 | 13 | 11 |
| RoaringBitmap | 5 | 5 | 5 | 0 | 0 | 0 | 0 | 0 |
| 合计 | 64 | 63 | 21 | 42 | 41 | 34 | 18 | 14 |

“新”列仅指最新Agent优先批次。历史21题为18个旧协议`succeeded`、3个旧协议`benchmark_failed`；旧版采用完整parent/overlay及预热5、测量10、fork2等设置，未在新协议重新评测，不能与新18题相加发布统一成功率。Kafka的新正式测量没有通过，RoaringBitmap本轮全部是历史复用；最终对照只有Netty3题和Presto11题，存在样本选择偏差。

### 14题超时补跑，单独统计

14题第二尝试：13实际进入Agent，6会话正常结束，7再次超时，1下载TLS失败；12生产补丁、7独立测试通过，正式JMH新增通过0。JMH失败中有入口和锁等执行障碍，不能全部当模型答错。补跑没有增加不同题数量，也没有替换首轮对照补丁；不会自动第三次调用Agent。

首轮14次超时中13次留下补丁，7题测试通过，Netty/dd69a81及Presto/fdb7611两题正式JMH也通过。**会话超时不等于没有成果；正常结束也不等于通过验收。**

## 6. 三版本性能对照结果

统一定义速比：吞吐量用`Variant / Original`，耗时用`Original / Variant`。大于1表示该场景点估计更快，小于1更慢；Agent与Developer比较用两者对Original速比之比。

63场景中：Agent快于Original **40/63（63.5%）**、慢于Original **23/63**；快于Developer **30/63（47.6%）**、慢于Developer **33/63**。按任务看，3题所有场景点估计更快、1题全部更慢、10题快慢混合，不定义“某题只要一行快就算成功”。29个场景的Agent/Original速比落在0.95–1.05，仅描述接近1，不是显著性判断阈值。

| 任务 | 场景 | Agent快于原版 | Agent快于开发者 | Agent/原版速比范围 | 开发者/原版速比范围 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| netty/9abeaf1 | 3 | 3 | 2 | 1.0103–1.6037 | 0.9700–1.5704 | 一次点估计 |
| netty/ab8c4f2 | 5 | 3 | 0 | 0.9883–5.1320 | 1.0016–9.7122 | 一次点估计 |
| netty/dd69a81 | 2 | 1 | 0 | 0.9891–1.0020 | 0.9965–1.6754 | 一次点估计 |
| presto/239f726 | 8 | 6 | 5 | 0.8153–1088 | 0.8843–1394 | 极大倍率待复核 |
| presto/290f5be | 5 | 3 | 2 | 0.9956–1.0204 | 0.9842–1.0170 | 一次点估计 |
| presto/3f63ade | 2 | 1 | 1 | 0.9954–6.0939 | 0.9760–8.6006 | 一次点估计 |
| presto/46d219f | 4 | 3 | 1 | 0.8934–9.2547 | 0.9509–9.2862 | 一次点估计 |
| presto/53aa7f6 | 1 | 1 | 1 | 1.0805–1.0805 | 1.0478–1.0478 | 一次点估计 |
| presto/60a5a5c | 2 | 0 | 1 | 0.8993–0.9759 | 0.8943–1.0044 | 一次点估计 |
| presto/a26f440 | 11 | 4 | 6 | 0.9417–8.4104 | 0.8495–11.1511 | 一次点估计 |
| presto/bfb18d6 | 7 | 6 | 4 | 0.9637–1.574e+06 | 0.9893–2.198e+05 | 极大倍率待复核 |
| presto/ee74e4b | 6 | 3 | 4 | 0.9650–68.6669 | 0.8994–68.7343 | 一次点估计 |
| presto/fa655f6 | 6 | 5 | 3 | 0.9941–1.1559 | 0.9557–1.1640 | 一次点估计 |
| presto/fdb7611 | 1 | 1 | 0 | 1.0360–1.0360 | 1.0918–1.0918 | 一次点估计 |

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

- [详细附录：64题台账、63场景原始分数与逐阶段失败](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/MEETING_DETAILS_ZH.md)。
- [机器可读汇总与输入文件哈希](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/meeting-statistics.json)；[64题原始台账](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/task-statuses-64.json)；[14题对照数据](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/matched-comparisons.json)；[失败日志位置](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/failure-catalog.json)。
- [只读核对的CLI/硬件/provider配置证据](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/report-runtime-evidence.json)。服务器benchmark副本没有`.git`，不能提供未经记录的源码版本指纹；已有[官方路线审计](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-11_benchllmrealse-failed51-retry/OFFICIAL_PIPELINE_AUDIT_ZH.md)包含相关脚本哈希。
- 实现入口：[Agent批调度](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/scripts/run_benchllm_agent_first.py)、[CLI进程封装](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/src/benchllmrealse/codex_cli.py)、[原生测试/JMH](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/scripts/benchllm_native.py)、[三版本一致性与比较](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/scripts/run_benchllm_three_versions.py)、[合格补测](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/scripts/remeasure_eligible_comparisons.py)。
- 所有过程文件按`experiments/YYYY-MM-DD_阶段/`归档；完整工作区/Agent轨迹/测试日志留在服务器`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/`。本次仅整理，不修改生产补丁或测试，不充值、不启动新实验、不commit/push。
