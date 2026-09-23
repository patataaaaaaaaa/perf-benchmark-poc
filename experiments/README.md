# 实验归档说明

这个目录保存适合 Git 提交、代码审查和阶段汇报的精简实验材料。完整的模型响应、临时 workspace 和所有运行日志仍保存在本机 `artifacts/` 中，不直接提交到仓库。

正式实验文稿见 [`REPORT_ZH.md`](REPORT_ZH.md)。其中每个二级标题与本目录下的一个
实验文件夹严格一一对应。框架开发过程中的中间验证统一记录在仓库根目录的
[`EXPERIMENT_EVOLUTION_ZH.md`](../EXPERIMENT_EVOLUTION_ZH.md)，不再混作正式实验目录。

## 命名规则

```text
YYYY-MM-DD_项目或阶段_目标或实验目的
```

例如：

- `2026-09-15_benchmark-generation-feasibility`
- `2026-09-17_more-itertools-triplewise-e2e`

日期表示实验完成或冻结的日期，后半段说明实验对象和目的。若同一天存在多个版本，可以在末尾增加 `_v2`，不要只使用没有语义的时间戳。

## `experiments/` 和 `artifacts/` 的区别

| 目录 | 用途 | 是否提交 Git |
|---|---|:---:|
| `experiments/` | 关键配置、benchmark、补丁、汇总结果、中文报告 | 是 |
| `artifacts/` | 模型原始响应、每次命令日志、临时 workspace、完整调试证据 | 否 |

## 每个实验建议包含

```text
实验目录/
├── README.md          # 问题、设计、结论和限制
├── config.yaml        # 当时实际使用的配置快照
├── benchmark/         # 冻结 benchmark 与说明
└── results/           # 汇总结果、候选表和最终补丁
```

只有确实需要复核的内容才进入归档。不要提交 `.env`、API 密钥、虚拟环境、仓库完整副本、缓存以及带有个人路径的原始日志。

## 当前归档

| 日期 | 实验 | 核心问题 |
|---|---|---|
| 2026-09-15 | [benchmark 生成可行性](2026-09-15_benchmark-generation-feasibility/) | LLM 能否生成并自动修复 pyperf 测试？ |
| 2026-09-17 | [More-itertools 端到端闭环](2026-09-17_more-itertools-triplewise-e2e/) | 生成测试、修改代码、功能验证和性能反馈能否串成闭环？ |
| 2026-09-19 | [Docker 基础沙箱验证](2026-09-19_docker-sandbox-validation/) | 陌生代码能否在断网、非 root、只读和资源受限的容器中执行？ |
| 2026-09-23 | [CPython urllib 自动内存闭环](2026-09-23_cpython-urllib-auto-memory-e2e/) | 不人工指定函数时，分类、profiler、DeepSeek 优化和验收能否完整串联？ |
| 2026-09-23 | [More-itertools 自主 Workload Bad Case](2026-09-23_more-itertools-autonomous-workload-badcase/) | 只给仓库时，自动选择 workload 和 Top 1 是否足以找到有效优化？ |
