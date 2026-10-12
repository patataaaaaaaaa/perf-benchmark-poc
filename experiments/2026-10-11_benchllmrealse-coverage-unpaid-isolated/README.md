# 评测覆盖率：隔离、不付费的公共障碍诊断

## 范围与隔离

2026-10-11 用户授权测试评测环境公共障碍，同时不得干扰另一个 Agent 运行的七题。
本阶段不调用模型，不修改生产源码、测试期望或正在使用的运行器。完整服务器构建
不得与七题正式 JMH 重叠；先在本机运行小型诊断，所需历史依赖只从服务器缓存只读复制。

七题批次：
`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/preparable7-p4-20261011T023531Z`，
启动 PID 2622703。10:39（北京时间）检查处于 Netty/5a9b28a developer evaluation。

## 初始证据

- 48 个准备失败中，20 个 Presto 卡在 git-commit-id-plugin 的浅历史遍历；13 个
  Netty 卡在 assertEquals 重载歧义。其他类别另行记录，不重复付费生成补丁。
- Netty/2791f0f 的旧测试存在 `assertEquals(1L, channel.readOutbound())`，通道读取
  是泛型返回值。历史 POM 含源码级别 1.6/1.7，当前适配器统一强制为8。
- Presto/000fa29 的 root POM 不直接含 git-commit-id-plugin；父 POM 为
  com.facebook.airlift:airbase:98，其 pluginManagement 和 build/plugins 引入
  git-commit-id-plugin:2.1.13。现有 history_plugin_present 只检查项目 POM 文本，
  会漏掉这类继承配置。历史插件 descriptor 的 skip 参数没有命令行 property 绑定，
  因此不能未经验证就假定 `-Dmaven.gitcommitid.skip=true` 生效。

## 验证边界

本机最小复现和旧依赖行为检查，不等同于完整真实任务构建/测试/JMH 通过。
需要记录失败与成功的对照、JDK/依赖版本、命令和原始输出；候选修复仅在本阶段
形成，不直接部署到当前运行中的共享脚本、源码缓存或 Maven 缓存。

## 已完成验证

### Netty：不是通过排除测试解决

本机使用 JDK8 1.8.0_302、原任务冻结生产类 JAR、JUnit4.12 和未经修改的
PendingWriteQueueTest.java。服务器只读复制约数 MB 已有依赖，不在服务器编译。

- 最小泛型/重载对照：source6、source7 编译成功；source8 重现 assertEquals 歧义。
- 真实旧测试：source8 编译失败；source7 编译成功，JUnit 显示 `OK (11 tests)`。
- 未修改测试断言、生产源码或沙箱；未通过排除测试制造成功。

候选方向：Netty 准备阶段去掉人为的 compiler.source/target=8 强制覆盖，让历史
POM 与兼容 JDK 决定源码级别。仍需整题 Maven 构建、目标测试及 JMH 注册验证；
本次11项是已知构建阻碍的真实测试，不是声称本题所有目标测试已完成。

### Presto：继承检测漏检，旧插件行为已复现

只读复制真实任务 root POM 和 airbase98 父 POM：项目 POM 文本检测为 False，
沿父 POM 解析的候选检测为 True。原修复不触发，不代表“加标签”方案已失败。

本机用 git-commit-id-plugin2.1.13 的实际 DescribeCommand（不是现代 git describe
替代品）、对应 JGit3.4.1，构造不含任何 benchmark 答案的浅克隆：

- 没有标签：返回1，复现 Unable to find commits until some tag / Missing commit。
- 仅在当前 HEAD 创建注解标签：返回0，输出 benchllm-prepare。
- 没有增加未来修复提交或生产源码，没有删除插件或改变目标测试。

第一次插件探针漏复制 JodaTime，标签分支报 NoClassDefFoundError；此初次诊断保留
为 `diagnostics/out/results-initial-missing-joda.json`，补齐原插件声明的依赖后再跑。
不能把缺少探针依赖的失败说成真实 Presto 构建失败。

候选方向：离线识别父 POM 继承插件，并在独立原版准备工作区创建仅指向父提交
HEAD 的构建标签。不要拉入未来修复历史；还要验证生成的构建元信息不影响本题语义。

### 候选辅助逻辑

`diagnostics/coverage_fixes.py` 是独立原型，未被活跃运行器导入或部署；父坐标
无法解析/缓存缺失时明确报错，不能静默宣称无插件。这不是完整 Maven effective POM
解析器，复杂属性或 profile 场景需要进一步验证。
3 项单元测试通过：继承检测不改 POM、缺父 POM 明确失败、编译配置不新增测试排除。

## 重现与产物

在本实验目录执行（本地、离线，不连接模型）：

```bash
python3 diagnostics/run_local_probes.py
python3 -m unittest discover -s diagnostics -p test_coverage_fixes.py -v
```

探针需要本机 JDK8，以及 `diagnostics/deps/` 中从旧任务只读复制的依赖；输入SHA256、
完整命令、stdout/stderr 及返回码在 `diagnostics/out/results.json`。原始输出含本机
路径及二进制依赖，按 `.gitignore` 不提交；关键对照、源码和配置保留在本阶段目录。

## 本机阶段结论与下一步（服务器验证前快照）

两个公共障碍都有失败/候选成功的对照，具备进一步验证价值，但新增“整题准备成功”
为0，Agent结果新增为0，不能把13＋20题直接计入已解锁数量。
七题队列在正式JMH期间，本阶段不启动服务器重型构建、不替换共享脚本。
本次没有建立延时任务或恢复监控；后续完整构建需再次执行，不能认为会自动发生。
待七题队列结束后，在独立运行器副本、全新工作区和独立可写构建缓存中，先对
Netty/2791f0f、Presto/000fa29做不付费完整准备，再决定是否扩展到同类任务。

## 2026-10-11 15:58：服务器两个典型题首次独立验证尝试（已停止）

通过 `ssh lab-server` 恢复访问。启动前只读检查确认七题付费队列已退出，且账号下
没有新的已知正式评测进程。该七题全部调用模型，4题正式评测通过、3题JMH失败，
与本阶段无模型验证分开统计。

- 独立批次：`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/coverage-typical-unpaid-20261011T075827Z`
- 首次启动PID：`2798275`；运行器：[`server-validation/isolated_validate.py`](server-validation/isolated_validate.py)
- 首次配置：[`server-validation/initial_config.yaml`](server-validation/initial_config.yaml)；初始状态为复制私有运行器与Maven缓存。
- 单独复制服务器当前 `scripts/`、`src/`，保存Python文件SHA256；不替换共享脚本。
- Maven缓存完整文件复制（约919MB），不使用硬链接或指向共享缓存的可写符号链接。
  Git使用私有bare仓库引用和只读对象alternates；每题仍为仅含fix-parent的浅工作区。
- Netty仅去掉人为source/target=8；Presto识别缓存父POM中的插件，仅在原版HEAD添加
  构建标签。不改生产源码，不排除测试，当前运行器的“排除无关测试”重试在副本中禁用。
- 串行执行：整题准备/编译及JMH注册 → 原有沙箱中的选定测试 → 原版正式JMH。
  JMH保留全部默认参数，2fork/5warmup/10measurement/1秒；30分钟超时不截断参数来冒充成功。
- 单题失败保存阶段、异常、日志并继续下一题；没有 `codex exec` 或模型API请求。

首次尝试在构建前发现：浅Git缓存的mirror clone没有保留旧任务非advertised-ref可达对象，
导致私有仓库不能解析fix-parent，尝试不必要的GitHub补取。只停止本阶段PID2798275及其
3个Git子进程，保留 `setup-stop.json`、日志和缓存，不停止其他任务、不删除产物。
这属于隔离启动器问题，不计为Netty/Presto构建失败。

## 第二次启动及16:03阶段结果

- 当前批次：`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/coverage-typical-unpaid-20261011T080300Z`
- PID：`2799960`（已退出）；配置：[`server-validation/two_task_config.yaml`](server-validation/two_task_config.yaml)。
- 私有Git仓库改为 `git init --bare` 加显式只读object alternates，全部引用/构建缓存仍
  私有；直接读已有历史对象，不再复制浅缓存的advertised refs或补取GitHub提交。
- 本机3项候选辅助测试和2项隔离启动器测试通过，后者验证仅复制代码、不复制凭据或旧产物。

Netty/2791f0f于16:03完成：19个依赖/目标reactor模块全部构建成功（43.315秒），
官方指定两类测试在既有沙箱中9/9通过、0跳过；原版正式JMH产生1行有限正值：
`ScheduleFutureTaskBenchmark.scheduleLots`、num=100000、387.1067 ops/s，
2fork/5warmup/10measurement/1秒。git status为空，HEAD为
`86ff76a4f77662fe1bf61deeec5f3e39e16d4020`，仍为浅工作区，没有新源码补丁、测试排除或构建标签。
这是新增1题原版评测环境验证通过，**不是**新增Agent样本、性能提升或全项目测试通过。

Presto/000fa29的13个reactor模块于16:04全部构建成功（55.024秒），继承Git插件不再报Missing commit。
随后classpath导出失败：Maven退出0但日志为`Skipping plugin execution`，未生成输出文件，
故第二次批次最终为1/2环境验证成功。父airbase98的maven-dependency-plugin配置
`skip=${air.check.skip-dependency}`，该属性通过skip-basic继承被统一skip-all=true开启。
这不是生产代码失败、不是功能测试失败；Presto此轮尚未进入沙箱测试及JMH。
两题全部日志、失败结果和私有缓存保留。不新增模型调用，也不将33个同类任务直接计为恢复。
阶段简表见 [`server-validation/progress.json`](server-validation/progress.json)。

## 16:07：只继续Presto，启用classpath导出

- 新批次：`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/coverage-typical-unpaid-20261011T080738Z`
- PID：`2809454`；配置：[`server-validation/config.yaml`](server-validation/config.yaml)。
- 新运行器/工作区/Maven缓存，缓存从已结束的第二次隔离批次完整文件复制，不写旧缓存。
  不重复已完整验证的Netty，不调用Agent。
- 只在显式`dependency:build-classpath`命令加`-Dair.check.skip-dependency=false`和
  `-Dmdep.skip=false`；准备构建及功能测试命令不变，不关闭任何测试。
  新增1项单元测试确认导出修复不改变构建/测试命令，本阶段辅助测试共6项通过。
- 保留前两次尝试结果；当前只判断Presto原版选定测试和正式JMH是否可完成。

16:09检查：Presto私有新工作区13个reactor模块构建再次通过（16.820秒），classpath
导出实际写出文件，JMH注册通过，已进入沙箱内TestNG选定测试。功能测试和正式JMH
尚未完成，不能提前计为第二题环境验证成功。后台按固定验收步骤继续，不设置模型调用。

## 16:47最终检查：已结束，Presto测量时限不足

PID2809454已退出，第三次批次于16:39结束。Presto构建、classpath与JMH注册通过，
沙箱内官方指定TestNG类 **20项测试通过、0失败、0跳过**。随后原版正式JMH持续测量，
在1800秒墙钟上限被截断，原始结果记为`environment_failed / original_formal_jmh / TimeoutExpired`。

已核对真实官方benchmark源码与注册清单：enableCompression2 × channelCount2 × type15 ×
hasNull2 =120参数组合，`addPage`、`optimizedAddPage`两个方法共240测量案例，每个2fork，
共有480fork实例。截断时日志进度15.63%，JMH预计剩余02:40:08；日志已完成37个案例的
文本结果，没有发现此阶段的异常报错，但`jmh-0.json`为0字节、正式`jmh.json`未生成。
这些部分文本数不能代替完整正式性能结果，也不能算模型失败（本阶段无模型调用）。

两个典型题都通过构建与选定测试；**仅Netty完成原版正式JMH**。新增Agent调用/成绩均为0。
Netty源码级别、Presto父POM Git插件及classpath跳过配置三类公共障碍已有真实任务证据，
仍不能宣称对应33题全部解锁。先前20–40分钟估计没有充分计入官方完整参数网格，偏短。

建议下一步保留全部官方参数及2fork/5warmup/10measurement，按本题测量规模提高外层
JMH超时（例如6小时上限），只补测Presto原版，不重新付费调用模型或重新构建全部题。
这是后续建议：本次检查**没有修改超时或启动新任务**；首次30分钟失败及所有日志继续保留。

查看输出（外网入口）：

```bash
ssh lab-server 'cat /downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/coverage-typical-unpaid-20261011T080738Z/status.txt'
ssh lab-server 'tail -n 30 /downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/coverage-typical-unpaid-20261011T080738Z/runner.log'
```
