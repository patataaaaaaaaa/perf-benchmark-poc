# CPython urllib 自动入口内存闭环

本实验验证完整自动入口：框架只接收固定可信 workload，不预先填写目标函数或目标文件。

```text
多规模 workload
→ 性能分类
→ profiler 路由
→ 自动选择热点函数
→ DeepSeek 生成补丁
→ 功能、内存和运行时间验收
→ 接受或拒绝
```

服务器运行将任务分类为高证据内存型，自动选择 tracemalloc，并从 Top 1 定位
`urllib.parse.unquote_to_bytes`。3 个候选全部功能正确，第 1 轮被接受；后两轮因内存没有
继续下降而被拒绝并回滚。

冻结补丁随后进行了不调用 LLM 的标准复测。DeepSeek Fix 相对 Baseline 的 tracemalloc
峰值下降 95.47%，pyperf 中位运行时间改善 3.02%。本结果只覆盖受控测试切片，不能直接
等同于补丁已经达到 CPython 上游合并标准。

关键文件：

- `config.yaml`：实验配置快照。
- `results/summary.json`：适合汇报的精简数据。
- `results/candidates.csv`：三轮候选和接受决定。
- `results/best.patch`：冻结补丁。
- `results/target_classification.json`：DeepSeek 调用前的多规模分类证据。
- `results/target_profiler_routing.json`：实际参与目标选择的 profiler 路由。
- `results/RETEST_REPORT_ZH.md`：无 LLM 独立标准复测。

完整原始证据保存在本机 `artifacts/cpython_urllib_auto_memory_e2e/20260923_084643_204419/`，
默认不提交 Git。
