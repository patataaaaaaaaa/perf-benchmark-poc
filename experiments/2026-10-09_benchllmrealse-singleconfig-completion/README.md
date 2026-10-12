# BenchLLMRealSE 单配置补齐实验（已结束，部分失败）

协议冻结日期：2026-10-09；批次已于北京时间 20:06:26 结束，状态为 complete_with_failures。

后续状态：已定位 topK 参考实现的功能回归，并于北京时间 21:07:28 启动单题补跑，PID 1364410。新批次为 `roaring-abdd6ff-retry-20261009T130643Z`，已于 21:20:05 结束；Agent 通过目标 JUnit 与四项正式补充 JMH，开发者参考失败被保留，所以批次状态仍为 complete_with_failures。

## 本次状态检查

- 原后台 PID 1335034 已退出，没有继续运行模型。
- abdd6ff：原版评测通过；开发者对照版在补充 JMH 初始化时由 BitSliceIndexBase.topK 抛出 `RuntimeException: bugs found when compute topK`。控制器将该题归为 infrastructure_failed 并跳过，其 Agent 尚未启动。异常的进一步归因尚未完成，不能将其计为 Agent 优化失败。
- 1de6825/P4：已完成 Agent、目标 JUnit 和完整补充 JMH，结果 succeeded。Agent 用时 341.96 秒；只修改 Node16.java。此状态不代表全面功能正确性，补丁语义尚未进行额外复核。
- 实际只启动一个 Agent 任务，而不是两个任务都成功。一个 Agent 内部可有多次 API 请求。
- 检查时余额 111.67 元，相对启动的 112.38 元下降 0.71 元；这不是根据逐调用账单核算的成本。
- budget.json 是“下一次启动之前”的快照，仍记 agent_runs_started=0，不是最终调用总数；最终实际任务数依据 summary.json 与 prompt4/result.json 确认。
- 本次状态检查没有修改评测器、重跑补丁或发起新的模型调用。

## topK 归因与补跑（2026-10-09）

独立诊断已复现，不是 API 或服务器故障：开发者提交将“先收集待删元素，再统一删除”改为 `F.remove(i.next())`，即边遍历边从同一 MutableRoaringBitmap 删除。在数组容器中，删除会移动后续元素，而迭代器继续前进，导致漏删。

- 四个与补充 JMH 相同的全相同值输入：原版全部通过；开发者版 count=1000、k=20/200 均抛出 topK 数量异常；count=10000 的两项通过。
- 最小删除序列：1000 个元素目标留下 20 个，按该删除方式最后留下 499 个，只删除 501 个，仍有 479 个待删。这是原有迭代器与外部删除组合的行为，开发者 topK 优化引入了这种组合。
- 上游新增删除测试使用 RoaringBitmap，而真实修改路径使用 MutableRoaringBitmap；原有 topK 测试使用不同的递增值，未覆盖本次大量并列值的数组容器场景。
- 诊断使用当前源码优先的 classpath；开发者提交生产代码仅修改 BitSliceIndexBase，未发现必须同时加载其他生产文件的修改，不能用“混入旧依赖”解释该异常。

源码见 [validation/TopKProbe.java](validation/TopKProbe.java)，诊断输出见 [results/topk_diagnosis.json](results/topk_diagnosis.json)。没有人工修补开发者版本，也没有删除失败用例或换成只会通过的数据。

评测器新增显式 `--continue-on-developer-failure` 开关：记录开发者对照失败及失败阶段，继续启动 Agent。原版失败仍禁止模型启动；Agent 仍须通过原项目目标测试和完整四项补充 JMH，没有放宽其验收门槛。默认行为不变，该开关仅在已定位参考失败的本次补跑中启用。新增参考评测单元测试与原接口测试合计 10 项通过。

补跑只运行 abdd6ff/P4，一次 Agent，单次上限 900 秒，不运行新的外层优化循环、不重跑已完成的 1de6825。复用原批次冻结的 harness 与测试依赖，在新目录重测三类版本，旧结果不覆盖。余额预留线仍为 92.38 元，与本次起始 111.67 元之间相差 19.29 元；金额阈值只在调用间检查，不是单次调用硬上限。

预计补跑从启动起约 15–25 分钟，无持续监控。查看新批次：

```bash
cat /downloads/patataWJY/benchllm-agent-eval/perf-benchmark-poc/artifacts/benchllmrealse/roaring-abdd6ff-retry-20261009T130643Z/status.txt
tail -f /downloads/patataWJY/benchllm-agent-eval/perf-benchmark-poc/artifacts/benchllmrealse/roaring-abdd6ff-retry-20261009T130643Z/launcher.log
```

补跑配置快照见 retry_config.yaml。开发者参考仍失败，即使 Agent 成功，批次仍显示 complete_with_failures；应分别阅读参考版本与 Agent 的结果，不能把总体状态等同于 Agent 失败。结果见 [results/topk_retry_summary.json](results/topk_retry_summary.json)，候选补丁见 [results/abdd6ff_prompt4.patch](results/abdd6ff_prompt4.patch)。功能正确性仍只覆盖已运行的测试和这些 JMH 初始化断言，未证明所有 topK 场景正确。

## 快速性能工具的沙箱修复

Agent 请求本身成功，但其 quick JMH 曾出现 `java.net.SocketException: Operation not permitted`。原因是 JMH 的 fork 控制需要绑定本地 ServerSocket，而原生 Agent 沙箱禁止此操作。这和 topK 参考代码回归是两个不同问题。

- 只将 quick 模式改为 `-f 0`，在当前 JVM 中运行，不放开沙箱网络或扩大权限。
- 正式 benchmark 仍为 `-f 2`、5 次预热、10 次测量，验收用例和结果完整性检查不变。
- quick 输出明确注明只用于调试和探索；非 fork 分数不能当作正式性能结论。结果目录增加 measurement_protocol.json，记录 quick/final、fork 数及工具修订版本。
- 本地 13 项测试通过；正式评测结束后，使用相同 Codex `:workspace` 沙箱，在原版 topK 工作区实测 quick，全部四个用例完成，退出码 0。未调用模型，也没有更改候选源码或污染原版工作区。
- 工具修订名为 socket-free-v2。本次 Agent 在修复之前已经结束推理，因此本次补丁不能宣称受益于新版快速性能反馈；也不能把本次当成工具全程可用的 P4 组参与严格配置消融。后续运行才统一使用新版。

工具修复部署到服务器，不启动第二个 Agent；旧失败事件、正式性能结果与开发者参考失败均保留。该工具问题也提示此前四配置批次的 P3/P4 不能默认视为获得了有效的性能反馈，进一步配置比较需按实际调用结果审核。

## 实验问题与范围

暂不扩大四种配置的组合实验，先以固定 P4 补齐上一批因余额停止而未完成的两道 RoaringBitmap 任务：

- abdd6ff：BitSliceIndexBase 的 topK 值移除路径。
- 1de6825：Node16 的子键读取；此前有单题试运行，但其官方 JMH 没有直接调用修改后的生产方法，本次不算全新的历史任务。

这不是五道新题，也不是跨项目实验。数据集中 RoaringBitmap 只有五题；其余 netty、kafka、presto 的评测适配尚未完成，本次未启动这些项目的模型调用。

## 为什么先用一种配置

上一批只有少数任务，每种配置各生成一次，而且 P3/P4 同时开放快速性能工具，因此既不能证明配置等价，也不能作严格的纯 Prompt 因果比较。

本批目标是补齐任务覆盖和生产路径测量，而不是回答哪个 Prompt 最优。选择 P4 是因为它提供问题描述、源码/测试与官方 JMH 文本，并允许 Agent 自主调用正确性与快速性能工具，不是因为它已被证明最好。

后续若研究配置差异，应独立设计消融实验，控制工具权限、使用相同任务并重复生成。当前不增加人为外层优化循环。

## 实际配置与评测

- Agent：Codex CLI；模型：deepseek-v4-pro。
- 每题一次 P4，最多两次模型运行，单次 Agent 超时 900 秒。
- 每题独立 parent-only Git 工作区；保留源码修改白名单。
- 比较原版、开发者版、Agent 版；先验证目标 JUnit，再运行 JMH。
- JMH：5 次预热、10 次测量、2 个 fork，每次 1 秒。
- abdd6ff 使用 BSITopKProductionBenchmark，1de6825 使用 Node16ProductionBenchmark。这是补充生产路径测量，不是原始官方 JMH 分数；使用同一补充测试比较三类代码。
- 本次没有自动对每个新补丁运行上一批的专项诊断，也不将目标 JUnit 通过称为全面功能正确性。完成后需要结合补丁复核。

## 启动与预算

- 服务器进程 PID：1335034。
- 启动：2026-10-09 19:51:47（北京时间）。
- 实验目录：`artifacts/benchllmrealse/roaring-singleconfig-20261009-nextbatch/`（服务器项目下）。
- 启动时余额 112.38 元，保留线 92.38 元，批次余额下降阈值 20 元。
- 检查发生在下一次 Agent 启动之前，不是单次调用过程中的硬金额上限，最后一次运行可能越过阈值；余额查询失败则停止继续启动模型。
- 实验独立后台运行，SSH 断开不会直接终止它；未设置持续监控或定时唤醒。
- 从启动起预计约 30–50 分钟，依赖/运行故障可能改变完成时间。

本地接口单元测试通过（6 项）。启动时进程存活；结束后的结果见上方“本次状态检查”。

## 查看进度

登录服务器后：

```bash
cat /downloads/patataWJY/benchllm-agent-eval/perf-benchmark-poc/artifacts/benchllmrealse/roaring-singleconfig-20261009-nextbatch/status.txt
tail -f /downloads/patataWJY/benchllm-agent-eval/perf-benchmark-poc/artifacts/benchllmrealse/roaring-singleconfig-20261009-nextbatch/launcher.log
```

launcher.log 主要显示阶段和命令。模型启动后，每题的 prompt4.runner.log 及 prompt4/codex_events.jsonl 保存更细的输出；summary.json 在运行完成后逐项更新。

配置快照见 config.yaml；原始数据和工作区继续保存在服务器 artifacts/ 中，后续只归档关键结果与补丁。
