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
| 2026-10-09 | [BenchLLMRealSE Codex / RoaringBitmap 小批量实验](2026-10-09_benchllmrealse-codex-roaringbitmap-batch/) | 单个 Agent 能否完成 Java 性能优化，四种输入/工具配置下的结果与开发者实现有何差异？ |
| 2026-10-09 | [BenchLLMRealSE 固定 P4 补齐实验（参考版本失败）](2026-10-09_benchllmrealse-singleconfig-completion/) | Node16/P4 与补跑的 topK/P4 均完成目标测试和补充 JMH；topK 开发者对照存在回归。快速 JMH 沙箱问题已在运行后修复。 |
| 2026-10-10 | [BenchLLMRealSE 全量 64 题 / 固定 P4](2026-10-10_benchllmrealse-full64-p4/) | 64 题已处理。Agent 实际调用 9 次且 9 次评测成功；55 题在调用前失败。 |
| 2026-10-11 | [7 题付费 P4 补跑](2026-10-11_benchllmrealse-preparable7-p4/) | 7 题都调用了模型。评测成功 4，JMH 失败尝试 3。 |
| 2026-10-11 | [评测覆盖率：隔离、不付费诊断](2026-10-11_benchllmrealse-coverage-unpaid-isolated/) | 已结束：Netty/2791f0f构建、9项测试及原版正式JMH通过；Presto/000fa29构建、20项测试通过，240案例的正式JMH在30分钟上限截断。无模型调用，未计部分性能数。 |
| 2026-10-11 | [剩余51题独立补跑](2026-10-11_benchllmrealse-failed51-retry/) | 已停止旧队列，保留已处理8条，其中5条新增Agent评测成功；参考测量不再挡住新题Agent。 |
| 2026-10-11 | [全量 Agent 优先尝试](2026-10-11_benchllmrealse-agent-first64/) | 10月12日04:58结束：64题均处理，历史21题复用；新增42题进入Agent、1题拉取源码超时。新41题有补丁，34题独立测试通过、18题正式JMH通过；三版本比较未自动完成。 |
| 2026-10-12 | [14题Agent超时独立补跑](2026-10-12_benchllmrealse-timeout-retry14/) | 13:53结束：6会话正常/7再次超时/1下载失败，12补丁、7测试通过，JMH暂0通过；含共享JMH锁和入口失败，不能全归因模型。 |
| 2026-10-12 | [18题自动三版本对照](2026-10-12_benchllmrealse-three-version18/) | 15:45完成18题，11完整对照；随后3题符合资格的锁冲突补测16:30全通过，最终14题完整三版本、4题资格不足不再试。 |
| 2026-10-12 | [进度收尾与失败归档](2026-10-12_benchllmrealse-progress-closeout/) | 全64题台账、首轮/重试分开；14题63组匹配对照及失败证据归档，无模型合格补测已完成，不继续扩展实验。 |
