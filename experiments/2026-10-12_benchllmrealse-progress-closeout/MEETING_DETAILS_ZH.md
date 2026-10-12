# 组会详细附录：BenchLLMRealSE

统计冻结2026-10-12。概括、架构及参数见[主报告](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/MEETING_REPORT_ZH.md)。本附录从JSON台账自动生成，核对64个不同任务、14个完整对照任务、63个匹配场景，以及三版本42份原始JMH文件的分数与10/50/1、每轮1秒参数。

## A. 按项目与逐题进度

| 项目 | 题数 | 累计进入Agent | 历史复用 | 新进入Agent | 新生产补丁 | 新测试通过 | 新JMH通过 | 完整三版 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kafka | 16 | 16 | 7 | 9 | 9 | 6 | 0 | 0 |
| netty | 18 | 18 | 9 | 9 | 9 | 9 | 5 | 3 |
| presto | 25 | 24 | 0 | 24 | 23 | 19 | 13 | 11 |
| RoaringBitmap | 5 | 5 | 5 | 0 | 0 | 0 | 0 | 0 |
| 合计 | 64 | 63 | 21 | 42 | 41 | 34 | 18 | 14 |

历史组的测试/JMH“—”表示本批未重新验收，不表示从未测过或本次失败。第二次Agent尝试不是新增任务；历史21题的生产补丁未在本台账统一计数，因此不发布跨协议总补丁数。

| 任务 | 协议分组 | 首轮/历史状态 | 生产补丁 | 新独立测试 | 新正式JMH | 第二次尝试（独立统计） | 三版本 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RoaringBitmap/1de6825 | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| RoaringBitmap/34bce1b | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| RoaringBitmap/53ba593 | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| RoaringBitmap/abdd6ff | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| RoaringBitmap/b5b4af6 | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| kafka/39eb31f | 新增 | 正常/许可配置修改 | 有 | 通过 | 命令失败 | — | 未纳入 |
| kafka/4fa5bdc | 新增 | 600秒超时 | 有 | 通过 | 命令失败 | 正常/许可配置修改；补丁有；测试通过/JMH命令失败 | 未纳入 |
| kafka/59a75f4 | 新增 | 600秒超时 | 有 | 通过 | 命令失败 | 600秒超时；补丁有；测试通过/JMH命令失败 | 未纳入 |
| kafka/8dff0b1 | 新增 | 600秒超时 | 有 | 通过 | 命令失败 | 600秒超时；补丁有；测试通过/JMH命令失败 | 未纳入 |
| kafka/922a95a | 历史 | 旧协议JMH失败 | 旧档另见 | — | — | — | 未纳入 |
| kafka/9bb2f78 | 新增 | 正常结束 | 有 | 通过 | 命令失败 | — | 未纳入 |
| kafka/aecd47b | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| kafka/b25c96a | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| kafka/b36e3c2 | 历史 | 旧协议JMH失败 | 旧档另见 | — | — | — | 未纳入 |
| kafka/c05403f | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| kafka/c7bc8f7 | 新增 | 600秒超时 | 有 | 命令失败 | 未运行 | 正常结束；补丁有；测试命令失败/JMH未运行 | 未纳入 |
| kafka/c8af740 | 新增 | 正常结束 | 有 | 命令失败 | 未运行 | — | 未纳入 |
| kafka/cfc34ca | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| kafka/e2e2c62 | 新增 | 600秒超时 | 有 | 命令失败 | 未运行 | 600秒超时；补丁有；测试通过/JMH命令失败 | 未纳入 |
| kafka/e3ccf20 | 新增 | 600秒超时 | 有 | 通过 | 命令失败 | 600秒超时；补丁有；测试通过/JMH命令失败 | 未纳入 |
| kafka/eb24ed8 | 历史 | 旧协议JMH失败 | 旧档另见 | — | — | — | 未纳入 |
| netty/2791f0f | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| netty/2ed95c9 | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| netty/5a9b28a | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| netty/67d3a78 | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| netty/687308b | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| netty/7b91edd | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 不完整 |
| netty/83a19d5 | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| netty/87ec2f8 | 新增 | 正常结束 | 有 | 通过 | 超时 | — | 未纳入 |
| netty/8a8337e | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| netty/95b8db0 | 新增 | 正常结束 | 有 | 通过 | 命令失败 | — | 未纳入 |
| netty/9abeaf1 | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整 |
| netty/ab8c4f2 | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整（补测） |
| netty/b2eaab0 | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| netty/b72fea3 | 新增 | 正常结束 | 有 | 通过 | 命令失败 | — | 未纳入 |
| netty/dd69a81 | 新增 | 600秒超时 | 有 | 通过 | 通过 | 600秒超时；补丁有；测试通过/JMH命令失败 | 完整（补测） |
| netty/deea51e | 新增 | 正常结束 | 有 | 通过 | 超时 | — | 未纳入 |
| netty/e542a2c | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 不完整 |
| netty/feb804d | 历史 | 旧协议通过 | 旧档另见 | — | — | — | 未纳入 |
| presto/000fa29 | 新增 | 正常结束 | 有 | 通过 | 超时 | — | 未纳入 |
| presto/20dcaed | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 不完整 |
| presto/239f726 | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整 |
| presto/290f5be | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整（补测） |
| presto/297b089 | 新增 | 600秒超时 | 有 | 超时 | 未运行 | 正常结束；补丁有；测试超时/JMH未运行 | 未纳入 |
| presto/3a4f2e3 | 新增 | 600秒超时 | 有 | 超时 | 未运行 | 正常结束；补丁有；测试超时/JMH未运行 | 未纳入 |
| presto/3f63ade | 新增 | 正常/许可配置修改 | 有 | 通过 | 通过 | — | 完整 |
| presto/46d219f | 新增 | 正常/许可配置修改 | 有 | 通过 | 通过 | — | 完整 |
| presto/4e71bf3 | 新增 | 600秒超时 | 有 | 超时 | 未运行 | 600秒超时；补丁有；测试超时/JMH未运行 | 未纳入 |
| presto/53aa7f6 | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整 |
| presto/60a5a5c | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整 |
| presto/659c3ee | 新增 | 600秒超时 | 有 | 超时 | 未运行 | 源码失败；补丁无；测试—/JMH— | 未纳入 |
| presto/6908344 | 新增 | 600秒超时 | 有 | 通过 | 超时 | 正常结束；补丁有；测试通过/JMH超时 | 未纳入 |
| presto/8abba9e | 新增 | 600秒超时 | 无 | 命令失败 | 未运行 | 600秒超时；补丁无；测试命令失败/JMH未运行 | 未纳入 |
| presto/8d7f587 | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 不完整 |
| presto/9e010a7 | 新增 | 源码失败 | 无 | — | — | — | 未纳入 |
| presto/a26f440 | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整 |
| presto/aed4c9a | 新增 | 正常结束 | 有 | 通过 | 超时 | — | 未纳入 |
| presto/b54d248 | 新增 | 正常结束 | 有 | 通过 | 超时 | — | 未纳入 |
| presto/bfb18d6 | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整 |
| presto/c3cb7a9 | 新增 | 正常结束 | 有 | 通过 | 超时 | — | 未纳入 |
| presto/ee74e4b | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整 |
| presto/efd0834 | 新增 | 正常结束 | 有 | 通过 | 超时 | — | 未纳入 |
| presto/fa655f6 | 新增 | 正常结束 | 有 | 通过 | 通过 | — | 完整 |
| presto/fdb7611 | 新增 | 600秒超时 | 有 | 通过 | 通过 | 正常结束；补丁有；测试命令失败/JMH未运行 | 完整 |

## B. 三版本逐题摘要

### 三版本整体排序（按性能指标分开）

| 三版本性能排序 | 平均耗时（43组） | 吞吐量（20组） | 合计 |
| --- | --- | --- | --- |
| Agent ＞ 开发者 ＞ 原版 | 9 | 7 | 16 |
| Agent ＞ 原版 ＞ 开发者 | 3 | 2 | 5 |
| 开发者 ＞ Agent ＞ 原版 | 14 | 5 | 19 |
| 开发者 ＞ 原版 ＞ Agent | 8 | 0 | 8 |
| 原版 ＞ Agent ＞ 开发者 | 6 | 3 | 9 |
| 原版 ＞ 开发者 ＞ Agent | 3 | 3 | 6 |
| 合计 | 43 | 20 | 63 |

“＞”表示性能优于：`avgt`耗时越低越好，`thrpt`吞吐量越高越好。六种排序互斥且覆盖全部63组；每组是一个benchmark函数及固定参数组合。按原始分数点估计排序，未检验排序差异的统计显著性；本批没有完全相等的分数，接近的结果仍可能受测量波动影响。42份匹配JMH文件没有额外secondaryMetrics，因此本次无内存/分配/GC/CPU利用率结果。

### 逐题速比范围

| 任务 | 场景 | Agent快于原版 | Agent快于开发者 | Agent/原版速比范围 | 开发者/原版速比范围 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| netty/9abeaf1 | 3 | 3 | 2 | 1.0103–1.6037 | 0.9700–1.5704 | 一次点估计 |
| netty/ab8c4f2 | 5 | 3 | 0 | 0.9883–5.1320 | 1.0016–9.7122 | 一次点估计 |
| netty/dd69a81 | 2 | 1 | 0 | 0.9891–1.0020 | 0.9965–1.6754 | 一次点估计 |
| presto/239f726 | 8 | 6 | 5 | 0.8153–1088 | 0.8843–1394 | 极大倍率待复核 |
| presto/290f5be | 5 | 3 | 2 | 0.9956–1.0204 | 0.9842–1.0170 | 一次点估计 |
| presto/3f63ade | 2 | 1 | 1 | 0.9954–6.0939 | 0.9760–8.6006 | 一次点估计 |
| presto/46d219f | 4 | 3 | 1 | 0.8934–9.2547 | 0.9509–9.2862 | 一次点估计 |
| presto/53aa7f6 | 1 | 1 | 1 | 1.0805–1.0805 | 1.0478–1.0478 | 一次点估计 |
| presto/60a5a5c | 2 | 0 | 1 | 0.8993–0.9759 | 0.8943–1.0044 | 一次点估计 |
| presto/a26f440 | 11 | 4 | 6 | 0.9417–8.4104 | 0.8495–11.1511 | 一次点估计 |
| presto/bfb18d6 | 7 | 6 | 4 | 0.9637–1.574e+06 | 0.9893–2.198e+05 | 极大倍率待复核 |
| presto/ee74e4b | 6 | 3 | 4 | 0.9650–68.6669 | 0.8994–68.7343 | 一次点估计 |
| presto/fa655f6 | 6 | 5 | 3 | 0.9941–1.1559 | 0.9557–1.1640 | 一次点估计 |
| presto/fdb7611 | 1 | 1 | 0 | 1.0360–1.0360 | 1.0918–1.0918 | 一次点估计 |

Agent/Original大于1才是该行更快。速比范围不是代表性分数；一次点估计不是统计显著性。详细比较覆盖全部匹配行，没有选择每题最好的负载。

## C. 63个场景的三版本原始分数

分数保留6位有效数字供阅读，完整精度见链接JSON。`thrpt`单位为吞吐，越大越好；`avgt`为耗时，越小越好。时间速比用Original/Variant，吞吐速比用Variant/Original。JMH的scoreError是报告内的误差字段，不是我们重新做的跨版本显著性检验；rawData/scoreConfidence保存在原始文件中。

### netty/9abeaf1

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-netty-9abeaf1/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-netty-9abeaf1/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-netty-9abeaf1/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | io.netty.microbench.channel.epoll.EpollSocketChannelBenchmark.executeMulti | {} | thrpt | ops/s | 438437 | 688511 | 703131 | Agent ＞ 开发者 ＞ 原版 | 1.6037 | 1.5704 | 1.0212 |
| 2 | io.netty.microbench.channel.epoll.EpollSocketChannelBenchmark.executeSingle | {} | thrpt | ops/s | 307945 | 298692 | 330272 | Agent ＞ 原版 ＞ 开发者 | 1.0725 | 0.9700 | 1.1057 |
| 3 | io.netty.microbench.channel.epoll.EpollSocketChannelBenchmark.pingPong | {} | thrpt | ops/s | 95302.1 | 97435.4 | 96279 | 开发者 ＞ Agent ＞ 原版 | 1.0103 | 1.0224 | 0.9881 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 7174.91 | 32696 | 19371.4 |
| 2 | 3819.49 | 9856.76 | 4226.17 |
| 3 | 2759.16 | 2572.54 | 2763.39 |

### netty/ab8c4f2

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/eligible-comparisons/tasks/netty/ab8c4f2/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/eligible-comparisons/tasks/netty/ab8c4f2/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/eligible-comparisons/tasks/netty/ab8c4f2/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchFirst | {} | avgt | ns/op | 10.1168 | 8.17987 | 9.93516 | 开发者 ＞ Agent ＞ 原版 | 1.0183 | 1.2368 | 0.8233 |
| 2 | io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchLast | {} | avgt | ns/op | 44.7608 | 35.5924 | 45.2916 | 开发者 ＞ 原版 ＞ Agent | 0.9883 | 1.2576 | 0.7858 |
| 3 | io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchBeginTable | {} | avgt | ns/op | 62.0517 | 6.38904 | 12.0912 | 开发者 ＞ Agent ＞ 原版 | 5.1320 | 9.7122 | 0.5284 |
| 4 | io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchEndTable | {} | avgt | ns/op | 10.0259 | 7.5367 | 8.67268 | 开发者 ＞ Agent ＞ 原版 | 1.1560 | 1.3303 | 0.8690 |
| 5 | io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNoNameMatch | {} | avgt | ns/op | 1.39208 | 1.38988 | 1.39826 | 开发者 ＞ 原版 ＞ Agent | 0.9956 | 1.0016 | 0.9940 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 0.131032 | 0.0955133 | 0.0449309 |
| 2 | 1.04272 | 0.25478 | 0.0271592 |
| 3 | 0.616612 | 0.0595292 | 0.227894 |
| 4 | 0.103558 | 0.0692483 | 0.13795 |
| 5 | 0.0105381 | 0.0100665 | 0.00981293 |

### netty/dd69a81

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/eligible-comparisons/tasks/netty/dd69a81/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/eligible-comparisons/tasks/netty/dd69a81/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/eligible-comparisons/tasks/netty/dd69a81/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | io.netty.handler.codec.http.HttpRequestEncoderInsertBenchmark.newEncoder | {} | thrpt | ops/s | 4.30326e+06 | 7.20969e+06 | 4.31189e+06 | 开发者 ＞ Agent ＞ 原版 | 1.0020 | 1.6754 | 0.5981 |
| 2 | io.netty.handler.codec.http.HttpRequestEncoderInsertBenchmark.oldEncoder | {} | thrpt | ops/s | 4.40131e+06 | 4.38599e+06 | 4.35347e+06 | 原版 ＞ 开发者 ＞ Agent | 0.9891 | 0.9965 | 0.9926 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 11862 | 33339.3 | 9796.12 |
| 2 | 16219.4 | 11633.6 | 9237.98 |

### presto/239f726

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-239f726/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-239f726/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-239f726/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersects.stIntersectsCrossingLine | {} | thrpt | ops/s | 6833.76 | 8841.39 | 8294.39 | 开发者 ＞ Agent ＞ 原版 | 1.2137 | 1.2938 | 0.9381 |
| 2 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersects.stIntersectsCrossingLineSimpleGeometry | {} | thrpt | ops/s | 1.09939e+06 | 972214 | 1.08237e+06 | 原版 ＞ Agent ＞ 开发者 | 0.9845 | 0.8843 | 1.1133 |
| 3 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersects.stIntersectsInnerLine | {} | thrpt | ops/s | 5910.95 | 6545 | 7164.06 | Agent ＞ 开发者 ＞ 原版 | 1.2120 | 1.1073 | 1.0946 |
| 4 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersects.stIntersectsInnerLineSimpleGeometry | {} | thrpt | ops/s | 909734 | 929670 | 1.00903e+06 | Agent ＞ 开发者 ＞ 原版 | 1.1092 | 1.0219 | 1.0854 |
| 5 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersects.stIntersectsOuterLineInEnvelope | {} | thrpt | ops/s | 6144.12 | 6335.57 | 6699.85 | Agent ＞ 开发者 ＞ 原版 | 1.0904 | 1.0312 | 1.0575 |
| 6 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersects.stIntersectsOuterLineInEnvelopeSimpleGeometry | {} | thrpt | ops/s | 1.04861e+06 | 954774 | 854955 | 原版 ＞ 开发者 ＞ Agent | 0.8153 | 0.9105 | 0.8955 |
| 7 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersects.stIntersectsOuterLineNotInEnvelope | {} | thrpt | ops/s | 13203.6 | 1.84096e+07 | 1.43682e+07 | 开发者 ＞ Agent ＞ 原版 | 1088 | 1394 | 0.7805 |
| 8 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersects.stIntersectsOuterLineNotInEnvelopeSimpleGeometry | {} | thrpt | ops/s | 2.21049e+06 | 1.52145e+07 | 1.87626e+07 | Agent ＞ 开发者 ＞ 原版 | 8.4880 | 6.8829 | 1.2332 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 253.453 | 179.061 | 130.905 |
| 2 | 34978.1 | 9554.58 | 8549.43 |
| 3 | 181.34 | 50.5088 | 13.4509 |
| 4 | 16570.6 | 17462.5 | 2645.85 |
| 5 | 78.6341 | 87.9379 | 172.044 |
| 6 | 6239.7 | 7111.83 | 9895.95 |
| 7 | 172.097 | 134978 | 126425 |
| 8 | 29697.6 | 342803 | 112906 |

### presto/290f5be

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/eligible-comparisons/tasks/presto/290f5be/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/eligible-comparisons/tasks/presto/290f5be/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/eligible-comparisons/tasks/presto/290f5be/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.spi.block.BenchmarkComputePosition.computePositionWithBitShifting | {} | avgt | ns/op | 1.37326 | 1.35033 | 1.34575 | Agent ＞ 开发者 ＞ 原版 | 1.0204 | 1.0170 | 1.0034 |
| 2 | com.facebook.presto.spi.block.BenchmarkComputePosition.computePositionWithDivision | {} | avgt | ns/op | 1.36371 | 1.34832 | 1.35524 | 开发者 ＞ Agent ＞ 原版 | 1.0062 | 1.0114 | 0.9949 |
| 3 | com.facebook.presto.spi.block.BenchmarkComputePosition.computePositionWithFloorMod | {} | avgt | ns/op | 1.84622 | 1.84292 | 1.84362 | 开发者 ＞ Agent ＞ 原版 | 1.0014 | 1.0018 | 0.9996 |
| 4 | com.facebook.presto.spi.block.BenchmarkComputePosition.computePositionWithMask | {} | avgt | ns/op | 1.39259 | 1.41491 | 1.39531 | 原版 ＞ Agent ＞ 开发者 | 0.9980 | 0.9842 | 1.0140 |
| 5 | com.facebook.presto.spi.block.BenchmarkComputePosition.computePositionWithMod | {} | avgt | ns/op | 1.47249 | 1.47035 | 1.479 | 开发者 ＞ 原版 ＞ Agent | 0.9956 | 1.0015 | 0.9942 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 0.0169689 | 0.0107944 | 0.00578744 |
| 2 | 0.0130339 | 0.00848277 | 0.00804377 |
| 3 | 0.0114534 | 0.00291383 | 0.0084892 |
| 4 | 0.0105638 | 0.0124144 | 0.00952976 |
| 5 | 0.00885334 | 0.0102024 | 0.0198761 |

### presto/3f63ade

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-3f63ade/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-3f63ade/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-3f63ade/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.operator.scalar.BenchmarkArrayDistinct.arrayDistinct | {"name":"array_distinct"} | avgt | ns/op | 375.574 | 43.6682 | 61.6316 | 开发者 ＞ Agent ＞ 原版 | 6.0939 | 8.6006 | 0.7085 |
| 2 | com.facebook.presto.operator.scalar.BenchmarkArrayDistinct.arrayDistinct | {"name":"old_array_distinct"} | avgt | ns/op | 381.433 | 390.826 | 383.181 | 原版 ＞ Agent ＞ 开发者 | 0.9954 | 0.9760 | 1.0200 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 1.22768 | 1.42387 | 0.962902 |
| 2 | 0.861882 | 7.98964 | 1.33913 |

### presto/46d219f

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-46d219f/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-46d219f/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-46d219f/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.operator.scalar.BenchmarkMapConcat.mapConcat | {"mapConfig":"both_empty"} | avgt | ns/op | 184.373 | 19.8544 | 19.922 | 开发者 ＞ Agent ＞ 原版 | 9.2547 | 9.2862 | 0.9966 |
| 2 | com.facebook.presto.operator.scalar.BenchmarkMapConcat.mapConcat | {"mapConfig":"left_empty"} | avgt | ns/op | 642.622 | 170.325 | 165.229 | Agent ＞ 开发者 ＞ 原版 | 3.8893 | 3.7729 | 1.0308 |
| 3 | com.facebook.presto.operator.scalar.BenchmarkMapConcat.mapConcat | {"mapConfig":"non_empty"} | avgt | ns/op | 840.936 | 884.397 | 941.317 | 原版 ＞ 开发者 ＞ Agent | 0.8934 | 0.9509 | 0.9395 |
| 4 | com.facebook.presto.operator.scalar.BenchmarkMapConcat.mapConcat | {"mapConfig":"right_empty"} | avgt | ns/op | 501.534 | 161.146 | 162.046 | 开发者 ＞ Agent ＞ 原版 | 3.0950 | 3.1123 | 0.9944 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 0.471093 | 0.0582218 | 0.306397 |
| 2 | 5.01603 | 0.26393 | 0.216719 |
| 3 | 15.3621 | 6.0265 | 32.0561 |
| 4 | 3.24699 | 0.166939 | 0.281448 |

### presto/53aa7f6

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-53aa7f6/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-53aa7f6/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-53aa7f6/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.sql.gen.BenchmarkPageProcessor.compiled | {} | thrpt | ops/s | 14219.7 | 14899.8 | 15363.8 | Agent ＞ 开发者 ＞ 原版 | 1.0805 | 1.0478 | 1.0311 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 346.257 | 377.12 | 287.18 |

### presto/60a5a5c

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-60a5a5c/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-60a5a5c/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-60a5a5c/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.operator.BenchmarkPartitionedOutputOperator.addPage | {"enableCompression":"false"} | avgt | ms/op | 2064.8 | 2308.79 | 2296.08 | 原版 ＞ Agent ＞ 开发者 | 0.8993 | 0.8943 | 1.0055 |
| 2 | com.facebook.presto.operator.BenchmarkPartitionedOutputOperator.addPage | {"enableCompression":"true"} | avgt | ms/op | 1953.71 | 1945.17 | 2001.99 | 开发者 ＞ 原版 ＞ Agent | 0.9759 | 1.0044 | 0.9716 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 125.033 | 142.377 | 133.089 |
| 2 | 31.2765 | 54.4998 | 34.4371 |

### presto/a26f440

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-a26f440/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-a26f440/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-a26f440/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkCopyT | {} | avgt | ns/op | 2548.93 | 1824.76 | 1098.18 | Agent ＞ 开发者 ＞ 原版 | 2.3210 | 1.3969 | 1.6616 |
| 2 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkDeserializeT | {} | avgt | ns/op | 1151.28 | 103.244 | 136.888 | 开发者 ＞ Agent ＞ 原版 | 8.4104 | 11.1511 | 0.7542 |
| 3 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkInsertsT | {} | avgt | ns/op | 48.476 | 57.0645 | 49.5756 | 原版 ＞ Agent ＞ 开发者 | 0.9778 | 0.8495 | 1.1511 |
| 4 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkMergeT | {} | avgt | ns/op | 2692.52 | 1964.88 | 1253.77 | Agent ＞ 开发者 ＞ 原版 | 2.1475 | 1.3703 | 1.5672 |
| 5 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkQuantilesT | {"quantile":"0.0001"} | avgt | ns/op | 11.0685 | 10.8918 | 11.7535 | 开发者 ＞ 原版 ＞ Agent | 0.9417 | 1.0162 | 0.9267 |
| 6 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkQuantilesT | {"quantile":"0.01"} | avgt | ns/op | 16.2132 | 15.6549 | 15.4123 | Agent ＞ 开发者 ＞ 原版 | 1.0520 | 1.0357 | 1.0157 |
| 7 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkQuantilesT | {"quantile":"0.2500"} | avgt | ns/op | 18.4733 | 18.5835 | 18.5543 | 原版 ＞ Agent ＞ 开发者 | 0.9956 | 0.9941 | 1.0016 |
| 8 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkQuantilesT | {"quantile":"0.5000"} | avgt | ns/op | 19.0751 | 19.6709 | 19.1606 | 原版 ＞ Agent ＞ 开发者 | 0.9955 | 0.9697 | 1.0266 |
| 9 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkQuantilesT | {"quantile":"0.7500"} | avgt | ns/op | 20.5869 | 20.4445 | 20.698 | 开发者 ＞ 原版 ＞ Agent | 0.9946 | 1.0070 | 0.9878 |
| 10 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkQuantilesT | {"quantile":"0.9999"} | avgt | ns/op | 27.8857 | 28.0152 | 28.0689 | 原版 ＞ 开发者 ＞ Agent | 0.9935 | 0.9954 | 0.9981 |
| 11 | com.facebook.presto.tdigest.BenchmarkTDigest.benchmarkSerializeT | {} | avgt | ns/op | 103.318 | 104.722 | 104.925 | 原版 ＞ 开发者 ＞ Agent | 0.9847 | 0.9866 | 0.9981 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 5.92928 | 3.90017 | 19.1408 |
| 2 | 2.91548 | 0.13227 | 0.307216 |
| 3 | 0.737018 | 0.687307 | 0.557436 |
| 4 | 34.9015 | 5.1839 | 3.22557 |
| 5 | 0.222374 | 0.120711 | 0.139022 |
| 6 | 0.154421 | 0.168864 | 0.231135 |
| 7 | 0.173967 | 0.267755 | 0.354456 |
| 8 | 0.245505 | 0.277344 | 0.195747 |
| 9 | 0.247467 | 0.16857 | 0.132598 |
| 10 | 0.247591 | 0.212081 | 0.245247 |
| 11 | 0.7397 | 0.643343 | 0.712216 |

### presto/bfb18d6

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-bfb18d6/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-bfb18d6/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-bfb18d6/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersection.stIntersectionComplexPolygonLargeEnvelope | {} | avgt | us/op | 9123.36 | 0.041506 | 88.0738 | 开发者 ＞ Agent ＞ 原版 | 103.5876 | 2.198e+05 | 0.0005 |
| 2 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersection.stIntersectionComplexPolygonSmallEnvelope | {} | avgt | us/op | 1049.42 | 1056.25 | 574.801 | Agent ＞ 原版 ＞ 开发者 | 1.8257 | 0.9935 | 1.8376 |
| 3 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersection.stIntersectionComplexPolygons | {} | avgt | us/op | 13894.8 | 14045.5 | 0.0088272 | Agent ＞ 原版 ＞ 开发者 | 1.574e+06 | 0.9893 | 1.591e+06 |
| 4 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersection.stIntersectionSimpleComplexPolygons | {} | avgt | us/op | 2845.7 | 2751.25 | 2953.02 | 开发者 ＞ 原版 ＞ Agent | 0.9637 | 1.0343 | 0.9317 |
| 5 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersection.stIntersectionSimplePolygonLargeEnvelope | {} | avgt | us/op | 13.1822 | 0.0414328 | 0.352808 | 开发者 ＞ Agent ＞ 原版 | 37.3637 | 318.1591 | 0.1174 |
| 6 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersection.stIntersectionSimplePolygonSmallEnvelope | {} | avgt | us/op | 27.6702 | 26.6726 | 2.66259 | Agent ＞ 开发者 ＞ 原版 | 10.3922 | 1.0374 | 10.0175 |
| 7 | com.facebook.presto.plugin.geospatial.BenchmarkSTIntersection.stIntersectionSimplePolygons | {} | avgt | us/op | 10.2871 | 9.99393 | 0.00802447 | Agent ＞ 开发者 ＞ 原版 | 1282 | 1.0293 | 1245 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 162.113 | 8.66486e-05 | 0.0990958 |
| 2 | 7.34237 | 9.08023 | 0.724508 |
| 3 | 18.2608 | 19.8986 | 0.000118216 |
| 4 | 21.665 | 19.9612 | 16.1225 |
| 5 | 0.0272971 | 9.25161e-05 | 0.000950315 |
| 6 | 0.0560381 | 0.0648802 | 0.00620288 |
| 7 | 0.0202462 | 0.0227771 | 0.000110929 |

### presto/ee74e4b

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-ee74e4b/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-ee74e4b/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-ee74e4b/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.sql.gen.BenchmarkPageProcessor.identityProjection | {"filterFails":"always","projectionDataType":"BIGINT"} | thrpt | ops/s | 1.19144e+07 | 1.1365e+07 | 1.1635e+07 | 原版 ＞ Agent ＞ 开发者 | 0.9765 | 0.9539 | 1.0238 |
| 2 | com.facebook.presto.sql.gen.BenchmarkPageProcessor.identityProjection | {"filterFails":"always","projectionDataType":"DOUBLE"} | thrpt | ops/s | 1.19858e+07 | 1.07797e+07 | 1.19258e+07 | 原版 ＞ Agent ＞ 开发者 | 0.9950 | 0.8994 | 1.1063 |
| 3 | com.facebook.presto.sql.gen.BenchmarkPageProcessor.identityProjection | {"filterFails":"never","projectionDataType":"BIGINT"} | thrpt | ops/s | 1.79627e+06 | 1.73766e+06 | 1.73339e+06 | 原版 ＞ 开发者 ＞ Agent | 0.9650 | 0.9674 | 0.9975 |
| 4 | com.facebook.presto.sql.gen.BenchmarkPageProcessor.identityProjection | {"filterFails":"never","projectionDataType":"DOUBLE"} | thrpt | ops/s | 1.80307e+06 | 1.80065e+06 | 1.83542e+06 | Agent ＞ 原版 ＞ 开发者 | 1.0179 | 0.9987 | 1.0193 |
| 5 | com.facebook.presto.sql.gen.BenchmarkPageProcessor.identityProjection | {"filterFails":"partial","projectionDataType":"BIGINT"} | thrpt | ops/s | 74883.9 | 5.14709e+06 | 5.14017e+06 | 开发者 ＞ Agent ＞ 原版 | 68.6418 | 68.7343 | 0.9987 |
| 6 | com.facebook.presto.sql.gen.BenchmarkPageProcessor.identityProjection | {"filterFails":"partial","projectionDataType":"DOUBLE"} | thrpt | ops/s | 74929.9 | 5.09722e+06 | 5.1452e+06 | Agent ＞ 开发者 ＞ 原版 | 68.6669 | 68.0266 | 1.0094 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 76215.2 | 160447 | 38301.3 |
| 2 | 33792.8 | 127796 | 34604.9 |
| 3 | 5914.09 | 5030.49 | 5165.62 |
| 4 | 5384.31 | 5971.19 | 7358.61 |
| 5 | 287.904 | 23760.2 | 14842.4 |
| 6 | 257.062 | 17634.4 | 15537.7 |

### presto/fa655f6

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-fa655f6/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-fa655f6/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-fa655f6/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.operator.scalar.BenchmarkMapSubscript.mapSubscript | {"mapSize":"1","name":"dictionary"} | avgt | ns/op | 42.6121 | 39.7069 | 38.9856 | Agent ＞ 开发者 ＞ 原版 | 1.0930 | 1.0732 | 1.0185 |
| 2 | com.facebook.presto.operator.scalar.BenchmarkMapSubscript.mapSubscript | {"mapSize":"1","name":"fix-width"} | avgt | ns/op | 20.9361 | 21.9056 | 20.7225 | Agent ＞ 原版 ＞ 开发者 | 1.0103 | 0.9557 | 1.0571 |
| 3 | com.facebook.presto.operator.scalar.BenchmarkMapSubscript.mapSubscript | {"mapSize":"1","name":"var-width"} | avgt | ns/op | 40.2792 | 37.3198 | 34.848 | Agent ＞ 开发者 ＞ 原版 | 1.1559 | 1.0793 | 1.0709 |
| 4 | com.facebook.presto.operator.scalar.BenchmarkMapSubscript.mapSubscript | {"mapSize":"13","name":"dictionary"} | avgt | ns/op | 700.773 | 622.159 | 662.202 | 开发者 ＞ Agent ＞ 原版 | 1.0582 | 1.1264 | 0.9395 |
| 5 | com.facebook.presto.operator.scalar.BenchmarkMapSubscript.mapSubscript | {"mapSize":"13","name":"fix-width"} | avgt | ns/op | 283.17 | 274.345 | 274.622 | 开发者 ＞ Agent ＞ 原版 | 1.0311 | 1.0322 | 0.9990 |
| 6 | com.facebook.presto.operator.scalar.BenchmarkMapSubscript.mapSubscript | {"mapSize":"13","name":"var-width"} | avgt | ns/op | 621.062 | 533.567 | 624.726 | 开发者 ＞ 原版 ＞ Agent | 0.9941 | 1.1640 | 0.8541 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 0.110627 | 0.146964 | 0.0793625 |
| 2 | 0.161403 | 0.168528 | 0.073828 |
| 3 | 0.0899985 | 0.0941966 | 0.0780904 |
| 4 | 1.44191 | 1.62262 | 1.29932 |
| 5 | 1.30278 | 0.910594 | 1.18976 |
| 6 | 1.70275 | 1.22597 | 1.87178 |

### presto/fdb7611

原始数据：[original](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-fdb7611/versions/original-jmh.json)；[developer](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-fdb7611/versions/developer-jmh.json)；[agent](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/initial-comparisons/cases/three-versions-presto-fdb7611/versions/agent-jmh.json)。

| 行 | benchmark | params | mode | 单位 | Original | Developer | Agent | 三版本性能排序 | Agent/Original速比 | Developer/Original速比 | Agent/Developer速比 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | com.facebook.presto.operator.scalar.BenchmarkArrayJoin.benchmark | {} | avgt | ns/op | 99.5022 | 91.1369 | 96.049 | 开发者 ＞ Agent ＞ 原版 | 1.0360 | 1.0918 | 0.9489 |

| 行 | Original scoreError | Developer scoreError | Agent scoreError |
| --- | --- | --- | --- |
| 1 | 0.705642 | 0.70606 | 1.37406 |

## D. 失败目录（历史事件，不是互斥任务数）

同一题可在会话、测试、JMH以及不同版本多次出现；下表77条不能称77题失败，也不能当最终失败率。已解决的锁冲突保留旧证据并标明补测结果。每条对应的完整服务器日志路径见[failure-catalog.json](https://github.com/patataaaaaaaaa/perf-benchmark-poc/blob/codex/benchllmrealse-agent/experiments/2026-10-12_benchllmrealse-progress-closeout/results/failure-catalog.json)。

| 证据序号 | 批次/阶段 | 任务 | 版本 | 环节 | 原因与后续处理 |
| --- | --- | --- | --- | --- | --- |
| 1 | 首轮 | kafka/39eb31f | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 2 | 首轮 | presto/000fa29 | — | benchmark | JMH测量时间上限 |
| 3 | 首轮 | kafka/4fa5bdc | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 4 | 首轮 | kafka/59a75f4 | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 5 | 首轮 | kafka/8dff0b1 | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 6 | 首轮 | presto/297b089 | — | verify | 测试时间上限 |
| 7 | 首轮 | kafka/9bb2f78 | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 8 | 首轮 | presto/3a4f2e3 | — | verify | 测试时间上限 |
| 9 | 首轮 | netty/87ec2f8 | — | benchmark | JMH测量时间上限 |
| 10 | 首轮 | presto/4e71bf3 | — | verify | 测试时间上限 |
| 11 | 首轮 | netty/95b8db0 | — | benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 12 | 首轮 | kafka/c7bc8f7 | — | verify | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 13 | 首轮 | kafka/c8af740 | — | verify | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 14 | 首轮 | presto/659c3ee | — | verify | 测试时间上限 |
| 15 | 首轮 | presto/6908344 | — | benchmark | JMH测量时间上限 |
| 16 | 首轮 | netty/b72fea3 | — | benchmark | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 17 | 首轮 | kafka/e2e2c62 | — | verify | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 18 | 首轮 | presto/8abba9e | — | verify | 现有功能测试失败，详见断言/异常 |
| 19 | 首轮 | kafka/e3ccf20 | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 20 | 首轮 | netty/deea51e | — | benchmark | JMH测量时间上限 |
| 21 | 首轮 | presto/aed4c9a | — | benchmark | JMH测量时间上限 |
| 22 | 首轮 | presto/b54d248 | — | benchmark | JMH测量时间上限 |
| 23 | 首轮 | presto/c3cb7a9 | — | benchmark | JMH测量时间上限 |
| 24 | 首轮 | presto/efd0834 | — | benchmark | JMH测量时间上限 |
| 25 | Agent补跑后验收 | kafka/4fa5bdc | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 26 | Agent补跑后验收 | kafka/59a75f4 | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 27 | Agent补跑后验收 | kafka/8dff0b1 | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 28 | Agent补跑后验收 | presto/297b089 | — | verify | 测试时间上限 |
| 29 | Agent补跑后验收 | presto/3a4f2e3 | — | verify | 测试时间上限 |
| 30 | Agent补跑后验收 | presto/4e71bf3 | — | verify | 测试时间上限 |
| 31 | Agent补跑后验收 | kafka/c7bc8f7 | — | verify | 原生命令失败；具体根因未确认，保留日志，不继续盲目尝试 |
| 32 | Agent补跑后验收 | presto/6908344 | — | benchmark | JMH测量时间上限 |
| 33 | Agent补跑后验收 | kafka/e2e2c62 | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 34 | Agent补跑后验收 | presto/8abba9e | — | verify | 现有功能测试失败，详见断言/异常 |
| 35 | Agent补跑后验收 | netty/dd69a81 | — | benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |
| 36 | Agent补跑后验收 | kafka/e3ccf20 | — | benchmark | Kafka JMH入口/工作目录或wrapper条件不满足 |
| 37 | Agent补跑后验收 | presto/fdb7611 | — | verify | 类初始化异常，源码/环境根因尚未确定 |
| 38 | 首轮 | kafka/4fa5bdc | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 39 | 首轮 | kafka/59a75f4 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 40 | 首轮 | kafka/8dff0b1 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 41 | 首轮 | presto/297b089 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 42 | 首轮 | presto/3a4f2e3 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 43 | 首轮 | presto/4e71bf3 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 44 | 首轮 | kafka/c7bc8f7 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 45 | 首轮 | presto/659c3ee | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 46 | 首轮 | presto/6908344 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 47 | 首轮 | kafka/e2e2c62 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 48 | 首轮 | presto/8abba9e | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 49 | 首轮 | netty/dd69a81 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 50 | 首轮 | kafka/e3ccf20 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 51 | 首轮 | presto/9e010a7 | — | source | 源码下载120秒超时，未调用模型 |
| 52 | 首轮 | presto/fdb7611 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 53 | 第二次Agent尝试 | kafka/59a75f4 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 54 | 第二次Agent尝试 | kafka/8dff0b1 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 55 | 第二次Agent尝试 | presto/4e71bf3 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 56 | 第二次Agent尝试 | presto/659c3ee | — | source | Git源码下载TLS连接异常 |
| 57 | 第二次Agent尝试 | kafka/e2e2c62 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 58 | 第二次Agent尝试 | presto/8abba9e | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 59 | 第二次Agent尝试 | netty/dd69a81 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 60 | 第二次Agent尝试 | kafka/e3ccf20 | — | agent | Agent会话600秒上限；有无补丁与后续验收单独统计 |
| 61 | 三版本对照 | presto/20dcaed | original | verify | 功能断言失败：期望null，实际NaN；不修改断言迁就原版 |
| 62 | 三版本对照 | presto/290f5be | original | benchmark | 首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留 |
| 63 | 三版本对照 | presto/290f5be | developer | benchmark | 首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留 |
| 64 | 三版本对照 | presto/290f5be | agent | benchmark | 首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留 |
| 65 | 三版本对照 | netty/7b91edd | original | benchmark | 原版生产API与共用benchmark访问要求不兼容 |
| 66 | 三版本对照 | netty/7b91edd | agent | benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |
| 67 | 三版本对照 | netty/ab8c4f2 | original | benchmark | 首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留 |
| 68 | 三版本对照 | netty/ab8c4f2 | developer | benchmark | 首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留 |
| 69 | 三版本对照 | netty/ab8c4f2 | agent | benchmark | 首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留 |
| 70 | 三版本对照 | netty/dd69a81 | original | benchmark | 首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留 |
| 71 | 三版本对照 | netty/dd69a81 | developer | benchmark | 首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留 |
| 72 | 三版本对照 | netty/dd69a81 | agent | benchmark | 首次JMH锁冲突；后续合格无模型补测已解决，旧日志保留 |
| 73 | 三版本对照 | presto/8d7f587 | original | verify | 功能测试空指针异常；是否由共用修复版fixture引起尚未确定 |
| 74 | 三版本对照 | presto/8d7f587 | developer | benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |
| 75 | 三版本对照 | presto/8d7f587 | agent | benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |
| 76 | 三版本对照 | netty/e542a2c | original | verify | 部分源码回退后API不兼容：internalRefCnt缺失 |
| 77 | 三版本对照 | netty/e542a2c | developer | benchmark | JMH共享全局锁冲突：调度/隔离问题，非性能失败 |

## E. 用量与次数口径

本轮新调用42题＋超时第二尝试13题＝55个实际启动Agent的题次；一个Agent会话通常包含多次模型API请求，55不是API请求总数，也不包括历史21题及此前其他批次的请求。

| 批次 | 实际Agent题次 | 有total_tokens记录 | 日志input_tokens合计 | 其中cached_input_tokens | 日志output_tokens合计 | 日志total_tokens合计 |
| --- | --- | --- | --- | --- | --- | --- |
| 首轮新增 | 42 | 29 | 66230119 | 64045312 | 526274 | 66756393 |
| 超时第二次尝试 | 13 | 6 | 13517125 | 13090304 | 110570 | 13627695 |

这些只是已记录usage字段的合计，不是完整费用账单；首轮含一条超时会话留下的usage，其他超时多缺最终记录。cached_input_tokens是input_tokens的子集，不能再次相加；未知usage不能按零计算，也不能用日志token和未经核验的单价猜本批费用。

## F. 批次路径与完成时间（北京时间）

| 批次 | Agent结束 | 评测/测量结束 | 服务器artifact目录名 |
| --- | --- | --- | --- |
| Agent优先全64台账 | 10-12 01:01:34 | 10-12 04:58:13 | agent-first64-20261011T113000Z |
| 14超时第二尝试 | 10-12 13:19:35 | 10-12 13:53:40 | agent-first64-timeout-retry-20261012T032000Z |
| 18题三版本 | 不调用模型 | 10-12 15:45:26 | three-versions-batch18-20261012T033600Z |
| 3题合格三版本补测 | 不调用模型 | 10-12 16:30:12 | three-versions-eligible-20261012T061300Z |

服务器artifact共同前缀：`/downloads/patataWJY/benchllm-agent-eval/artifacts/benchllmrealse/`；通过`ssh lab-server`只读查看。最后3题补测完成后本阶段全部队列结束，不应再用旧PID当仍运行。完整Agent事件、最终消息、patch及环境patch留在各批次`tasks/<项目>/<题号>/`，三版本日志在对应`cases/`或补测`tasks/`。
