# 2026-09-17：More-itertools `triplewise` 端到端闭环

## 实验目标

在真实仓库中串联第一版完整流程：

```text
生成并验证 benchmark → 冻结 benchmark → 性能分析 → 生成补丁
→ 功能验证 → 性能测量 → 接受/拒绝 → 反馈下一轮 → 独立标准复测
```

本阶段关注流程是否科学地跑通，不追求多仓库、大样本或最终论文级测量。

## 实验对象

- 仓库：`more-itertools/more-itertools`
- 目标函数：`more_itertools.recipes.triplewise`
- Baseline commit：`b87f67bbbfa488cf56bd86e7b64eb3e8118c34bc`
- Human Fix commit：`7ddf9d26014fa576b8601c6d631d3670668eab06`
- 模型：`deepseek-v4-pro`
- 独立 Run：1 个
- 最大优化轮数：3 轮
- 唯一允许修改：`more_itertools/recipes.py`

## 正确性保护

候选补丁必须通过：

1. 补丁白名单、语法和导入检查；
2. `TriplewiseTests` 定向测试；
3. 完整 `python -m unittest`；
4. 空输入、短输入、列表、生成器、惰性消费等额外行为检查；
5. benchmark 动态目标命中；
6. benchmark 和测试文件哈希不变。

不通过功能检查的候选不会进入性能比较。没有达到性能门槛的候选会被拒绝并回退到当前最佳版本。

## 运行结果

3 轮中共产生 3 个候选：前两个候选通过功能验证并被接受，第三个候选补丁无法应用，被拒绝。完整闭环共调用模型 10 次，使用 135,389 tokens。

冻结结果随后进行了无 LLM、pyperf 标准模式复测：

| 版本 | median | 相对 Baseline | robust RSD | 样本数 |
|---|---:|---:|---:|---:|
| Baseline | 36.09 ms | — | 2.86% | 60 |
| Human Fix | 18.54 ms | 快 48.62% | 5.53% | 60 |
| DeepSeek Fix | 18.20 ms | 快 49.56% | 3.88% | 60 |

Human Fix 和 DeepSeek Fix 相对 Baseline 均有显著提升。两种修复彼此的约 1.8% 数值差异不显著，因此应表述为“DeepSeek 找到了与官方人工修复性能基本相当的方案”。

## 文件说明

- [`config.yaml`](config.yaml)：端到端实验实际配置快照。
- [`benchmark/benchmark.py`](benchmark/benchmark.py)：模型生成并冻结的 benchmark。
- [`benchmark/manifest.json`](benchmark/manifest.json)：benchmark 哈希、workload 与预期输出。
- [`results/REPORT.md`](results/REPORT.md)：标准复测中文报告。
- [`results/summary.json`](results/summary.json)：去除本机绝对路径后的汇总数据。
- [`results/candidates.csv`](results/candidates.csv)：三轮候选与决定。
- [`results/best.patch`](results/best.patch)：最终最佳补丁。
- [`results/environment.json`](results/environment.json)：精简运行环境。

## 结论边界

- 这是一个函数级、单仓库、单个独立 Run 的流程验证。
- 标准复测在个人 macOS 机器运行，不是固定 Linux 服务器上的最终实验。
- 当前 benchmark 的 workload 已经过自动验证和人工检查，但泛化到其他输入分布仍需更多案例。
- 当前没有安全沙箱，只有临时工作区、文件白名单、哈希检查、回退与超时等基础保护。
