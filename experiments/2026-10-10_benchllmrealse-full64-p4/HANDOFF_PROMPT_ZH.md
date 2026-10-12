# BenchLLMRealSE 全量 Agent 实验交接提示词

你是这个项目的实验监工，请接管已有实验的状态检查、失败定位、结果归档和阶段总结。先读本提示词及指定实验 README，再只读检查服务器；不要因为接管就重新启动实验。以下进度是交接前的快照，不是实时状态。

## 1. 研究目标与当前范围

我们研究 coding agent 在真实 Java 项目中的性能优化能力。基于 BenchLLMRealSE / PerfOpt：
https://github.com/icetlab/BenchLLMRealSE

当前队列是全部 64 道 PerfOpt 任务：RoaringBitmap 5、Netty 18、Kafka 16、Presto 25。
固定官方 P4 Prompt，通过 Codex CLI 调用 DeepSeek `deepseek-v4-pro`。不是直接调用 LLM
返回 diff，也不是使用 OpenAI 模型。Agent 在独立 Git 工作区里自主修改生产代码、调用
测试和快速 JMH；外部评测器再独立验收。没有固定的外层三轮优化循环。

每题比较三种代码：Original（真实修复的父提交）、Developer（真实修复提交）、Agent
（从 Original 开始修改）。不新增直接 LLM baseline，不扩展四 Prompt 组合，不跑 SCAT。
目标是尽可能获得全量任务的可解释结果；“全跑”不代表允许把不可构建的题伪装成成功。

## 2. 服务器与工作区

SSH 不是网站，服务器是实验室内网地址：

```bash
ssh patataWJY@10.254.12.14
```

需要实验室内网或可访问该内网的 VPN。优先使用已有 SSH 密钥，不索取或打印密钥。
若连接超时，只能说明当前连接失败，不能声称服务器实验停止。不要立即重启任务。

本地仓库：
`/Users/aha-yue/Documents/ChatGPT/New project/perf-benchmark-poc`

服务器实验根目录：
`/downloads/patataWJY/benchllm-agent-eval`

服务器代码仓库：
`/downloads/patataWJY/benchllm-agent-eval/perf-benchmark-poc`

服务器 benchmark 仓库：
`/downloads/patataWJY/benchllm-agent-eval/BenchLLMRealSE`

当前且唯一应首先检查的批次：
`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/full64-p4-retry-20261010T041500Z`

启动主进程 PID：`1664573`。检查存活还要确认命令行属于这个批次，不能只看 PID 存在。
旧批次 `full64-p4-20261010T021000Z` 的主进程已经停止，旧记录保留，不能把旧成果加到
新批次成功数中。

实验 Codex：`/downloads/patataWJY/.local/bin/codex`，交接前版本 0.161.0。
实验专用 `CODEX_HOME`：`/downloads/patataWJY/benchllm-agent-eval/codex-home`。
凭据文件：`/downloads/patataWJY/benchllm-agent-eval/secrets.env`。
只允许被已有启动流程安全加载，不要输出其内容、环境变量全集、请求 Authorization。
不要修改服务器用户全局 `.codex/config.toml` 或擅自升级 CLI、模型和依赖。

## 3. 第一次接管的检查命令

优先只执行下面一次 SSH；这个脚本只读且会核验结果，不要先读大量模型日志：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 patataWJY@10.254.12.14 \
  'python3 /downloads/patataWJY/benchllm-agent-eval/perf-benchmark-poc/scripts/inspect_benchllm_batch.py --batch-dir /downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/full64-p4-retry-20261010T041500Z'
```

重点读取 `status`、`queue_alive`、`processed_tasks`、`agent_runs_started`、
`confirmed_successes`、`successes` 和当前事件类型。

交接前快照：已处理 21/64，7 个 Agent 成功，14 个 infrastructure_failed。
7 个成功：RoaringBitmap `34bce1b、53ba593、1de6825、abdd6ff、b5b4af6`；Netty
`2ed95c9、67d3a78`。它们都有真实 token、补丁、目标测试和正式 JMH 成功记录。

2026-10-10 16:02（北京时间）检查时，第 22 题 Kafka/9bb2f78 正在下载 Gradle 8.1.1。
约 48 MB 的下载文件当时仍更新，主进程存活；不是已有 Agent 正在推理。安装包路径：
`/downloads/patataWJY/benchllm-agent-eval/tools/gradle-8.1.1-bin.zip`。
慢下载时题数可能长时间不变，应结合文件大小/mtime、进程及网络状态判断，不能仅据
status 不变就断言卡死。当前 Python 下载的 60 秒 timeout 不等于整次下载的总时间上限。

原临时监控 `benchllm-3` 已因达到至少 3 个成功而 PAUSED；只暂停了监控，没有停止
服务器队列。不要自动恢复它或新建高频监控。如果用户要求定时监控，使用产品正式
自动化机制，正常无变化时保持安静；不要用持续轮询耗费大量 token。

## 4. 已确认的 14 个失败，需作为定位起点

以下均发生在付费 Agent 调用前，不能计为 Agent 解题失败：

| 原因 | 任务 | 已确认的证据 |
| --- | --- | --- |
| GitHub 网络失败（5） | Presto 20dcaed、297b089；Netty 5a9b28a；Kafka 59a75f4、922a95a | fetch.log：3 个连接超时，2 个 TLS 异常中断 |
| Gradle 包无效（2） | Kafka 4fa5bdc、8dff0b1 | 都需要 5.6.2；约 40 MiB ZIP 头文件无法解析，BadZipFile |
| 浅历史与插件冲突（3） | Presto 000fa29、239f726、290f5be | git-commit-id-plugin 2.1.13 沿历史找 tag，Missing commit |
| 原版测试编译失败（2） | Netty 2791f0f、687308b | PendingWriteQueueTest 的 assertEquals 重载歧义；skipTests 仍编译测试 |
| wrapper 路径假设错误（1） | Kafka 39eb31f | 旧版本无 wrapper properties，但 build.gradle 声明 gradleVersion 3.5 |
| 原版/JMH 接口不兼容（1） | Netty 7b91edd | 补入修复提交的 GetIpV6ByNameBenchmark 后，它调用原版私有 getIPv6ByName，编译失败 |

这些包含我们适配器的不足，不要全部归咎于 benchmark 或模型。应保留“网络问题”、
“构建兼容问题”、“基准接口问题”等细分类。其他历史批次出现过不同旧插件问题，
但不能未经本批次日志核对就混入这 14 个的原因。

## 5. 遇到失败如何处理

1. 先定位所属阶段：源码获取、依赖/构建、原版预检查、参考评测、Agent、最终测试、JMH。
2. 读取本题 `task-result.json`、`infrastructure-error.log` 和对应 support 的日志。
   优先错误段及有界尾部；不重复拉取完整模型事件文件，不泄露凭据。
3. 普通单题失败按现有队列继续后面的任务，不要因为一题失败停止全量；但共享配置、
   凭据/计费故障、队列进程退出要及时报告。进程活着但长期无活动，要调查而非报正常。
4. 默认监工权限是检查、定位和记录。修改代码、停止/重启队列、新增付费补跑前，
   向用户说明具体对象、方案、测量影响及费用，并获得相应授权。不要直接重跑全部64。
5. 若获准修复：先做不付费的构建/原版测试/JMH 注册检查，再验证补跑可评测；补跑
   只针对授权任务，使用新批次目录，保留旧失败记录和完整尝试关系。
6. 修复适配器不能篡改题目答案：不能删掉失败测试/参数、修改测试期望、偷用开发者补丁，
   或把 Original 改成 Developer。任何必要 harness 兼容改动需说明，并对三个版本一致应用。
7. 保持 Agent 可写文件范围、沙箱权限和性能协议。不因构建困难直接改成无沙箱。
8. 不自动充值，不重新启动重复队列；用户此前已授权的全量队列继续执行即可。

构建缓存和源码准备可在沙箱外，但 Agent 不能看参考答案。已有提示禁止参考读取，
当前服务器参考目录并未完全物理隔离，这是实验限制。修复 Presto 浅历史时尤其不要
把未来修复历史暴露给 Agent 的原版工作区。

## 6. 判定结果与费用边界

“已处理”包括准备失败；“启动 Agent”必须有模型请求证据；“完成评测”必须至少有：
正 token 用量、outcome=succeeded、非空合法补丁、verification.returncode=0、
benchmark.returncode=0、有效非空 JMH 结果。不要只凭 CLI 最后一句话或退出码判断。

这仍然不等于全面正确或性能提升。要报告“加速”，必须解析 JMH 指标方向、单位、
参数及三版本的可比较数据；吞吐率越大越好，耗时越小越好。不要把编译通过、测试
通过、JMH 能跑、性能显著改善混为一个指标。

当前测试是 metadata 相关测试及必要扩展，不是完整项目测试套件。评测采取冻结基线
classpath＋重编译本题允许生产源码的 overlay，不是每个补丁完整重建仓库。
正式 JMH 固定 2 forks、5 warmup、10 measurement、每次1秒；快速 JMH 为 f0、1/2轮，
只供 Agent 探索，不能用它代替正式结果。官方默认参数不截断，结果项覆盖要一致。
RoaringBitmap 1de6825、abdd6ff 使用补充生产路径 JMH，必须单独标注。
Agent 成功也不保证 Original/Developer 参考评测全成功，汇总时要另核对 references。

当前准备失败14题没有模型费用，但已经运行的7题有费用；无须保持 SSH 终端在线。
启动前余额110.44元只是历史值，不是当前余额。当前队列调用间保留2元余额，不设旧的
20元整批上限；这是调用间软保护，不是单次请求硬上限。不要擅自改预算或模型。

## 7. 实现入口（读代码再作决定）

本地仓库下：

- `scripts/run_benchllm_full_batch.py`：64题排队、构建准备、参考评测、费用保护、失败隔离。
- `scripts/inspect_benchllm_batch.py`：只读紧凑状态与成功核验。
- `scripts/start_benchllm_full_batch.sh`：已有固定批次启动器，不要盲目再次执行。
- `scripts/run_benchllm_codex.py`、`src/benchllmrealse/codex_cli.py`：加载官方任务/P4，启动 Agent，提取补丁，最终验收。
- `scripts/benchllm_project_tools.py`、`scripts/benchllm_full_classpath.gradle`：Kafka/Netty/Presto 编译、测试、JMH 适配。
- `scripts/run_roaringbitmap_batch.py`、`scripts/benchllm_java_tools.py`：RoaringBitmap 准备及评测。
- `src/benchllmrealse/process.py`：带超时的进程组隔离与清理。

交接前相关测试共24项通过，但不等于所有历史版本构建适配通过。仓库分支
`codex/benchllmrealse-agent`，ahead 1，存在修改和未跟踪文件；这些是现有工作。
先检查 Git 状态，不要 reset、覆盖、清理或丢失文件，不自动 commit/push。

## 8. 数据和过程文件如何落盘

服务器原始数据保留在当前批次目录内：

```text
full64-p4-retry-20261010T041500Z/
├── protocol.json / summary.json / budget.json / status.txt / runner.log
├── support/<项目>/<题号>/        构建、测试、classpath、harness信息
├── workspaces/                  三版本独立工作区
└── tasks/<项目>/<题号>/
    ├── task-result.json 或 infrastructure-error.log
    ├── original/                原版评测
    ├── developer/               开发者参考评测
    └── prompt4/                 Agent事件、用量、agent.patch、result.json、测试和JMH
```

并非每题都有全部文件，缺失时记录原因，不补造空“成功”。禁止把不同任务或批次互相覆盖。

本地本阶段记录统一落在已有目录：
`/Users/aha-yue/Documents/ChatGPT/New project/perf-benchmark-poc/experiments/2026-10-10_benchllmrealse-full64-p4/`

先读并更新其中 README.md；config.yaml 和 retry_config.yaml 是既有配置证据，不覆盖
历史值。需要新检查快照可放 `snapshots/<UTC时间戳>.json`；需要修复过程可增加
`FAILURE_ANALYSIS_ZH.md` 或有日期的小节；阶段汇总可放 `results/`。记录北京时间的
阅读时间、UTC批次时间、batch路径、代码/配置版本和原始证据路径，区分观察与推测。
不要每次无变化检查都创建一份新报告，也不要在项目根目录乱放实验报告。

只有真正新的一阶段/新协议才创建：
`experiments/YYYY-MM-DD_benchllmrealse-<范围>-<配置>-<目的>/`。
例如 `2026-10-11_benchllmrealse-failed14-p4-buildfix/`，仅作为命名示例，不预先执行。
日期按北京时间，名称用 ASCII、小写、连字符；同一批次的连续观察留在同一文件夹。
新建阶段后更新 `experiments/README.md` 索引；重要结论同步 `experiments/REPORT_ZH.md`，
保留原有历史叙述，不把失败记录删除或改写成从未发生。

## 9. 如何总结实验

给用户的进度要简短，至少区分：总数64、已处理、准备失败、Agent启动/成功/失败、
当前任务阶段、进程是否真实存活，以及是否需要用户处理。无明显变化不持续刷状态。

阶段结束时输出：

- 覆盖率和失败原因统计：基础设施失败、模型/超时失败、测试失败、JMH失败分别统计。
- 可比较三版本任务数，以及模型真实请求数/用量/费用（费用需核实来源，不凭token猜）。
- 每个成功题的 Original/Developer/Agent 性能、参数、单位和指标方向；补充JMH单列。
- 独立功能正确性和测量可靠性限制。已有单测不足以证明缓存失效、混合负载等正确性。
- 失败补跑与原尝试关系、harness修改、配置差异、未解决问题、可复现命令及产物位置。

作者 Analysis 的归一化、代表性分数、Wilcoxon/A12、定性策略分析目前未完整接入，
不能声称已经完成论文复现。不要仅用7个可构建题推广所有64题的能力；也不要把14个
不可评测题直接记为模型错误。报告全量覆盖与可评测子集，并明确选择偏差。

先给我一次新的实际检查结果，说明当前运行是否正常、进展是否比交接快照变化，以及
接下来最值得解决的问题。除了已有全量队列继续运行，不要因为这份交接提示词自行
新增付费实验、调整研究范围、重启队列或对外发送消息。
