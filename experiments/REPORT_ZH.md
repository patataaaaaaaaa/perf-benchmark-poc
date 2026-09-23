# 正式实验汇总

本文只汇总已经整理并提交到 `experiments/` 的正式实验。每个二级标题与一个实验文件夹
严格一一对应；规则调整、排错过程和未形成独立结论的中间验证不在这里展开。

## 2026-09-15_benchmark-generation-feasibility

### 实验问题

DeepSeek 能否针对真实 Python 函数生成可以执行的 pyperf benchmark，并利用真实报错
自动修复？

### 规模与结果

- 项目：SymPy、mpmath。
- 目标函数：10个，每个独立生成3次，共30个候选。
- 初次运行通过：21/30（70.0%）。
- 自动修复后运行通过：29/30（96.7%）。
- 人工确认测试语义正确：28/30（93.3%）。

### 结论

DeepSeek能够生成并修复Python性能测试，但“可以运行”不等于“测对目标”，仍需动态
目标命中和语义复核。

### 归档

[`2026-09-15_benchmark-generation-feasibility/`](2026-09-15_benchmark-generation-feasibility/)

## 2026-09-17_more-itertools-triplewise-e2e

### 实验问题

在给定真实仓库历史任务和可信测试场景后，benchmark生成、代码优化、功能验证、性能
反馈和有限循环能否串成完整闭环？

### 结果

| 版本 | pyperf中位时间 | 相对Baseline |
|---|---:|---:|
| Baseline | 36.09 ms | — |
| 官方人工修复 | 18.54 ms | 提升48.62% |
| DeepSeek修复 | 18.20 ms | 提升49.56% |

DeepSeek修复与人工修复之间的差异不显著，因此准确结论是二者性能基本相当。

### 结论

受控的真实仓库性能优化闭环可行，功能测试、性能门槛、拒绝回退和无LLM复测能够联动。

### 归档

[`2026-09-17_more-itertools-triplewise-e2e/`](2026-09-17_more-itertools-triplewise-e2e/)

## 2026-09-19_docker-sandbox-validation

### 实验问题

workload、测试、benchmark和候选代码能否在具备最小安全边界的Docker环境中执行？

### 结果

- 非root运行：通过。
- DeepSeek密钥隔离：通过。
- 仓库只读挂载：通过。
- 禁止网络访问：通过。
- 超时终止：通过，退出码124。
- 超内存终止：通过，退出码137。

### 结论

沙箱满足当前科研原型的最小隔离要求，但Docker共享宿主机内核，不能据此宣称达到生产级
恶意代码隔离能力。

### 归档

[`2026-09-19_docker-sandbox-validation/`](2026-09-19_docker-sandbox-validation/)

## 2026-09-23_cpython-urllib-auto-memory-e2e

### 实验问题

只提供CPython仓库和可信workload、不配置目标文件或目标函数时，框架能否自动判断性能
类型、选择profiler、定位目标并完成内存优化闭环？

### 结果

- 规则分类：`memory/high`。
- profiler路由：`tracemalloc`。
- 自动目标：`urllib.parse.unquote_to_bytes`。
- 3个候选全部功能正确，第1轮被接受，后两轮因没有继续改善而被拒绝并回滚。
- 无LLM标准复测：DeepSeek修复的峰值内存下降95.47%，运行时间改善3.02%。
- 官方人工修复：峰值内存下降76.78%，运行时间改善30.49%。

### 结论

“给定可信workload、自动寻找修改目标”的入口已经跑通。当前功能门禁覆盖受控任务切片，
尚不能宣称补丁达到CPython上游合并标准。

### 归档

[`2026-09-23_cpython-urllib-auto-memory-e2e/`](2026-09-23_cpython-urllib-auto-memory-e2e/)

## 2026-09-23_more-itertools-autonomous-workload-badcase

### 实验问题

只提供More-itertools仓库，不指定testcase、workload和目标函数时，框架能否自主选择场景、
生成workload、定位热点并找到有效优化？

### 结果

- 扫描出150个候选场景，DeepSeek选择`PeekableTests`。
- workload经过3次生成/修复尝试后通过语法、结果、动态项目代码命中和运行验收。
- profiler将`more_itertools.more.peekable.__next__`选为Top 1。
- 两个候选补丁均通过815项完整测试（另有1项跳过）。
- 两个候选性能分别下降约3.40%和14.93%，均被拒绝；最终保持Baseline。

### 结论

仓库级自主链路和失败回退能够工作，但“可运行的workload”和“耗时Top 1”不一定代表
真实且可优化的性能根因。这是后续改进workload选择和Top N目标决策的正式bad case。

### 归档

[`2026-09-23_more-itertools-autonomous-workload-badcase/`](2026-09-23_more-itertools-autonomous-workload-badcase/)

## 文档边界

- 本文与`experiments/`下五个实验目录一一对应。
- 更细的规则分类校准、attrs workload验证、callback调试和历史任务筛选属于过程证据，见
  [`../EXPERIMENT_EVOLUTION_ZH.md`](../EXPERIMENT_EVOLUTION_ZH.md)。
- 完整模型响应、临时仓库、原始pyperf数据和调试日志保存在忽略提交的`artifacts/`中。
