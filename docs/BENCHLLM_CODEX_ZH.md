# BenchLLMRealSE × Codex CLI 接入说明

本阶段不再直接调用 DeepSeek Chat Completions，也不要求模型输出 JSON
`search/replace` 补丁。控制器将 BenchLLMRealSE 的任务提示交给 Codex CLI，Codex 在一个
干净、隔离的 Java 仓库副本中直接修改源码；退出后再由外部命令执行编译、单元测试和
JMH。测试与性能结果不由 Agent 自己判定。

## 当前边界

- 首批接入对象是 `Dataset/PerfOpt` 任务。
- 允许修改的文件直接读取任务 JSON 的 `source_code` 字段。
- 测试文件、JMH、构建配置和评测脚本均在修改白名单之外。
- 每次运行记录精确模型名、Codex 版本、JSONL 事件、最终回复、Git patch、验证日志和
  JMH 日志。
- 工作目录必须在启动前保持 Git clean；建议每次实验创建新的 detached checkout。
- 启动前会验证工作目录 HEAD 等于任务 `commit_hash` 的父提交（buggy revision），避免
  在错误版本上生成补丁。

## 环境

1. 安装并确认 Codex CLI：

   ```bash
   codex --version
   ```

2. 按 DeepSeek 的 Codex 接入文档配置 Responses API provider。密钥只放在环境变量或
   用户级 Codex 配置中，不能提交到本仓库。

3. 显式选择模型。BenchLLMRealSE 原始代码中的 `deepseek-chat` /
   `deepseek-reasoner` 与当前 Codex 可用模型不一定相同；正式实验必须记录实际模型
   标识，不能只写“DeepSeek”。

4. 为对应 Java 项目确认正确版本的 JDK 和构建工具。本机已有 JDK 11，但没有全局
   Maven/Gradle；RoaringBitmap 自带 Gradle Wrapper，因此首个任务可以用 `./gradlew`
   下载固定版本后构建。正式 JMH 前仍需先验证 wrapper、依赖下载和 Java 版本。

## 单任务 dry run

先准备 BenchLLMRealSE 以及一个干净的目标项目 checkout。`--commit-id` 是数据集中性能
修复提交的 ID；目标工作目录应定位到 benchmark 所要求的 buggy revision，不能直接在
日常开发副本上运行。

```bash
.venv/bin/python scripts/run_benchllm_codex.py \
  --benchmark-root /path/to/BenchLLMRealSE \
  --workspace /path/to/isolated/RoaringBitmap \
  --repo-name RoaringBitmap \
  --commit-id <PERFOPT_COMMIT> \
  --prompt-number 1 \
  --model <EXACT_DEEPSEEK_MODEL> \
  --profile <CODEX_DEEPSEEK_PROFILE> \
  --dry-run
```

dry run 会检查任务 JSON、Prompt 和源码白名单，但不会调用模型。

## 运行 Agent

下面的验证与 JMH 命令只是接口形式；应替换成对应 PerfOpt 项目的权威命令。命令使用
参数列表直接执行，不经过 shell。参数中的 `{workspace}` 和 `{artifacts}` 会分别替换为
隔离仓库和本次产物目录的绝对路径。

```bash
.venv/bin/python scripts/run_benchllm_codex.py \
  --benchmark-root /path/to/BenchLLMRealSE \
  --workspace /path/to/isolated/RoaringBitmap \
  --repo-name RoaringBitmap \
  --commit-id <PERFOPT_COMMIT> \
  --prompt-number 1 \
  --model <EXACT_DEEPSEEK_MODEL> \
  --profile <CODEX_DEEPSEEK_PROFILE> \
  --verification-command './gradlew test --tests org.roaringbitmap.art.Node16Test' \
  --benchmark-command './jmh/run.sh .*IntermediateByteArrayBenchmark.* -rf json -rff {artifacts}/jmh.json'
```

不要直接使用上游 `Scripts/run_jmh/bitmap.sh -llm`：它会自行 `git reset`、应用旧式
patch 并修改 `jmh/run.sh`，不适合 Agent 已经直接编辑好的隔离工作区。

默认产物目录：

```text
artifacts/benchllmrealse/<repo>/<commit>/prompt<N>-<UTC timestamp>/
├── prompt.txt
├── codex_events.jsonl
├── codex_stderr.log
├── last_message.txt
├── agent.patch
├── verification.stdout.log
├── verification.stderr.log
├── benchmark.stdout.log
├── benchmark.stderr.log
└── result.json
```

只有以下条件全部满足，结果才是 `succeeded`：Codex 正常退出、产生源码修改、未越过
文件白名单、验证命令通过、JMH 命令通过。性能是否提升仍需读取 JMH 数据并与同机运行
的 Original 和 Developer/Reference 结果比较。
