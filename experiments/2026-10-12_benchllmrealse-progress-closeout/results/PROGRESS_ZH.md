# BenchLLMRealSE 实验进度与失败说明

更新：2026-10-12T10:32:14.523822+00:00

## 当前边界

仅继续具备三版本对照资格的无模型补测；其他失败先归档，不再新增付费Agent或盲目重跑。

## 全量覆盖

64题全部处理，63题实际进入过Agent；21题为历史协议复用，43题为新增处理。
新增28次正常结束、14次Agent超时、1题源码拉取超时，41个生产补丁。
首次独立验收：34题功能测试通过、18题正式JMH通过。

## 第二次尝试

{"agent_completed_with_environment_changes": 1, "timeout": 7, "agent_completed": 5, "task_error": 1}
13个工作区验收，7个测试通过；0个JMH通过，包含锁冲突、入口失败等，不能全归为模型问题。

## 三版本对照

已处理18/18题；首次11题完整，合格补测后累计14个不同任务具备完整三版本测量。
合格补测使用首轮冻结补丁，不将第二次Agent尝试替换进来，也不把首次失败证据删除。
只有三个版本均通过功能测试且缺失测量仅因JMH锁冲突的任务进入一次串行补测。

## 失败证据（分阶段，不能把行数当不同任务数）

| 阶段 | 任务 | 版本/环节 | 原因 |
|---|---|---|---|
| 首轮 | kafka/39eb31f |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 首轮 | presto/000fa29 |  benchmark | JMH测量时间上限 |
| 首轮 | kafka/4fa5bdc |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 首轮 | kafka/59a75f4 |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 首轮 | kafka/8dff0b1 |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 首轮 | presto/297b089 |  verify | 测试时间上限 |
| 首轮 | kafka/9bb2f78 |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 首轮 | presto/3a4f2e3 |  verify | 测试时间上限 |
| 首轮 | netty/87ec2f8 |  benchmark | JMH测量时间上限 |
| 首轮 | presto/4e71bf3 |  verify | 测试时间上限 |
| 首轮 | netty/95b8db0 |  benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 首轮 | kafka/c7bc8f7 |  verify | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 首轮 | kafka/c8af740 |  verify | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 首轮 | presto/659c3ee |  verify | 测试时间上限 |
| 首轮 | presto/6908344 |  benchmark | JMH测量时间上限 |
| 首轮 | netty/b72fea3 |  benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 首轮 | kafka/e2e2c62 |  verify | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 首轮 | presto/8abba9e |  verify | 现有功能测试失败，详见断言/异常 |
| 首轮 | kafka/e3ccf20 |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 首轮 | netty/deea51e |  benchmark | JMH测量时间上限 |
| 首轮 | presto/aed4c9a |  benchmark | JMH测量时间上限 |
| 首轮 | presto/b54d248 |  benchmark | JMH测量时间上限 |
| 首轮 | presto/c3cb7a9 |  benchmark | JMH测量时间上限 |
| 首轮 | presto/efd0834 |  benchmark | JMH测量时间上限 |
| Agent补跑后验收 | kafka/4fa5bdc |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| Agent补跑后验收 | kafka/59a75f4 |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| Agent补跑后验收 | kafka/8dff0b1 |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| Agent补跑后验收 | presto/297b089 |  verify | 测试时间上限 |
| Agent补跑后验收 | presto/3a4f2e3 |  verify | 测试时间上限 |
| Agent补跑后验收 | presto/4e71bf3 |  verify | 测试时间上限 |
| Agent补跑后验收 | kafka/c7bc8f7 |  verify | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| Agent补跑后验收 | presto/6908344 |  benchmark | JMH测量时间上限 |
| Agent补跑后验收 | kafka/e2e2c62 |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| Agent补跑后验收 | presto/8abba9e |  verify | 现有功能测试失败，详见断言/异常 |
| Agent补跑后验收 | netty/dd69a81 |  benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |
| Agent补跑后验收 | kafka/e3ccf20 |  benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| Agent补跑后验收 | presto/fdb7611 |  verify | 类初始化异常，源码/环境根因尚未确定 |
| 首轮 | kafka/4fa5bdc |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | kafka/59a75f4 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | kafka/8dff0b1 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | presto/297b089 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | presto/3a4f2e3 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | presto/4e71bf3 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | kafka/c7bc8f7 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | presto/659c3ee |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | presto/6908344 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | kafka/e2e2c62 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | presto/8abba9e |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | netty/dd69a81 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | kafka/e3ccf20 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 首轮 | presto/9e010a7 |  source | 源码下载120秒超时，未调用模型 |
| 首轮 | presto/fdb7611 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 第二次Agent尝试 | kafka/59a75f4 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 第二次Agent尝试 | kafka/8dff0b1 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 第二次Agent尝试 | presto/4e71bf3 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 第二次Agent尝试 | presto/659c3ee |  source | Git源码下载TLS连接异常 |
| 第二次Agent尝试 | kafka/e2e2c62 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 第二次Agent尝试 | presto/8abba9e |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 第二次Agent尝试 | netty/dd69a81 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 第二次Agent尝试 | kafka/e3ccf20 |  agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 三版本对照 | presto/20dcaed | original verify | 功能断言失败：期望null，实际NaN；不修改断言迁就原版 |
| 三版本对照 | presto/290f5be | original benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试（后续无模型补测已解决） |
| 三版本对照 | presto/290f5be | developer benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试（后续无模型补测已解决） |
| 三版本对照 | presto/290f5be | agent benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试（后续无模型补测已解决） |
| 三版本对照 | netty/7b91edd | original benchmark | 原版生产API与共用benchmark访问要求不兼容 |
| 三版本对照 | netty/7b91edd | agent benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |
| 三版本对照 | netty/ab8c4f2 | original benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试（后续无模型补测已解决） |
| 三版本对照 | netty/ab8c4f2 | developer benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试（后续无模型补测已解决） |
| 三版本对照 | netty/ab8c4f2 | agent benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试（后续无模型补测已解决） |
| 三版本对照 | netty/dd69a81 | original benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试（后续无模型补测已解决） |
| 三版本对照 | netty/dd69a81 | developer benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试（后续无模型补测已解决） |
| 三版本对照 | netty/dd69a81 | agent benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试（后续无模型补测已解决） |
| 三版本对照 | presto/8d7f587 | original verify | 功能测试空指针异常；是否由共用修复版fixture引起尚未确定 |
| 三版本对照 | presto/8d7f587 | developer benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |
| 三版本对照 | presto/8d7f587 | agent benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |
| 三版本对照 | netty/e542a2c | original verify | 部分源码回退后API不兼容：internalRefCnt缺失 |
| 三版本对照 | netty/e542a2c | developer benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |

原始日志路径见failure-catalog.json；逐题台账见task-statuses-64.json。

不改测试/断言或额外生产代码迁就原版；不绕过JMH锁保护；不自动充值；首次和补跑数据均保留。
对照一次测量只能报告观察到的加速/退化，不能直接称稳定性能提升。
