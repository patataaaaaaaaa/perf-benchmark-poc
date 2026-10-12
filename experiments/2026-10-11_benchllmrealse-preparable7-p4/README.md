# 7 题付费 P4 补跑

2026-10-11 10:35（北京时间）启动。只跑不付费准备已经通过的 7 题。

- 批次：`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/preparable7-p4-20261011T023531Z`
- PID：`2622703`
- 模型：DeepSeek `deepseek-v4-pro`，官方 P4，Codex CLI
- 复用准备批次 `failed55-prepare-20261010T123140Z` 的冻结构建，不复用任何 Agent 补丁
- 每题顺序：原版正式评测、开发者版正式评测、再调用 Agent
- 不重跑已成功的 9 题，也不跑仍未通过准备的 48 题

题号：Netty `5a9b28a`，Kafka `922a95a`、`b25c96a`、`b36e3c2`、`c05403f`、`cfc34ca`、`eb24ed8`。

模型调用后如果测试或 JMH 失败，记为 Agent 失败尝试，不从分母里去掉。
启动后第一条状态是 Netty `5a9b28a` 的原版评测，此时还没有 `codex exec`。

### 2026-10-11 15:43（北京时间）批次结束

PID `2622703` 已退出。状态为 `complete_with_failures; 7/7 processed`。
7 题都调用了模型。评测成功 4 题：Netty `5a9b28a`，Kafka `b25c96a`、`c05403f`、`cfc34ca`。
Agent 失败尝试 3 题，选定测试都通过，正式 JMH 失败：

- Kafka `922a95a`：约 19 秒。原版、开发者版、Agent 都在 JMH 中因日志刷写异常失败。
- Kafka `b36e3c2`、`eb24ed8`：Agent 基准跑满 1800 秒后被截断。原版和开发者版的正式 JMH 也失败。

这 3 题没有可比较的三版本性能数。没有再启动新队列。
