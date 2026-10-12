# 剩余51题：独立环境补跑、已有补丁复测及固定P4实验

## 目标与实际历史状态

2026-10-11用户授权大批量重跑失败任务，扩大有效实验样本；不能将调用前的基础设施失败
算为模型能力失败，也不能只报告成功子集。服务器外网入口现在使用`ssh lab-server`。

启动前从三个历史summary验证64题互斥分区：

- 13题已完成Agent评测：原全量队列9题＋七题补跑4题，不重新生成或测量。
  “Agent评测完成”不等于所有参考版本必然成功、功能全面正确或一定加速。
- 48题调用模型前仍准备失败：重新进行不付费准备，通过后再进入正式评测/Agent队列。
- 3题已调用模型、选定测试通过，但正式JMH失败：Kafka922a95a、b36e3c2、eb24ed8。
  复用其现有agent.patch与用量记录，绝不重新付费生成。

此前归因已列出全部48题的阶段/原因；实际典型验证只有Netty2791f0f和Presto000fa29，
不是“每个类别都测过”。前者完整原版评测通过，后者构建/20测试通过但240案例的JMH在
30分钟被截断。本批将已有证据的修复推广验证，尚未确认全部同类题可恢复。

## 批次与流程

- 批次：`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/failed51-retry-20261011T090459Z`
- 启动PID：`2834321`；本地运行器[`retry_failed.py`](retry_failed.py)，状态检查器[`inspect_retry.py`](inspect_retry.py)。
- 入口启动为nohup后台任务，SSH断开不主动终止；没有新增监控自动化。

1. 独立复制服务器代码、Maven/Gradle/工具缓存，私有Git引用及原版浅工作区；只读共享Git对象。
2. 先对全部48题完成不付费准备：历史构建、JMH注册、原沙箱内选定测试、工作区完整性。
   每题成功/失败都保留并继续；只有准备通过的题才进入下一阶段。
3. 对准备通过的题及3个已有补丁，串行进行原版及开发者版正式测试/JMH。
   原版失败即记为参考/评测失败，跳过开发者及模型；两参考都成功才进入下一步。
4. 对48题中的可评测任务调用CodexCLI＋DeepSeek deepseek-v4-pro，官方P4，900秒自主优化，
   新工作区/新会话，不设置外层优化循环。Agent产物、用量、补丁、测试及正式JMH各自保存。
5. 对3个已有补丁，只在全新fix-parent工作区验证并应用原patch，检查允许路径后复测。
   旧用量单独关联，新模型用量为0。若参考仍失败，保留旧补丁但不冒充已有可比较性能。

队列优先准备通过的Netty，再复测3个已有Kafka补丁，然后新Kafka，长时间Presto最后。
这个顺序可能使部分大测量任务等待较久；每个阶段有有限超时，普通单题失败不终止后续。

## 环境修复与测量约束

- Netty：去掉适配器强制的compiler.source/target=8，让历史POM决定源码级别，仍使用兼容JDK8。
- Presto：沿缓存父POM识别Git插件，在原版HEAD创建构建标签，不拉入未来开发者历史。
- classpath：仅在dependency:build-classpath显式启用air.check.skip-dependency=false及mdep.skip=false，
  防止父POM跳过检查连导出也跳过。正常构建与测试命令不变。
- 不新增测试排除、不改测试断言、不人为修复生产代码、不修改共享运行器或沙箱权限。
- 使用官方benchmark案例，但测量协议为我们自定的2fork、5warmup、10measurement、每次1秒，
  保留案例默认负载参数；不删失败行。2026-10-11核对更正：官方Netty/Presto/Kafka脚本为
  1fork、10warmup、50measurement，当前不能称为完全复现官方测量协议。
  仅将正式测量墙钟上限从1800秒改为21600秒（6小时），超时结果记录为不完整，不是有效性能数。
- 测试600秒；历史构建1800秒；下载/历史获取使用已有有限重试。三版本结果集合与原版一致才可比较。
- baseline构建是相关模块＋依赖reactor，之后使用已冻结类路径重新编译题目允许源码并执行选定测试，
  不是每个patch全项目clean rebuild，也不是完整项目测试套件。

## 费用与停止条件

新Agent最多48次，只在全部48题无付费准备记完、且本题两个参考正式评测均成功后自动调用。
初期没有模型API请求是预期状态，不是队列异常。每次调用前读余额，保留2元，余额不可读取或
不足则停止付费阶段；凭据/计费错误同样停止，不自动充值，不重复启动模型。
余额门槛是调用间保护，不是单次请求或总费用硬上限。
凭据只在付费阶段按配置变量名读入内存，不复制到新批次，不输出密钥，不执行secrets.env中的shell。

## 记录与汇总

原始记录全在独立批次：

- protocol.json、runner-snapshot-sha256.json：冻结范围/配置及运行器hash。
- prepare-summary.json：全部48题环境结果；tasks/仓库/题号/prepare-result.json和错误日志。
- evaluation-queue.json、evaluation-summary.json：正式参考与Agent/复用补丁结果。
- tasks/仓库/题号/{original,developer,prompt4,replayed-agent}/：三版本各自日志与JMH JSON。
- budget.json、status.txt、completion.json或queue-error.json：费用保护、进度及最终状态。

阶段结论在本目录、experiments/README.md和REPORT_ZH.md更新，不在仓库根目录新建报告。
同时报告处理数、准备覆盖率、模型正用量调用数、选定测试通过数、完整JMH数和三版本可比较数。
调用前失败、参考失败、调用后失败分开；未测量/部分文本数据不填成0分，也不计加速。

相关本机测试：新批次6项＋隔离启动器3项通过；既有候选辅助逻辑3项此前通过。
当前只确认后台启动，尚未报告48题准备覆盖率或新Agent成绩。完整批次可能跨天甚至数天，
建议先在2–4小时后检查准备进度；无需持续读取完整日志。

17:07启动核对：PID2834321存活，私有缓存复制及无模型沙箱配置预检查已通过，
状态`unpaid_prepare 0/48; netty/2791f0f`。进入首题实际准备，尚未有新模型请求/成绩；
不是“51题已经跑完”。启动快照见[`results/startup.json`](results/startup.json)。

17:08检查：2/48已记完，Netty2791f0f准备通过；Kafka39eb31f构建失败已记录并继续
Presto000fa29，证明普通任务失败没有阻塞队列。此Kafka旧工作区冲突已消除，当前新障碍
是Gradle3.5历史Bintray插件源的SHA1下载返回非预期内容，涉及grgit1.9.2、versions0.14.0、
shadow1.2.4。保留原因，不将其算为模型失败，也未在运行队列中临时修改生产代码或关闭测试。
快照见[`results/progress-20261011T090844Z.json`](results/progress-20261011T090844Z.json)。

18:44检查：48题全部完成无付费准备，24准备通过、24仍基础设施失败。正式队列为24个
准备通过的新任务＋3个旧patch，共27题；已经完成3题，均有正token用量、Agent选定测试
返回0、正式JMH返回0和非空结果：Netty2791f0f（1行）、687308b（6行）、83a19d5（10行）。
这3题的原版与开发者版也均正式评测成功，可进入三版本比较；没有据此提前宣称加速。
当前Netty95b8db0正在原版JMH，日志刚更新，PID2834321存活、无整批错误。旧patch尚未复测。
累计已有16题Agent评测通过（历史13＋本轮3），仍不等同全部功能正确或所有负载性能提升。
快照见[`results/progress-20261011T104422Z.json`](results/progress-20261011T104422Z.json)。

18:53检查：正式队列已处理4/27，其中3成功、1参考失败（Netty95b8db0开发者版缺JCTools类，
未调用模型）。第5题b2eaab0两参考通过、P4 Agent运行中；22题等待。原队列正常存活。
24个准备失败逐题核对后分为11种首个阻塞，其中aed4c9a的1项测试失败尚无断言详情，不能
将全部失败都解释成已确定的环境问题。详情及建议修复见[FAILURE_ANALYSIS_ZH.md](FAILURE_ANALYSIS_ZH.md)，
完整27题清单及快照已保存。本轮只读诊断，没有修改运行中队列或触发额外付费请求。

随后对照官方脚本，确认原版构造、项目原生测试入口、依赖路径与JMH配置均存在差异。
大量失败不能一概归因于benchmark本身；当前实际重写了评测适配层，而不只是替换模型调用。
详见[官方路线核对](OFFICIAL_PIPELINE_AUDIT_ZH.md)。此次只读核对，没有停队列、改参数或新增请求。

19:06为次日组会整理已有数据：前三题非空patch、验证/JMH返回0，17行三版本原始分数已
核对并保存，不只选择收益最大的行。2791f0f本轮吞吐483.36/960.23/1815.58ops/s；83a19d5
有收益也有退化，均为自定义协议下探索性观察，未做同官方协议复现/显著性结论。
当前27题已处理6题：4成功/2参考失败，feb804d Agent运行中；本次整理没有新增请求或改队列。

```bash
ssh lab-server 'python3 /downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/failed51-retry-20261011T090459Z/inputs/inspect_retry.py --batch-dir /downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/failed51-retry-20261011T090459Z'
```

19:16之后按用户止损要求停止此旧队列及其Kafka/b36e3c2参考测量子进程；没有中断付费Agent。
保留8条已完成记录，其中5条新增Agent评测成功，操作证据见服务器本批次operator-stop.json。
后续改为[全量Agent优先尝试](../2026-10-11_benchllmrealse-agent-first64/)，本批次不再运行。
