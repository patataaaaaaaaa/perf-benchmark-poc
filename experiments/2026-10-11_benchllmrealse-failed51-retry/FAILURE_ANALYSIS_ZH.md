# 27题正式队列进度与24题准备失败归因

检查时间：2026-10-11 18:53:42（北京时间）。只读检查，没有修改服务器队列、权限、源码或触发额外模型请求。

批次：`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/failed51-retry-20261011T090459Z`，PID 2834321 存活，无 queue-error。

## 正式评测队列

27题 = 24个新准备通过的题 + 3个待复测旧patch。已处理4题：3成功、1参考版测试失败；第5题正在Agent阶段，22题等待。前三题有正token用量。运行中第5题不计为完整成功。

| 序号 | 项目 | 题号 | 状态（18:53） |
|---:|---|---|---|
| 1 | netty | 2791f0f | 三版本选定测试/正式JMH通过，Agent有正用量 |
| 2 | netty | 687308b | 三版本选定测试/正式JMH通过，Agent有正用量 |
| 3 | netty | 83a19d5 | 三版本选定测试/正式JMH通过，Agent有正用量 |
| 4 | netty | 95b8db0 | 开发者测试缺JCTools类；原版JMH4行；未调用Agent |
| 5 | netty | b2eaab0 | 原版/开发者正式评测通过，P4 Agent运行中 |
| 6 | netty | b72fea3 | 等待 |
| 7 | netty | feb804d | 等待 |
| 8 | kafka | 922a95a | 等待；复用旧patch，不新增模型调用 |
| 9 | kafka | b36e3c2 | 等待；复用旧patch，不新增模型调用 |
| 10 | kafka | eb24ed8 | 等待；复用旧patch，不新增模型调用 |
| 11 | presto | 000fa29 | 等待 |
| 12 | presto | 20dcaed | 等待 |
| 13 | presto | 239f726 | 等待 |
| 14 | presto | 290f5be | 等待 |
| 15 | presto | 53aa7f6 | 等待 |
| 16 | presto | 60a5a5c | 等待 |
| 17 | presto | 6908344 | 等待 |
| 18 | presto | 8abba9e | 等待 |
| 19 | presto | 8d7f587 | 等待 |
| 20 | presto | a26f440 | 等待 |
| 21 | presto | b54d248 | 等待 |
| 22 | presto | bfb18d6 | 等待 |
| 23 | presto | c3cb7a9 | 等待 |
| 24 | presto | ee74e4b | 等待 |
| 25 | presto | efd0834 | 等待 |
| 26 | presto | fa655f6 | 等待 |
| 27 | presto | fdb7611 | 等待 |

95b8db0不是模型失败：开发者版4/14测试因缺少org/jctools/queues/SpscLinkedQueue失败；本题没有启动Agent。
这与准备失败的6个Netty案例属于同类依赖适配障碍，需另批恢复，不计入下表24题。
已成功的3题分别有1、6、10行Agent正式JMH，不据此宣布加速或全面正确。

## 24个准备失败任务

这24题全部没有调用模型，不计模型错误。共11种当前阻塞（按每题首个阻塞归类），其中1题仅知道测试失败、根因未确定。
修好第一个阻塞后可能暴露后续问题，所以下列数量不是承诺能立即新增的有效样本数。

| 类别 | 数量 | 题号 | 已确认日志证据 | 建议修复（尚未验证） |
|---|---:|---|---|---|
| Netty 未重打包的 JCTools 依赖缺失 | 6 | netty: 87ec2f8 9abeaf1 ab8c4f2 dd69a81 deea51e e542a2c | org/jctools/queues/SpscLinkedQueue 不存在。87ec2f8、9abeaf1 的 common JAR 只有 io/netty/util/internal/shaded/org/jctools/...；classpath 同时放入未经 shade 的 common/target/classes，且没有 jctools-core.jar。 | 按本题历史 common 模块的编译依赖导出完整 classpath，加入对应版本的未重打包 JCTools；统一三版本，不随意换最新版。先验证一例后覆盖同类。 |
| Presto TestNG 与跨模块监听器不兼容 | 3 | presto: 297b089 3a4f2e3 4e71bf3 | NoClassDefFoundError: org/testng/IClassListener。三题使用 testng-6.9.6.jar（没有该接口），但全部 reactor target 目录被放入运行路径，presto-main/target/test-classes/META-INF/services/org.testng.ITestNGListener 加载 LogTestDurationListener。 | 限制测试运行路径为本题选定模块及必要依赖，不引入无关模块的测试目录和服务监听器；保留正确的历史测试版本。若仍不兼容，再核对历史模块实际 runner 配置。 |
| Kafka 沙箱拒绝创建 socket | 3 | kafka: 4fa5bdc e2e2c62 e3ccf20 | AclAuthorizerTest 需要本机服务；出现 java.net.SocketException: Operation not permitted 及清理时连带 NullPointerException。 | 保持 Agent 原沙箱；考虑把既有测试放在独立外部评测容器的隔离网络中执行，仅容许本机测试服务。必须显式设计并验证，不直接给 Agent 全网络/全权限，也不删相关测试。 |
| 旧 FindBugs 与 Maven 参数注入不兼容 | 2 | presto: 3f63ade 46d219f | findbugs-maven-plugin:2.5.2 配置 pluginArtifacts 失败，UnmodifiableRandomAccessList 不能赋给 ArrayList；skip 标志没有阻止插件初始化。 | 先验证兼容的历史 Maven；必要时仅在环境准备配置中禁用静态分析插件的执行，不能禁用功能测试，保留补丁与命令记录。 |
| 历史插件仓库返回非 SHA1 内容 | 2 | kafka: 39eb31f c7bc8f7 | Gradle3.5 从 dl.bintray.com 取 grgit1.9.2 / versions0.14.0 / shadow1.2.4，SHA1 下载解析报 For input string: <ht。 | 配置可用的依赖镜像或离线缓存，保持原插件坐标/版本，校验文件与校验和，不把插件升级当作等价修复。 |
| Git 获取缺失对象 | 2 | presto: 659c3ee 9e010a7 | fetch: fatal: bad object；remote did not send all necessary objects，同时有 Could not read 对象。尚未确定缺失位于本地缓存、shallow/alternates 还是远端。 | 使用独立干净 bare 仓库获取确切 fix 及 parent，检查对象完整性，避开已有不完整引用；不改共享仓库，不向 Agent 暴露未来修复历史。 |
| JMH 源码与原版 API 不兼容 | 2 | kafka/netty: kafka/8dff0b1 netty/7b91edd | Kafka AclAuthorizerBenchmark 引用原版没有的 ResourceOrdering；Netty GetIpV6ByNameBenchmark 访问 private getIPv6ByName。 | 逐题做仅限 harness 的兼容适配，验证三版本操作/输入语义相同并明确披露；不能把开发者生产修复塞入原版。无法等价适配的保留为不可评测。 |
| Gradle 版本识别器不支持变量声明 | 1 | kafka: 59a75f4 | 识别器仅匹配 gradleVersion='数字'，历史 build.gradle 使用 $versions.gradle；gradle/dependencies.gradle 实际声明 gradle: 5.6.2。 | 扩展版本解析读取 dependencies.gradle 的明确数字值，验证后固定 Gradle5.6.2，不猜测或统一使用新 Gradle。 |
| Gradle 分发包下载超时 | 1 | kafka: c8af740 | URLError: urlopen error timed out，未进入项目构建；历史 wrapper 声明 Gradle8.7。 | 独立预下载对应分发包，有限重试/镜像，校验与 wrapper 一致后进入私有缓存。 |
| Kafka JMH 模块缺少 Connect 依赖 | 1 | kafka: 9bb2f78 | ReplaceFieldBenchmark 编译找不到 org.apache.kafka.connect.source.SourceRecord 和 org.apache.kafka.connect.transforms.ReplaceField。 | 核对该历史版本 jmh-benchmarks 的依赖图，把 connect:api/transforms 的同版本输出加入 harness 的编译和运行路径；仅适配评测依赖，不改生产实现。 |
| Presto 选定测试失败，缺少断言详情 | 1 | presto: aed4c9a | TestGeometrySerde 总计8项，1项失败，0跳过；当前日志只有汇总。TestNG XML 报告位于 TemporaryDirectory，退出后被删除。 | 先修复报告留存，将测试名称、断言、异常栈落盘，然后隔离复现；当前不能判断是原版行为问题、依赖差异或适配问题，不能跳过断言冒充通过。 |

## 建议次序与实验边界

1. 当前27题继续按冻结配置运行，不在其中热修改适配器。普通单题失败继续后续任务。
2. 下一独立无付费准备批次先处理classpath/测试目录污染：6个Netty＋3个Presto，以及新增参考失败Netty95b8db0。然后补Gradle版本识别和模块依赖。
3. 下载/历史插件镜像、Git对象完整性、旧FindBugs分别以一例验证后覆盖同类。socket所需评测隔离环境单独设计，不放宽Agent权限。
4. 两个API不兼容题必须证明harness语义等价；aed4c9a先保留完整测试报告。不能为提高覆盖率改生产功能、删断言或省略JMH默认参数。
5. 修复需记录适配器版本、依赖版本/校验和及三版本一致性。环境预检和原版/开发者正式评测通过后才进入新的Agent调用。

原始证据：本批次support/项目/题号/{prepare.log,sandbox-verify.log,fetch.log}及tasks/netty/95b8db0/developer/verification.log。
快照：results/progress-and-failures-20261011T105342Z.json。当前修复办法均为建议，未在本检查轮执行或宣称验证成功。

