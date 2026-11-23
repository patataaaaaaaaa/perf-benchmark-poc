# Netty 基线实验结果（2026-11-23）

## 实验配置

本次汇报覆盖 12 道 Netty 性能优化题。前两组提供 GPT 基线，后四组用 OpenCode 对照有、无历史案例检索（RAG）的结果。每份进入测量的候选补丁均与同批次的两个版本对照，即优化前的 Netty 原版，以及应用 benchmark 所收录的 Netty 开发者补丁后的版本。

| 组别 | 模型与运行方式 | 历史案例 | 题目范围 |
| --- | --- | --- | --- |
| 历史 GPT Chat | GPT-6 High（历史记录），网页单次生成 | 无实验提供的 RAG 案例 | 从 19 份历史输出中按既定清单纳入 12 题 |
| GPT + Codex | GPT-6 Sol High，Codex CLI | 无 RAG | 全部 12 题 |
| OpenCode 8K 无 RAG | DeepSeek Flash High，OpenCode | 无 RAG | 全部 12 题 |
| OpenCode 8K 有 RAG | DeepSeek Flash High，OpenCode | 每题检索 3 条历史案例 | 全部 12 题 |
| OpenCode 32K 无 RAG | DeepSeek Flash High，OpenCode | 无 RAG | 两个 8K 组均未产出代码修改的 4 题 |
| OpenCode 32K 有 RAG | DeepSeek Flash High，OpenCode | 每题检索 3 条历史案例 | 同上 4 题 |

四个 OpenCode 组均使用 1.19.6 版，每题每组生成一次。8K 和 32K 分别指单次输出上限 8,192 和 32,768 token。同一上限下，有、无 RAG 两组使用相同的题目、源码、镜像和功能测试。

## 主要结果

本次六组计划内的性能测量已完成。按每组实际测到的题数相加，共有 48 份候选补丁（12 + 12 + 8 + 8 + 4 + 4）。8K 主实验中，有、无 RAG 两组都在相同的 8 道题产出补丁，其中各有 7 题比原版更快、每次操作的 CPU 时间也更少。以同题、同批次的 benchmark 开发者补丁为对照，无 RAG 组有 1 题更快、2 题接近、5 题更慢，有 RAG 组为 2 题更快、2 题接近、4 题更慢。比较这 8 题各自相对原版的提速，有 RAG 相对无 RAG 为 2 题更快、4 题接近、2 题更慢，未见一致的速度优势。

## 绝对测量值

下表按题目和实验组列出全部测量。点击场景数即可查看该题所有场景的参数，以及**原版、开发者版、候选版**的吞吐量或平均耗时、每次操作 CPU 时间、每次操作堆分配、驻留内存和内存高水位。

| 题目 | 历史 GPT Chat | GPT + Codex | 8K 无 RAG | 8K 有 RAG | 32K 无 RAG | 32K 有 RAG |
| --- | --- | --- | --- | --- | --- | --- |
| `2791f0f` | [1 个场景](absolute-measurements/chat.md#2791f0f) | [1 个场景](absolute-measurements/gpt-codex.md#2791f0f) | [1 个场景](absolute-measurements/8k-no-rag.md#2791f0f) | [1 个场景](absolute-measurements/8k-rag.md#2791f0f) | 未安排补测 | 未安排补测 |
| `2ed95c9` | [7 个场景](absolute-measurements/chat.md#2ed95c9) | [7 个场景](absolute-measurements/gpt-codex.md#2ed95c9) | 空补丁 | 空补丁 | [7 个场景](absolute-measurements/32k-no-rag.md#2ed95c9) | [7 个场景](absolute-measurements/32k-rag.md#2ed95c9) |
| `5a9b28a` | [6 个场景](absolute-measurements/chat.md#5a9b28a) | [6 个场景](absolute-measurements/gpt-codex.md#5a9b28a) | [6 个场景](absolute-measurements/8k-no-rag.md#5a9b28a) | [6 个场景](absolute-measurements/8k-rag.md#5a9b28a) | 未安排补测 | 未安排补测 |
| `67d3a78` | [12 个场景](absolute-measurements/chat.md#67d3a78) | [12 个场景](absolute-measurements/gpt-codex.md#67d3a78) | [12 个场景](absolute-measurements/8k-no-rag.md#67d3a78) | [12 个场景](absolute-measurements/8k-rag.md#67d3a78) | 未安排补测 | 未安排补测 |
| `687308b` | [6 个场景](absolute-measurements/chat.md#687308b) | [6 个场景](absolute-measurements/gpt-codex.md#687308b) | [6 个场景](absolute-measurements/8k-no-rag.md#687308b) | [6 个场景](absolute-measurements/8k-rag.md#687308b) | 未安排补测 | 未安排补测 |
| `87ec2f8` | [40 个场景](absolute-measurements/chat.md#87ec2f8) | [40 个场景](absolute-measurements/gpt-codex.md#87ec2f8) | [40 个场景](absolute-measurements/8k-no-rag.md#87ec2f8) | [40 个场景](absolute-measurements/8k-rag.md#87ec2f8) | 未安排补测 | 未安排补测 |
| `8a8337e` | [4 个场景](absolute-measurements/chat.md#8a8337e) | [4 个场景](absolute-measurements/gpt-codex.md#8a8337e) | 空补丁 | 空补丁 | [4 个场景](absolute-measurements/32k-no-rag.md#8a8337e) | [4 个场景](absolute-measurements/32k-rag.md#8a8337e) |
| `95b8db0` | [4 个场景](absolute-measurements/chat.md#95b8db0) | [4 个场景](absolute-measurements/gpt-codex.md#95b8db0) | [4 个场景](absolute-measurements/8k-no-rag.md#95b8db0) | [4 个场景](absolute-measurements/8k-rag.md#95b8db0) | 未安排补测 | 未安排补测 |
| `9abeaf1` | [3 个场景](absolute-measurements/chat.md#9abeaf1) | [3 个场景](absolute-measurements/gpt-codex.md#9abeaf1) | 空补丁 | 空补丁 | [3 个场景](absolute-measurements/32k-no-rag.md#9abeaf1) | [3 个场景](absolute-measurements/32k-rag.md#9abeaf1) |
| `ab8c4f2` | [5 个场景](absolute-measurements/chat.md#ab8c4f2) | [5 个场景](absolute-measurements/gpt-codex.md#ab8c4f2) | [5 个场景](absolute-measurements/8k-no-rag.md#ab8c4f2) | [5 个场景](absolute-measurements/8k-rag.md#ab8c4f2) | 未安排补测 | 未安排补测 |
| `b72fea3` | [2 个场景](absolute-measurements/chat.md#b72fea3) | [2 个场景](absolute-measurements/gpt-codex.md#b72fea3) | [2 个场景](absolute-measurements/8k-no-rag.md#b72fea3) | [2 个场景](absolute-measurements/8k-rag.md#b72fea3) | 未安排补测 | 未安排补测 |
| `feb804d` | [3 个场景](absolute-measurements/chat.md#feb804d) | [3 个场景](absolute-measurements/gpt-codex.md#feb804d) | 空补丁 | 空补丁 | [3 个场景](absolute-measurements/32k-no-rag.md#feb804d) | [3 个场景](absolute-measurements/32k-rag.md#feb804d) |

每个数值均为同批次五个有效 JMH 区组的算术平均。吞吐量沿用 ops/s 或 ops/us，平均耗时和 CPU 时间用 ns/op，堆分配用 B/op，进程内存用 MiB。正文的逐题百分比按区组配对后对区组和场景比值取几何平均。

8K 的“空补丁”表示该组尝试了该题，但没有候选版可供测量。32K 只补测两组 8K 都产生空补丁的四题。

## 六组候选相对原版

每格依次列出相对本批次原版 **改善 / 接近 / 退化** 的题数。速度越快越好，其余四项越低越好。以 1.01 倍为描述性阈值，将改善方向的比值介于 1/1.01 和 1.01 之间的题目计为接近。

| 组别 | 实测题数 | 速度 | CPU 时间/op | 堆分配/op | 驻留内存 | 内存高水位 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 历史 GPT Chat | 12 | 9 / 0 / 3 | 9 / 0 / 3 | 7 / 3 / 2 | 2 / 7 / 3 | 2 / 7 / 3 |
| GPT + Codex | 12 | 8 / 1 / 3 | 8 / 1 / 3 | 7 / 3 / 2 | 2 / 7 / 3 | 2 / 7 / 3 |
| OpenCode 8K 无 RAG | 8 | 7 / 0 / 1 | 7 / 0 / 1 | 6 / 2 / 0 | 1 / 4 / 3 | 1 / 4 / 3 |
| OpenCode 8K 有 RAG | 8 | 7 / 0 / 1 | 7 / 0 / 1 | 5 / 2 / 1 | 1 / 4 / 3 | 1 / 4 / 3 |
| OpenCode 32K 无 RAG | 4 | 3 / 0 / 1 | 3 / 0 / 1 | 2 / 1 / 1 | 1 / 3 / 0 | 1 / 3 / 0 |
| OpenCode 32K 有 RAG | 4 | 3 / 1 / 0 | 4 / 0 / 0 | 3 / 1 / 0 | 1 / 2 / 1 | 1 / 3 / 0 |

8K 两组均尝试了全部 12 题，每组有 4 题为空补丁。32K 仅对这 4 题补测，两组均获得 4 份通过功能测试的补丁。8K 和 32K 每组分别覆盖 76 和 17 个 JMH 场景，含 40 个场景的 `87ec2f8` 已完成全部区组。

## 六组候选相对 benchmark 开发者补丁

每格依次为候选补丁**优于 / 接近 / 落后于开发者补丁**的题数，沿用上表的 1.01 倍阈值。每份候选只和同题、同场景、同区组实测的开发者版本配对。空补丁不计入性能比较。

| 组别 | 实测题数 | 速度 | CPU 时间/op | 堆分配/op | 驻留内存 | 内存高水位 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 历史 GPT Chat | 12 | 3 / 3 / 6 | 4 / 2 / 6 | 3 / 5 / 4 | 3 / 9 / 0 | 2 / 10 / 0 |
| GPT + Codex | 12 | 3 / 0 / 9 | 3 / 0 / 9 | 1 / 5 / 6 | 2 / 10 / 0 | 1 / 11 / 0 |
| OpenCode 8K 无 RAG | 8 | 1 / 2 / 5 | 1 / 2 / 5 | 0 / 4 / 4 | 0 / 7 / 1 | 0 / 7 / 1 |
| OpenCode 8K 有 RAG | 8 | 2 / 2 / 4 | 2 / 2 / 4 | 1 / 4 / 3 | 2 / 6 / 0 | 2 / 6 / 0 |
| OpenCode 32K 无 RAG | 4 | 1 / 2 / 1 | 2 / 1 / 1 | 1 / 1 / 2 | 1 / 3 / 0 | 1 / 3 / 0 |
| OpenCode 32K 有 RAG | 4 | 2 / 0 / 2 | 3 / 0 / 1 | 1 / 1 / 2 | 0 / 3 / 1 | 0 / 3 / 1 |

历史 GPT Chat 在 12 题中有 6 题速度落后于开发者，GPT + Codex 有 9 题落后。两组的驻留内存分别有 9 题和 10 题与开发者接近。每份候选与开发者的五项实测差值见[逐题开发者对照](结果分析.md#候选相对开发者)。

## OpenCode 8K 主实验

以下两张逐题表中，提速、CPU 时间减少和堆分配减少均相对各组自己的原版。“有 RAG / 无 RAG 速度差”按两组归一化后的速度比计算。例如 32K 的 `2ed95c9`，有 RAG 为原版速度的 1.3430 倍，无 RAG 为 0.5144 倍，两者之比约为 2.61，即表中的 +161.08%。

| 题目 | 场景 | 无 RAG 提速 | 有 RAG 提速 | 有 RAG / 无 RAG 速度差 | 无 RAG CPU 减少 | 有 RAG CPU 减少 | 无 RAG 堆分配减少 | 有 RAG 堆分配减少 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `2791f0f` | 1 | +106.61% | +119.40% | +6.19% | +44.10% | +46.34% | +0.00% | +0.00% |
| `2ed95c9` | — | 空补丁 | 空补丁 | — | — | — | — | — |
| `5a9b28a` | 6 | -15.31% | -14.78% | +0.64% | -18.08% | -17.32% | +18.61% | -18.86% |
| `67d3a78` | 12 | +5.68% | +5.44% | -0.23% | +5.37% | +5.14% | +5.41% | +5.18% |
| `687308b` | 6 | +15.19% | +11.07% | -3.57% | +13.13% | +9.94% | +9.55% | +9.55% |
| `87ec2f8` | 40 | +38.33% | +41.00% | +1.93% | +27.25% | +28.58% | +6.15% | +6.31% |
| `8a8337e` | — | 空补丁 | 空补丁 | — | — | — | — | — |
| `95b8db0` | 4 | +3.29% | +2.96% | -0.33% | +3.16% | +2.90% | +5.69% | +7.91% |
| `9abeaf1` | — | 空补丁 | 空补丁 | — | — | — | — | — |
| `ab8c4f2` | 5 | +59.04% | +44.05% | -9.43% | +37.12% | +30.60% | +37.14% | +30.57% |
| `b72fea3` | 2 | +29.01% | +30.12% | +0.86% | +22.31% | +22.98% | +0.00% | +0.00% |
| `feb804d` | — | 空补丁 | 空补丁 | — | — | — | — | — |

8 道可配对题中，有 RAG 相对无 RAG 的 CPU 时间为 2 题改善、4 题接近、2 题退化，堆分配为 1 / 5 / 2，驻留内存为 0 / 7 / 1，内存高水位为 1 / 6 / 1。两组相比，有 RAG 在速度上有 2 题更快、4 题接近、2 题更慢。速度优势最大的是 `2791f0f`（+6.19%），降幅最大的是 `ab8c4f2`（−9.43%）。

## OpenCode 32K 补充实验

| 题目 | 场景 | 无 RAG 提速 | 有 RAG 提速 | 有 RAG / 无 RAG 速度差 | 无 RAG CPU 减少 | 有 RAG CPU 减少 | 无 RAG 堆分配减少 | 有 RAG 堆分配减少 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `2ed95c9` | 7 | -48.56% | +34.30% | +161.08% | -94.42% | +25.53% | -94.35% | +25.54% |
| `8a8337e` | 4 | +4.70% | +4.88% | +0.18% | +4.46% | +4.50% | +5.55% | +4.75% |
| `9abeaf1` | 3 | +23.66% | +24.70% | +0.84% | +19.95% | +20.71% | +0.00% | +0.00% |
| `feb804d` | 3 | +1.63% | +0.11% | -1.49% | +1.78% | +1.59% | +15.66% | +15.66% |

四题中差异最大的是 `2ed95c9`。无 RAG 版比原版慢 48.56%，有 RAG 版快 34.30%，每次操作 CPU 时间由增加 94.42% 转为减少 25.53%。两组所有场景中，原版、候选版和开发者版的实测堆分配均低于 0.0001 B/op，因此该题堆分配列的大百分比对应的绝对差很小。与同批开发者直接比较，`2ed95c9` 有 RAG 版仍慢 39.08%，每次操作多用 64.19% 的 CPU 时间。其余三题有、无 RAG 的组间速度差均在 1.5% 以内。

## 历史 GPT 与开发者对照

相对各自同批原版，历史 GPT Chat 在 12 题中有 9 题速度改善，GPT + Codex 有 8 题。按相同的比值阈值，两组均有 7 题每次操作堆分配改善。与开发者的差距因题而异。例如 `87ec2f8` 上，历史 GPT Chat 提速 42.21%，同批开发者提速 86.13%，换算成直接对照，GPT Chat 比开发者慢 23.59%，每次操作多用 31.04% 的 CPU 时间，多分配 18.32% 的堆内存。全部 12 题的速度、CPU、堆分配、驻留内存和内存高水位均可逐项对照。[逐题结果与同批开发者数据](结果分析.md)

**补丁观察。** `9abeaf1` 上，历史 GPT Chat 调整了等待前后的唤醒标记，提速 24.08%，CPU 时间减少 20.27%，同批开发者分别为 23.99% 和 20.23%。32K 无 RAG 版仅删除等待返回后的二次唤醒写入和注释，也提速 23.66%，CPU 时间减少 19.95%。直接对照各自的开发者版，历史 GPT Chat 快 0.07%，简单删除版慢 0.17%，两者的 CPU 时间差也均小于 0.1%。简单删除版在并发唤醒时的行为仍待专门验证。

## 测量口径

- 每个候选完成 5 个有效 JMH 区组，每个区组测原版、开发者版和候选版。每场景预热 10 次、正式测量 50 次，每次 1 秒。先在区组内配对，再对区组和场景比值取几何平均。各批次分别以自己的原版归一化，组间速度差按归一化速度比计算。历史 GPT Chat 和 GPT + Codex 同时改变了模型和运行方式。OpenCode 各条件在不同日期生成，每题每条件生成一次。五个区组重复测量同一份补丁，1% 阈值仅作描述。
- CPU 时间单位为 ns/op，堆分配单位为 B/op。驻留内存（VmRSS）和内存高水位（VmHWM）均取迭代末采样值再汇总。表中资源减少为正、增加为负。`87ec2f8` 补测沿用原验收条件，仅计入通过压力检查的区组。
