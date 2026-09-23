# More-itertools 自主 Workload 闭环 Bad Case

## 实验问题

只提供真实仓库、不指定目标函数和 testcase 时，框架能否自行选择并生成 workload、
定位热点、修改代码并完成正确性和性能闭环？

## 实验流程

```text
扫描仓库测试（150 个候选场景）
→ DeepSeek 选择 PeekableTests
→ DeepSeek 生成 workload，并根据真实错误修复两次
→ Docker 中验证语法、契约、结果和项目代码动态命中
→ profiler 自动选择 peekable.__next__
→ DeepSeek 生成补丁
→ 完整功能测试与性能验收
→ 接受或拒绝并回退
```

模型最终生成的主场景会完整消费一个含 20,000 个元素的 `peekable`，因此
`peekable.__next__` 被高频调用。

## 结果

| 项目 | 结果 |
|---|---:|
| 自动扫描候选场景 | 150 |
| workload 生成/修复轮次 | 3 次尝试后通过 |
| 自动热点 | `more_itertools.more.peekable.__next__` |
| 热点调用次数 | 20,001 |
| 热点 self time | 约 2.775 ms（约 47.9%） |
| Baseline 完整测试 | 815 passed，1 skipped |
| 候选补丁 | 2 |
| 功能正确候选 | 2/2 |
| 接受候选 | 0/2 |
| 候选 1 | 比 Baseline 慢约 3.40%，拒绝 |
| 候选 2 | 比 Baseline 慢约 14.93%，拒绝 |
| 最终版本 | Baseline，未产生有效 `best.patch` |

## 如何理解

这是一个有价值的失败样例：自主链路和安全回退是有效的，但自动选择出的场景未必代表
用户真正遇到的问题，profile 的 Top 1 也未必是存在优化空间的根因。高频调用
`__next__` 是该 workload 的自然结果；两个补丁均变慢，说明框架需要结合 Top N、
调用关系、跨规模趋势和补丁反馈重新选择目标，而不能把 Top 1 固定到底。

本实验选择的是 `PeekableTests`，历史人工性能修复针对的是 `triplewise()`，两者不是
同一个任务，因此不能用“是否找到官方修复函数”评价本次自主选择的对错。

## 证据位置

服务器项目内的原始记录：

- `artifacts/more_itertools_repository_autonomous_e2e/20260923_102459_372669/`
- `artifacts/more_itertools_repository_autonomous_e2e/20260923_102459_372669/optimization/20260923_105019_163333/`
- `logs/more_itertools_repository_autonomous_retry_20260923.log`

## 限制与下一步

- 当前只让模型选择一个 workload，缺少多候选比较。
- 当前主要按 `self time` Top 1 选目标，缺少 callers/callees 和因果证据。
- 连续补丁无提升后应切换 Top N 或 workload。
- 应在具有历史人工修复的多个任务上建立标签，再比较规则、DeepSeek 和 Jev 的选择效果。
