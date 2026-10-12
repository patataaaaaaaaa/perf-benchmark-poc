# 本周工作汇报：Agent Pipeline接入与Java性能优化评测

汇报日期：2026年10月12日。

## 一、本周完成的工作

本周主要完成了两项工作：一是将Java性能优化实验中的直接LLM补丁生成环节替换为Codex CLI，使Agent能够自主读取项目、修改源码和执行构建测试；二是在BenchLLMRealSE上完成全量任务处理，并获得原版、开发者版和Agent版的性能对照数据。Agent框架采用Codex CLI，底层模型配置为DeepSeek。

Benchmark包含Kafka、Netty、Presto和RoaringBitmap四个项目，共64个真实性能优化任务。全量队列已结束，63个任务实际进入Agent，另1个任务因源码下载失败未进入Agent。在统一配置的对照阶段，14个任务完成了三版本功能测试和性能测量，共获得63组可比较的性能场景。

## 二、最终实验结果

### 1. 全量任务覆盖与完整对照

| 项目 | 任务总数 | 已进入Agent的任务 | 完整三版本对照任务 |
| --- | --- | --- | --- |
| kafka | 16 | 16 | 0 |
| netty | 18 | 18 | 3 |
| presto | 25 | 24 | 11 |
| RoaringBitmap | 5 | 5 | 0 |
| 合计 | 64 | 63 | 14 |

“完整三版本对照”指原版、开发者版和Agent版均完成对应测试与正式JMH，并具有一致的benchmark及参数覆盖。最终对照数据来自Netty3题、Presto11题；Kafka与RoaringBitmap未纳入本次统一配置的完整三版本结果。任务进入Agent仅表示实际尝试，不表示补丁通过验收。

### 2. 性能比较

对14个任务，按benchmark函数及其固定输入参数分别比较性能，共获得63组对照数据。每组包含原版、开发者版和Agent版在相同负载与JMH配置下的分数；63组不是63道任务，也不是将三个版本重复计数。

按三版本的整体性能排序统计，每组只归入以下六种排序中的一种。“＞”表示左侧版本性能优于右侧：平均耗时更低，或吞吐量更高，并非耗时数值更大。

| 三版本性能排序 | 对照组合数 | 占比 |
| --- | --- | --- |
| Agent ＞ 开发者 ＞ 原版 | 16 | 25.4% |
| Agent ＞ 原版 ＞ 开发者 | 5 | 7.9% |
| 开发者 ＞ Agent ＞ 原版 | 19 | 30.2% |
| 开发者 ＞ 原版 ＞ Agent | 8 | 12.7% |
| 原版 ＞ Agent ＞ 开发者 | 9 | 14.3% |
| 原版 ＞ 开发者 ＞ Agent | 6 | 9.5% |
| 合计 | 63 | 100% |

从本轮分数看，Agent在21组中排名第一，开发者版在27组中排名第一，原版在15组中排名第一。排序描述三者的相对位置，具体优化幅度仍需结合各组原始分数与速比判断。

本次有两类性能指标：43组测量平均耗时（`ns/op`、`us/op`、`ms/op`，越低越好），20组测量吞吐量（`ops/s`，越高越好）。统计的是各组内的相对排序，不将不同单位的原始分数相加或平均。原始JMH没有内存、对象分配、GC、CPU利用率等指标；本轮未启用相应的额外采集，不能据此报告这些方面的提升。这里的耗时是代码每次操作的耗时，不是Agent处理任务的用时。

按任务观察：3题的所有已测场景均快于原版，1题的所有场景均慢于原版，10题在不同场景下有快有慢。

代表案例：

- Netty/9abeaf1：3个场景均快于原版，速比为1.0103–1.6037。
- Presto/53aa7f6：单场景速比1.0805，开发者版对应速比1.0478。
- Presto/60a5a5c：2个场景均慢于原版，速比为0.8993–0.9759。

速比大于1表示更快：吞吐量按优化版/原版计算，耗时按原版/优化版计算。当前结果说明Agent已经能够完成部分Java性能优化，但收益具有负载差异，不能将“某个场景加速”视为整题普遍成功。

上述快慢依据本轮JMH分数判断，尚未做独立重复运行的显著性检验。部分几何运算场景出现极大倍率，暂保留为待复核数据，不作为已证实的优化幅度展示。全部逐题结果和原始分数见[详细附录](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/MEETING_DETAILS_ZH.md)。

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
| 哪些题运行过，哪些测试或测量失败 | [详细附录A节](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/MEETING_DETAILS_ZH.md)；机器记录为[task-statuses-64.json](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/task-statuses-64.json) |
| 三版本六种排序，以及按耗时/吞吐分开的计数 | [详细附录B节](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/MEETING_DETAILS_ZH.md)；汇总为[meeting-statistics.json](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/meeting-statistics.json) |
| 某题某个函数/参数下，三版具体是多少 | [详细附录C节](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/MEETING_DETAILS_ZH.md)，按题号查找；统一整理的完整精度数据见[matched-comparisons.json](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/matched-comparisons.json) |
| 每轮测量值、分数误差与置信区间 | 附录C节每题的original/developer/agent链接，打开对应`*-jmh.json`，查看`primaryMetric` |
| 具体失败原因和原始日志在哪里 | [详细附录D节](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/MEETING_DETAILS_ZH.md)与[failure-catalog.json](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/failure-catalog.json)，按题号、阶段和版本找`evidence`路径 |
| Agent执行耗时、token和运行轨迹 | 附录E/F节给出用量与批次路径；完整单次`result.json`和JSONL事件保留在服务器 |
| 模型、时间预算、权限和不同阶段设置 | [方法文档](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/METHODS_AND_ACCOUNTING_ZH.md)、各实验目录的`config.json`及[运行配置核对](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/report-runtime-evidence.json) |
| Agent究竟修改了哪些源码 | 服务器对应任务的`source.patch`、`environment.patch`及工作区；本地归档没有复制所有补丁/测试日志 |

### 2. 示例：查看Netty/9abeaf1

在附录C节搜索`netty/9abeaf1`，可看到三个benchmark函数的三版分数与排序。继续打开[Agent原始JMH](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-netty-9abeaf1/versions/agent-jmh.json)，定位`benchmark`名称末尾为`executeMulti`的记录：`mode=thrpt`、单位`ops/s`、`score≈703131.35`；对应原版约438437.26、开发者版约688511.48，因此该组为Agent ＞ 开发者 ＞ 原版。

`primaryMetric.score`是性能分数，`scoreError`与`scoreConfidence`是JMH报告的误差及区间，`rawData`是各轮测量值。测试是否通过查看[该题三版本状态](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-netty-9abeaf1/summary.json)，测量预算/CPU/预热等查看[该题protocol.json](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-netty-9abeaf1/protocol.json)。

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
