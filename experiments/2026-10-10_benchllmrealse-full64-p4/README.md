# BenchLLMRealSE / PerfOpt 全量固定 P4 实验

## 状态

旧队列 PID 1615827 已停止，原始日志与 30 条基础设施失败记录保留；实际启动 Agent 为 0。
新的补跑队列 PID 1664573 已启动，使用实验专用配置，仍覆盖全部 64 题。
2026-10-10 20:35（北京时间）：全量队列已结束。不付费准备检查已在新目录启动，
PID 2057275，不调用模型。目录是
`failed55-prepare-20261010T123140Z`。旧批次结果保留。
这 9 个确认成功均有正 token 用量、非空补丁、目标测试和正式 JMH 成功记录。
已达到用户要求的至少 3 个成功；临时监控 benchllm-3 已暂停，服务器实验未停止。
启动前查询余额为 110.44 元。这里的“全跑”指全部 64 道题进入队列，不代表
每题必然构建成功、都有补丁或都能获得三类有效性能数据。

## 范围与协议

- RoaringBitmap 5 题、Netty 18 题、Kafka 16 题、Presto 25 题，共 64 题。
- 固定官方 P4 输入与 DeepSeek `deepseek-v4-pro`，每题新建独立 Codex CLI 会话。
- 每题以性能修复提交的完整父提交为起点；只允许修改 metadata 指定的生产源码。
- 已跑过的 5 道 RoaringBitmap 也重新进入本批次，以使用修复后的快速反馈工具。
- Agent 自主决定修改、测试和结束；不添加固定的外层优化循环。
- 正式 JMH：2 forks、5 次预热、10 次测量，每次 1 秒；快速反馈为 `-f 0`，仅供探索。
- 原版、开发者版、Agent 版共用本题冻结测试和 JMH。开发者参考失败原样记录，
  不人工修复参考、不删除失败输入，不因此阻塞 Agent 或下一题。
- Netty/Kafka/Presto 使用官方 JMH 的全部默认参数，不为通过评测而截断输入。
  原版成功测量后冻结结果项集合，其余版本必须覆盖同样的 benchmark/参数组合。
- abdd6ff 与 1de6825 延续补充生产路径 JMH，单独标注，不冒充官方分数。

## 失败隔离与费用

按题顺序执行，四项目有独立的源码缓存。跨项目部分在 RoaringBitmap 之后交错排列。
每题结果写入独立目录，汇总采用临时文件加原子替换，失败不会覆盖前题结果。

构建准备上限通常 30 分钟，源码拉取上限 10 分钟；Agent 上限 15 分钟，目标测试
上限 10 分钟、每个正式参考 JMH 上限 30 分钟。Agent 收尾的测试/性能命令分别
有 30 分钟上限。超时清理对应进程组；普通构建、模型任务、测试或 JMH 失败继续下一题。
基线构建或沙箱正确性工具不可用时，记 `infrastructure_failed`，不花钱生成不可评测补丁。

取消上一试点的 20 元批次阈值，不自动充值。每次付费调用前查询余额；余额不高于
2 元、无法查询余额，或服务返回凭据/计费错误时停止整批。余额门槛是调用之间的
软保护，不是单次调用中的硬费用上限。剩余题可以稍后根据记录继续处理。

## 构建与正确性边界

跨项目新入口已通过 Python 编译和队列单元测试；三项目的历史版本构建成功率还需
由本次真实队列验证，不能预先声称 59 道跨项目题已经可运行。

准备阶段在沙箱外下载依赖、构建原版测试与官方 JMH，记录 classpath/JDK。
测试/JMH 内重新编译本题全部允许源码，当前补丁的类优先于准备时的原版类；
Java 与 Scala 分别使用 javac 和 Scala 编译器。Presto 使用 TestNG，其他项目使用 JUnit。
这沿用已验证的源码 overlay 路线，不等于对每个补丁重建全部仓库和运行全项目测试。
开发者版本也以 metadata 生产源码重编译覆盖冻结基线依赖，因此涉及其他生产文件、
构建配置或依赖变更的参考失败，需要进一步判定是否为评测兼容性问题，不能直接判为
开发者功能缺陷。原版验证同样失败的题不会获得可信的正确性比较。

少数 metadata 指向测试 helper 而非可执行测试，例如 OrcTester，此时扩展为该模块
实际含 `@Test` 的 Test* 类，扩展范围写入 manifest，不把“没有测试”当成通过。
目标测试通过不是完整正确性证明；本轮不另行付费生成额外功能测试。

父提交浅克隆不包含未来修复历史，Agent 提示禁止读取参考提交和其他工作区；当前
沙箱并未完全隐藏服务器上所有可读参考文件，仍有数据泄漏隔离限制。

## 查看输出

当前补跑批次（旧目录仍保留）：

```bash
tail -f /downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/full64-p4-retry-20261010T041500Z/runner.log
```

```bash
cat /downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/full64-p4-retry-20261010T041500Z/status.txt
```

以下为第一次启动的历史目录，不再运行：

在服务器终端执行：

```bash
tail -f /downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/full64-p4-20261010T021000Z/runner.log
```

查看当前进度：

```bash
cat /downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/full64-p4-20261010T021000Z/status.txt
```

原始产物目录包含 `protocol.json`、`summary.json`、`budget.json`、`status.txt`，
每题位于 `tasks/<项目>/<题号>/`，含原版/开发者/Agent 三类结果或明确的失败记录。
建议先在 4–6 小时后查看首批，整批串行处理粗估 1–3 天，复杂历史构建或大量参数
可更久；余额不足可能提前停止。无需保持查看日志的终端在线。

## 启动验证

19 项相关单元测试通过，包括 64 题 manifest、方法级 JMH 路径、计费错误识别、
结果项检查、原子汇总写入、进程树超时清理和既有 Codex/Java/参考失败测试。
服务器端 Python 编译、真实 64 题清单/P4 文件检查通过。之后只做了一次启动状态
确认，不持续轮询实验。

## 零 API 消费定位及补跑

用户发现没有 API 消费后检查：旧队列处理了 30 道题，全部在付费调用前失败。
一项公共原因是启动漏传实验 `CODEX_HOME`，Codex 读到了服务器默认配置，其第 14 行
拼接为 `truemodel_provider`，TOML 解析失败。没有模型请求，不能将 30 条失败计为
Agent 优化失败。其他问题包括 GitHub 拉取/Gradle 下载超时、Netty 依赖模块测试编译
歧义、Presto 的旧 Maven 插件与浅历史兼容问题。

临时指定实验配置目录后，首题原版沙箱内 7 个测试通过，未产生模型费用。
随后按用户授权停止旧队列；日志、工作区、失败记录均未删除，也未修改用户全局配置。

补跑增加显式子进程配置环境及整批无模型配置预检查：共享配置错误直接阻止批次启动，
不再重复跳过全部题。优先顺序调整为 34bce1b、53ba593、1de6825，再继续其他任务。
支持复用旧批次有效的冻结构建产物，但必须新建原版/Agent 源码工作区，不能复用旧补丁。
运行时重新检查构建产物路径，缺失则重新准备。补跑配置见 retry_config.yaml；新增
配置隔离/缓存复用单元测试，相关测试合计 21 项通过。

用户要求确认约 3 个完整成功后再停止监控。因此建立本聊天临时监控，每 5 分钟检查
新批次；需有真实模型 token 用量、有效补丁、目标测试和正式 JMH 全部通过才计成功。
达到 3 个成功后报告并暂停监控，不停止全量实验。队列结束或出现阻断时准确报告，
不能将仅构建完成或失败跳过计为成功。启动时阈值尚未达到；后续达标检查见下。

只读检查脚本 `scripts/inspect_benchllm_batch.py` 统一核验模型用量、测试/正式 JMH
返回码、补丁和结果文件。加入“有 summary 成功但无模型用量”和“构建失败不能计成功”
测试，并验证未写入 summary 的正在运行 Agent 也纳入启动数，相关测试总数为 24。
监控只读取事件日志最多 64KB 的尾部，不重复读取完整模型日志。

### 2026-10-10 13:38（北京时间）连接检查

本次只读 SSH 检查连接 `10.254.12.14:22` 超时，未取得服务器状态。当地路由检查
显示该地址经 `en0` 的默认网关访问；仅凭这些信息不能判定服务器实验结束、失败或
仍在运行，也不能更新成功数量。未重启队列、发起模型请求或改变沙箱权限。
暂保留监控，待后续连接恢复后继续核验；尚未确认满足 3 个成功的停止条件。

### 2026-10-10 15:24（北京时间）恢复连接及监控达标

按用户要求重试后 SSH 恢复。指定补跑批次的只读检查结果为：PID 1664573 存活，
已处理 21/64 题；summary 的 outcome 计数为 succeeded 7、infrastructure_failed 14，
已启动 Agent 为 7，其他题的准备失败未阻塞后续队列。当前状态为
`kafka/9bb2f78: preparing (unpaid)`。

确认成功的任务（括号内为非空 JMH 结果项数）：

- RoaringBitmap：34bce1b（6）、53ba593（4）、1de6825（4）、abdd6ff（4）、b5b4af6（4）。
- Netty：2ed95c9（5）、67d3a78（12）。

上述每题均有真实模型 token 用量、outcome=succeeded、目标测试和正式 JMH 返回码 0、
非空补丁与 JMH 结果，且检查未发现越界修改。1de6825、abdd6ff 仍是协议中标注的补充
生产路径 JMH，不冒充官方原始基准。成功不等于全面功能正确、统计显著加速或所有负载
受益，本次状态检查未分析性能提升幅度或新增功能测试。

准备阶段失败示例包括 Netty/2791f0f 的 Maven 构建返回码 1，以及 Kafka/39eb31f
缺少 gradle/wrapper/gradle-wrapper.properties。这些属于评测基础设施失败，不能计为
Agent 优化失败；本次仅检查，未修改运行中的构建流程或补跑任务。

原始结果保留在服务器：
`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/full64-p4-retry-20261010T041500Z`，
每题位于 `tasks/<项目>/<题号>/`。

已通过应用工具将 benchllm-3 设置为 PAUSED，并读取本地 automation.toml 确认状态。
按约定只停止监控，未向服务器实验进程发送停止信号、未重复启动、未增加模型调用，
也未改变沙箱权限。定时监控不再继续；后续由用户主动要求检查。

### 2026-10-10 16:24（北京时间）接管后的只读检查

阅读本地 README 后，对补跑批次执行 `scripts/inspect_benchllm_batch.py`，并核对
进程命令行、`summary.json` 与 3 道新失败的有界日志。本地代码版本为
`codex/benchllmrealse-agent` 的 `d4aa190`，分支比远端超前 1 个提交，工作区仍有
既有修改和未跟踪文件；本次未提交、未推送、未重置。`config.yaml` 与
`retry_config.yaml` 未改。服务器进程未重启，也没有新增模型调用。

相对 15:24 快照：已处理 21 → 24，基础设施失败 14 → 17，Agent 启动和确认成功仍为 7。
检查脚本的 `other_agent_results` 与 `agents_in_progress` 都为空。当前状态为
`24/64 complete; kafka/aecd47b: original evaluation`。采样时正式 JMH 处于第 2 个
fork 的测量阶段，`benchmark.log` 在 3 秒内从 14656 字节增至 14740 字节，子进程为
Java。该采样只说明当时在推进，不代表这道原版评测已经结束。

3 道新的准备失败都是 `agent_started=false`，不能计为 Agent 解题失败：

| 分类 | 任务 | 证据 |
| --- | --- | --- |
| Gradle 包不完整 | Kafka 9bb2f78 | 07:13:55–08:18:01 UTC。`BadZipFile`。`tools/gradle-8.1.1-bin.zip` 正好 62914560 字节，有 ZIP 本地头、无中央目录，`gradle-8.1.1/bin/gradle` 不存在。官方 HEAD 的 Content-Length 为 124643981。 |
| 浅历史与插件冲突 | Presto 3a4f2e3 | 约 64 秒。`presto-spi` 上 git-commit-id-plugin 2.1.13：Missing commit `b2a5e7031212d876518b214617f5e7ff75e5d7d6`。 |
| 原版测试编译失败 | Netty 83a19d5 | 约 31 秒。`PendingWriteQueueTest` 的 `assertEquals` 在 long 与 Object 重载之间歧义；`-DskipTests` 仍编译测试。 |

后两类与此前 Presto `000fa29、239f726、290f5be` 和 Netty `2791f0f、687308b`
是同一类适配器问题。Gradle 8.1.1 与此前 Kafka `4fa5bdc、8dff0b1` 的 5.6.2
同属下载后 ZIP 无法解析；本次重新看到 5.6.2 压缩包仍正好 41943040 字节且未解压。
`tools/gradle-6.6-bin.zip` 现为 11337728 字节且没有已解压的 `bin/gradle`，本次没有
把它对应到某条失败记录。Python 对 8.1.1 是在下载调用返回后才报 `BadZipFile`，
因此收到的响应体在官方长度之前结束；具体是哪一层提前关闭连接，这次没有定位。

原始证据仍在上述批次目录。紧凑检查结果另存
`snapshots/20261010T082428Z.json`。现有全量队列继续运行。下载完整性、Presto
浅历史和 Netty 测试编译这三处都还没有改代码。

### 2026-10-10 16:39（北京时间）再次只读检查

完成数仍是 24/64，确认成功仍是 7，基础设施失败仍是 17。状态变为
`24/64 complete; kafka/aecd47b: P4 agent/evaluation`，`agent_runs_started` 从 7
变为 8。`run_benchllm_codex.py` 与 `codex exec` 都在运行。事件日志约 119KB，
采样时最后修改约 52 秒前；尾部是已结束的命令：Gradle checkstyle、读取
`clients/src/main/java/org/apache/kafka/common/utils/Checksums.java`、javac。
这道题还没有 `result.json`，不能计为第 8 个成功。队列未重启。快照见
`snapshots/20261010T083927Z.json`。

### 2026-10-10 17:22（北京时间）进度检查

完成数 24 → 30。确认成功 7 → 9，新增 Kafka `aecd47b`（12 条正式 JMH）和 Netty
`8a8337e`（4 条）。两次都有正 token 用量。`agent_runs_started` 为 9，没有正在运行的
Agent。基础设施失败 17 → 21，新增且都发生在付费调用前：

| 分类 | 任务 | 证据 |
| --- | --- | --- |
| 旧版 FindBugs 插件配置无法解析 | Presto 3f63ade、46d219f | 各约 3 秒。findbugs-maven-plugin 2.5.2 的 `pluginArtifacts` 配置解析失败。 |
| 原版测试编译失败 | Netty 87ec2f8 | 约 10 秒。仍是 `PendingWriteQueueTest` 的 `assertEquals` 重载歧义。 |
| 沙箱内 Mockito 无法自附加 | Kafka b25c96a | 约 24 秒。原版沙箱验证报 `Could not self-attach to current VM`，Agent 未启动。 |

当前 Kafka `b36e3c2` 的 wrapper 指向 Gradle 6.6。主进程无子进程，正把
`tools/gradle-6.6-bin.zip` 写到约 13.1 MB；3 秒内增加 64 KB。状态文件和
`runner.log` 已约 15 分钟没变，原因是下载发生在 Python 进程内，克隆之后还没有
新的构建日志。队列未重启。快照见 `snapshots/20261010T092247Z.json`。

### 2026-10-10 18:26（北京时间）本地适配器修改

18:18 前后只读看到完成数已到 48/64，成功仍是 9，基础设施失败 39。Kafka `b36e3c2`
随后以 `BadZipFile` 结束。新增失败仍落在已有类别：GitHub 拉取失败、Gradle 包不完整
或下载超时、Presto 的 `git-commit-id-plugin` / FindBugs、Netty 的
`PendingWriteQueueTest`、Kafka 缺少 wrapper，以及 Kafka `cfc34ca` 的 Scala
后缀运算符。Kafka `e3ccf20` 当时尚未完成，其父提交声明 Gradle 5.6.2。

尚未完成的题用的是同一套准备代码。能读到父提交的 Kafka `e3ccf20` 需要 Gradle 5.6.2。
其余 Kafka、Netty 和 12 道 Presto 的父提交还没拉到本地，指定测试都不是
`PendingWriteQueueTest`。因此 Gradle 校验、拉取重试、Maven 插件跳过和无关测试排除
会同样作用于它们。Netty `7b91edd` 的基准调用原版私有方法，这次没有改。

本地改动在 `scripts/run_benchllm_full_batch.py` 和 `scripts/benchllm_project_tools.py`：

- Gradle 发行包必须是完整 ZIP，中断后续传，最多 3 次。
- 没有 wrapper 文件时从 `build.gradle` 的 `gradleVersion` 读取版本。
- 源码拉取失败重试 3 次。
- Maven 准备增加 `-Dfindbugs.skip=true`。含 `git-commit-id-plugin` 时只在准备用的父提交上打本地 tag `benchllm-prepare`，不拉取修复提交。
- 编译失败若只发生在非本题测试上，临时排除那些测试并重试一次；本题指定测试失败则不排除。
- 沙箱测试若 classpath 里有 `byte-buddy-agent`，用 `-javaagent` 预加载，避免 Mockito 自附加。
- 重编译 Scala 时加上 `-language:postfixOps`。

相关单元测试 23 项通过。这些修改还在本机，服务器队列没有重启，也没有把新脚本部署上去。

### 2026-10-10 20:13（北京时间）全量队列结束

PID 1664573 已不在。`status.txt` 为 `complete_with_failures; 64/64 processed`，
约 55 分钟前写入。`summary.json` 有 64 条：`succeeded` 9，`infrastructure_failed` 55。
`agent_started` 为 9，没有第 10 次 Agent。日志末尾是 Presto `fdb7611` 准备失败后的
`TASK_FAILED_CONTINUING`，不是余额或凭据中断。

55 个准备失败按日志归类：GitHub 拉取 23，Presto 浅历史 RevWalk 10，Netty
`PendingWriteQueueTest` 编译歧义 8，Gradle 无效压缩包 5，缺少 wrapper 3，
FindBugs 插件 2，沙箱验证 2（Mockito 自附加、Scala 后缀运算符各 1），Gradle
下载超时 1，Netty `7b91edd` 基准接口 1。这些都发生在付费调用前。成功题仍是
RoaringBitmap 全部 5 题、Kafka `aecd47b`、Netty `2ed95c9`、`67d3a78`、`8a8337e`。

### 2026-10-10 20:35（北京时间）55 题不付费准备

已把本地适配器部署到服务器，并用 `--prepare-failed-summary` 启动新批次
`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/failed55-prepare-20261010T123140Z`。
进程只做准备和沙箱测试，命令行没有 Agent 脚本。第一次启动后 Netty `2791f0f`
的重试 POM 出现重复 `<profiles>`，已改为插入现有 `<profiles>` 并重启这次检查。
重启时 Kafka `39eb31f` 的半成品工作区被拒绝，该题记为准备失败。

启动后的前三条记录仍是准备失败：Netty `2791f0f` 排除 `PendingWriteQueueTest`
后，`ByteToMessageCodecTest` 仍编译失败；Presto `000fa29` 的本地 tag 没有阻止
`git-commit-id-plugin` 继续向浅历史之外查找。当前正在处理 Kafka `4fa5bdc`。
这批检查会继续跑完 55 题，不会因此停掉。

### 2026-10-10 22:43（北京时间）55 题准备结束

状态为 `prepare_complete; 7/55 preparable; 55 checked`。进程 `2057275` 已退出。
没有模型调用。7 题可准备：Netty `5a9b28a`，Kafka `922a95a`、`b25c96a`、`b36e3c2`、
`c05403f`、`cfc34ca`、`eb24ed8`。48 题未通过准备，分类见
`results/prepare55-classification.md`。其中 8 题是运行器或适配器问题，不能写成题目不可构建。

已完成付费队列里，模型实际启动 9 次，9 次评测成功，0 次是调用后测试或 JMH 失败。
以后调用了模型但测试或 JMH 失败的题记为 Agent 失败尝试，成功率和尝试数分开报。
这 7 题的正式三版本分数还没有跑。付费补跑尚未开始。
