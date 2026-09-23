# 实验演进记录

这个文件记录项目为什么增加某一步、流程发生了什么变化，以及对应证据放在哪里。
这里只保留浓缩后的过程性思考，不代替正式实验报告。

## 2026-09-23：仓库级自主 Workload 闭环 Bad Case

### 增量考虑

此前实验要么人工给定目标函数，要么给定可信 workload。本次只向框架提供
More-itertools 仓库，不指定目标函数或 testcase，验证“扫描场景 → DeepSeek 选择并生成
workload → 沙箱验收 → profiler 定位热点 → DeepSeek 优化 → 功能与性能验收”的自主入口。

### 过程与结果

- 扫描器从仓库测试中提取 150 个候选场景；DeepSeek 选择
  `tests/test_more.py::PeekableTests`，并在两次修复后生成通过自动验收的 workload。
- profiler 在该 workload 下选择 `more_itertools.more.peekable.__next__` 为 Top 1：
  20,001 次调用，自身耗时约 2.775 ms，占 profile 总时间约 47.9%。两次独立 profile
  的 Top 1 一致。
- 运行中暴露了类方法名称丢失作用域的问题；修复后可正确解析、导入和提取
  `peekable.__next__`，Baseline 完整测试为 815 passed、1 skipped。
- DeepSeek 生成两个候选补丁，二者功能测试均通过，但相对 Baseline 分别慢约
  3.40% 和 14.93%，因此全部拒绝；当前最佳版本保持 Baseline，`best.patch` 为空。

### 结论

自主链路已经能够完整运行并在失败时正确拒绝、回退，但这个实验不能证明自动选择的
workload 具有真实代表性，也不能证明 `self time` Top 1 就是值得修改的根因。该场景大量
消费迭代器，会自然放大 `__next__`；“频繁且耗时”与“存在可优化缺陷”不是同一件事。
这也不能与历史 `triplewise()` 官方修复直接对比，因为模型自主选择了不同场景。

### 证据

- 精简归档：`experiments/2026-09-23_more-itertools-autonomous-workload-badcase/`
- 服务器原始实验：
  `artifacts/more_itertools_repository_autonomous_e2e/20260923_102459_372669/`
- 优化闭环：
  `artifacts/more_itertools_repository_autonomous_e2e/20260923_102459_372669/optimization/20260923_105019_163333/`

### 由此产生的下一步

不再只保留一个 workload 和一个 Top 1。先保留多个候选 workload，对每个候选采集
Top N、调用关系、跨规模趋势和稳定性；若连续两个补丁无提升，则切换到下一个热点或
workload。随后用带历史人工修复的任务建立标签，比较规则、DeepSeek 与 Jev 在
workload 选择、性能类型分类和热点选择上的准确率、成本与稳定性。

## 2026-09-21：第一版性能任务规则分类器

### 增量考虑

此前所有真实任务都直接进入 `cProfile + pyperf` 的运行时间路线，但后续仓库可能是
内存或 I/O 问题。现增加一个不需要训练、结果可解释的基线分类器，在进入具体 profiler
之前根据 CPU/wall、RSS、tracemalloc 和进程 I/O 判断路由。证据不足时输出 `unknown`，
不强行猜测。用户声明的目标只作为上下文，不覆盖测量结果。

### 第一版规则

```text
CPU/wall 较高                         → cpu_bound
内存随小/大输入规模持续明显增长       → memory
真实 I/O 字节或 I/O 次数随规模增长    → io
同时命中多个信号                     → mixed
证据不足                             → unknown
```

### 验证结果

- 旧实验复用：`triplewise` 判为 `cpu_bound/high`；`attrs.asdict` 判为
  `cpu_bound/medium`。
- Docker 受控实验：纯计算、内存增长、文件读写三类均分类正确。
- 首轮曾把 Python 解释器固定的约 129 次启动读取误判为 I/O；规则修正为要求真实字节
  或操作次数随 workload 规模增长，复测后内存任务不再误判。
- 完整回归：57 个测试全部通过。
- 结果路径：
  `artifacts/task_classification/20260921_151207_842396/summary.json`

### Linux 服务器复测

- 环境：Ubuntu Linux，i9-13900K（32 逻辑 CPU），125 GiB 内存，Docker 27.0.2；
  控制器 Python 3.10.12，沙箱 Python 3.11。
- 服务器完整回归：57/57 通过。
- 受控分类：纯计算 → `cpu_bound/high`，内存增长 → `memory/high`，
  文件读写 → `io/medium`，3/3 符合已知标签。
- 运行中发现服务器的首选阿里云 Docker mirror 对固定 digest 返回 403；改用显式
  Docker 官方 registry 地址后成功，基础镜像 digest 未改变。
- 本地下载证据：
  `artifacts/task_classification_server/20260921_161325_202500`
- 服务器原始路径（相对项目根目录）：
  `artifacts/task_classification/20260921_161325_202500`

### 当前边界

阈值仍是第一版启发式规则，只用于建立稳定、可复现的无模型基线。积累更多真实任务后，
再与 Jev 或 DeepSeek 分类进行同条件对照；目前没有足够标注数据训练小模型。

## 2026-09-21：分类器以观察模式接入主流程

### 增量考虑

受控样例通过后，先让分类器跟随真实闭环积累证据，但不能立即让第一版启发式规则
控制 profiler 路由。这样可以验证它在真实任务上的表现，同时避免错误分类破坏已经跑通的
CPU 优化流程。

### 流程变化

```text
Baseline 原始 workload/资源测量
→ 规则分类
→ 输出 task_classification.json
→ 继续原有 profiler 和优化闭环（分类结果不参与控制）
```

- 优先使用原始端到端 workload 的资源数据；没有时才使用目标 microbenchmark。
- 输出明确保存 `mode=observe_only`、`routing_applied=false` 和证据来源。
- 单一规模无法证明内存增长时会保留限制说明，不把一次高 RSS 强判为内存问题。
- 本机与 Linux 服务器完整回归均为 59/59 通过。

下一步是在真实 CPU、内存和 I/O 任务上积累分类记录，再决定是否启用自动路由，
以及是否需要 Jev、DeepSeek 或训练小模型。

## 2026-09-19：从目标函数加速扩展到原始场景验收

### 增量考虑

不能只检查目标函数单独运行是否变快，还要检查最初用于发现热点的完整 workload
是否真的变快。否则可能出现目标函数的 microbenchmark 提升明显，但对真实执行场景帮助很小，
甚至导致场景整体变慢的情况。

### 流程变化

```text
原始 workload → profiler 定位热点 → 生成目标函数 benchmark
                                  ↓
                              生成候选补丁
                                  ↓
                            功能正确性验证
                                  ↓
              目标函数 benchmark 前后对比（局部是否变快）
                                  ↓
                 原始 workload 前后对比（整体是否变快）
                                  ↓
                     两项均满足条件才接受补丁
```

### 实验结果路径

- 验证方式：复用已经冻结的 Baseline、Human Fix 和 DeepSeek Fix，不调用 LLM，
  在 Docker 沙箱中运行同一份原始 workload。
- 本地快速结果：Baseline median `214.42 ms`，Human Fix `53.79 ms`，
  DeepSeek Fix `95.58 ms`；DeepSeek Fix 相对 Baseline 提升 `55.42%`，通过 `3%` 门槛。
- 结果路径：
  `artifacts/more_itertools_triplewise_auto_e2e/20260919_145740_690761/original_workload_retest/20260919_160354_622848`
- 解释边界：本次使用 `--fast`，且 Baseline 波动较大，只验证新增验收流程能够工作，
  不作为正式性能结论。

## 2026-09-19：执行带原始 workload 验收的新闭环

### 增量考虑

前一项实验只用冻结补丁验证了原始 workload 测量。本次重新调用 DeepSeek 生成
benchmark 和候选补丁，确认新增条件已经真正接入自动接受/拒绝决策。

### 流程

```text
workload 自动定位热点 → DeepSeek 生成并冻结 benchmark → DeepSeek 分析并生成补丁
→ 功能测试 → 目标函数 benchmark → 原始 workload → 自动接受或拒绝
```

### 实验结果路径

- 结果：热点自动定位为 `more_itertools.recipes.triplewise`；benchmark 一次生成成功；
  候选通过全部功能检查。
- 目标函数 benchmark：median 从 `237.89 ms` 降至 `139.65 ms`，提升 `41.30%`。
- 原始 workload：median 从 `173.41 ms` 降至 `96.66 ms`，提升 `44.26%`。
- 决策：`ACCEPT`。
- 结果路径：
  `artifacts/more_itertools_triplewise_auto_e2e/20260919_190957_924101`
- 解释边界：这是本机 `--fast` 单 Run、单轮闭环，只证明流程能够正确联动，
  不用于估计系统的总体成功率或正式加速效果。

## 2026-09-19：加固实验副本与发布流程

### 增量考虑

实验副本必须与缓存独立、可以安全回滚和清理；被接受的补丁还需要一个明确但
不自动合并的后续入口。

### 流程变化

```text
独立 clone → 候选测试 → 接受则生成 release_candidate → 清理代码副本
→ 用户显式创建审查分支 → 重新功能验证 → 人工决定 commit/merge/push
```

### 验证

- 已取消 `git clone --shared`。
- 已增加“接受→拒绝→再次接受”回滚测试。
- 已增加补丁哈希、基线校验和显式发布命令；不会自动合并或推送。

## 2026-09-19：补充 Workload 获取与验证层

### 增量考虑

Workload 是“让项目完成什么工作”的执行场景，不是运行后得到的时间、CPU、内存
或日志。只有先确定 workload，真实运行后才能产生指标并由 profiler 定位热点。

当前 `triplewise` workload 是根据历史性能问题人工编写的：对
`triplewise(repeat(None, 1_000_000))` 进行完整消费。它有问题背景作为依据，
但尚未证明框架能从一般仓库中自动获得可信 workload。

### 计划流程

```text
问题描述/真实记录/仓库证据
→ 扫描 benchmark、testcase、examples
→ 形成候选并标注来源与可信度
→ 必要时由 DeepSeek 补全脚本
→ 验证运行、正确性、仓库代码命中和稳定性
→ 人工确认并冻结
→ profiler 与优化闭环
```

### 当前边界

- 框架可以自动产生和验证候选，但不能在没有业务证据时保证其代表真实使用场景。
- 项目存在多个入口时应保留多个 workload，并根据用户报告的性能问题选择。

### 第一阶段扫描结果

- 已实现只读候选扫描器，第一阶段不调用 LLM、不执行候选。
- More-itertools Baseline 中没有发现已有 benchmark 或 examples；发现两个有效测试模块：
  `tests/test_more.py` 和 `tests/test_recipes.py`。
- 两者目前只能作为中等可信度的 testcase 候选，仍需要提取具体场景、放大合理输入并验证。
- 结果路径：`artifacts/workload_discovery/20260919_203609_715230`

## 2026-09-19：Testcase 派生 Workload 受控实验

### 增量考虑

候选扫描只能找到测试文件，不能直接说明其中哪个场景适合做性能 workload。
因此先做一个已知答案的受控实验：从 `tests/test_recipes.py` 自动提取
`TriplewiseTests`，让 DeepSeek 只依据目标源码和这段测试把小输入放大为可测量脚本，
再与人工根据历史 issue 编写的 workload 对照。

### 流程

```text
testcase 场景提取 → DeepSeek 放大输入并生成脚本 → Docker 自动验收
→ 生成 WorkloadSpec 并锁定脚本哈希 → 连续三次 profiler
→ 与人工历史 workload 的 Top 1、Top 5 和排名稳定性对照
```

### 结果

- DeepSeek 第一次生成即通过语法、契约、正确结果、重复执行和动态目标命中检查。
- 派生 workload 连续三次都将 `more_itertools.recipes.triplewise` 排为 Top 1。
- 人工历史 workload 连续三次也将同一函数排为 Top 1；两类 workload 的 Top 1
  结论 `3/3` 次一致。
- 派生 workload 三次 Top 5 完全一致，交并比为 `1.0`。
- 当前状态仍是“自动验收通过的候选”：脚本在本次实验中按哈希锁定，
  但尚未经过人工代表性确认，因此 `human_confirmed=false`、`frozen=false`。
- 结果路径：`artifacts/workload_builder/20260919_205005_233057`

## 2026-09-19：人工确认与正式冻结入口

自动验收通过不等于 workload 代表真实业务。新增显式冻结命令后，只有候选已经通过
自动验收、实验期间按哈希锁定，并且人工提供审阅者、确认理由和完全匹配的 SHA-256，
才会在独立 `frozen_workload/` 目录生成正式版本。原候选文件与元数据不会被覆盖。

当前候选尚未得到用户对“业务代表性”的明确确认，因此没有替用户执行冻结，
`human_confirmed=false` 和 `frozen=false` 保持不变。

## 2026-09-19：第二个仓库 attrs.asdict Workload 实验

### 任务来源

- 仓库：`python-attrs/attrs`
- 历史修复：PR #1463
- Baseline：`57f0d5441c9deaac44aebbbf45e38e477651e4f2`
- Human Fix：`7369ad9f4b273e400478c8e65399d826ab3f3b32`
- 仓库证据：`bench/test_benchmarks.py::test_asdict_atomic`

该任务用于验证不同仓库、标准 `src/` 目录结构和“优先复用已有 benchmark”的路径。

### 发现并修复的问题

1. 官方 benchmark 使用 `ad = attrs.asdict` 后调用 `ad(c)`；原提取器只识别直接调用。
   现已支持函数别名引用证据。
2. 原热点模块名错误包含 `src.`；现已按 Python `src/` 布局输出
   `attr._funcs.asdict`。
3. 首次 profile 把模块导入和动态建类计入热点，导致派生 workload 只有 `2/3` 次
   Top 1 一致。现改为先加载、校验和预热，再只对主 callback 本体启用 cProfile。

### 结果

- 初次结果（保留为失败证据）：
  `artifacts/workload_builder/20260919_211538_077233`
- 修正后复用同一生成脚本，不调用 LLM：
  `artifacts/workload_builder/20260919_212228_109736`
- 参考 workload 与派生 workload 均连续三次将 `attr._funcs.asdict` 排为 Top 1。
- 派生 workload 三次 Top 5 完全一致，交并比为 `1.0`。
- 复测记录 `llm_called=false`，复用脚本 SHA-256 为
  `0533b4b82d7e4d17b853e3b133d63c3a10bdcfb333b4b44fb5f3c96797065e2e`。
- 边界：官方场景是 atomic-only 对象，而 DeepSeek 将主 case 扩展成了 large nested
  对象。它在“热点定位一致性”上通过，但还没有通过“workload 意图保真”的人工确认，
  因此不能冻结为正式 workload。下一步需增加数据形状、操作和主 case 的保真检查。

## 2026-09-21：服务器真实项目性能类型分类

### 增量考虑

受控 CPU、内存和 I/O workload 只能验证规则实现，不能代表真实项目。本次选择
`openpyxl==3.1.5` 的工作簿加载场景和 `fsspec==2025.3.0` 的本地文件顺序读取场景，
在固定 Linux 服务器的 Docker 沙箱中采集两个输入规模的资源数据。数据准备不计入
测量，不调用 LLM，也不修改项目代码。

第一轮调试在 workload 中加入了固定等待，会人为降低 CPU/wall，因此作废。正式运行
删除固定等待，并对 fsspec 文件使用 Linux cache-drop hint，避免用“看起来正确”的
数据证明分类器。

### 结果

- openpyxl：实际为 `mixed/high`，同时检出 CPU 和内存信号；RSS 随输入规模增加约
  `104 MB`，tracemalloc peak 增加约 `38.7 MB`。
- fsspec：实际为 `io/medium`；16 MiB 与 64 MiB 输入对应读取约 16 MiB 与 64 MiB，
  中位 CPU/wall 约 `0.48`。
- 真实任务不再要求强制单标签，而是要求预期资源信号必须出现，并保留完整分类结果。
- 结果路径：
  `artifacts/real_task_classification_server/20260921_170127_443797`

### 当前判断

分类器已经从“合成样本可用”推进到“能描述两个真实项目场景”，但样本数仍不足以
固定阈值或开启自动路由。下一步应再增加独立内存/I/O 任务，再接入类型对应的 profiler。

## 2026-09-21：第二组真实内存/I/O 样本与规则校准

### 增量考虑

为避免一套规则只适配 openpyxl 和 fsspec，增加 cachetools 的 LRU 缓存增长场景与
smart_open 的本地文件分块读取场景。两者各自使用 16/64 MiB 两个规模，在服务器
Docker 中独立测量三次。

曾尝试使用 joblib 数组加载作为 I/O 样本，但实际测量显示它还会显著增加进程内存，
因此拒绝将其包装成“纯 I/O 成功案例”，改用低内存的 smart_open 流式读取。

### 发现与修正

cachetools 第二次运行受到解释器启动文件读取波动影响，被额外误报 I/O。原规则在
没有实际读写字节时，只要求操作次数增长 20 次或 10%，门槛过低。现调整为至少
40 次且 25%，并使用原始证据回放验证：受控三类样本仍正确，新样本三次分类一致。

### 结果

- cachetools：三次均检出内存信号；校准后均为 `memory/high`。
- smart_open：三次均为 `io/medium`。
- 最终四项目统一复测：openpyxl=`mixed`、cachetools=`memory`、
  fsspec=`io`、smart_open=`io`，预期资源信号 `4/4` 检出。
- 最终结果路径：
  `artifacts/real_task_classification_server/20260921_174818_986853`
- joblib 失败证据路径：
  `artifacts/real_task_classification_server/20260921_174117_938355`

### 当前判断

现有证据已足够进入第一版“观察式 profiler 路由”：分类结果决定额外采集哪类热点
证据，但暂时不直接决定补丁是否接受。

## 2026-09-21：观察式 Profiler 路由与内存 Top N 解析

### 增量考虑

将分类结果接回主 pipeline，但先把“选择工具”和“执行工具”分开，避免新路由直接
改变已经跑通的补丁闭环。映射固定为：CPU→cProfile、内存→tracemalloc、I/O→
进程 I/O 证据，mixed→组合选择，unknown→不猜测。

### 实现与验证

- 完整闭环会新增 `profiler_routing.json`，记录选择的工具、理由、实现状态，以及
  `execution_applied=false`、`optimization_decision_impact=false`。
- 新增 tracemalloc snapshot 解析器，可以输出仓库内分配位置 Top N，包括文件、
  行号、函数、分配字节数、分配次数和占比。
- 新增路由与内存热点测试；Linux 服务器完整回归 `64/64` 通过。

### 当前边界

路由目前只生成计划，还没有执行专项 profiler。tracemalloc 解析器已经可用，但真实
workload 必须提供明确 callback 边界，才能在主要对象被释放前采集有意义的 snapshot。
下一步应定义统一 workload callback 接口，并真正执行路由选择的采集器。

## 2026-09-21：统一 Callback 与 tracemalloc 实际执行

### 增量考虑

tracemalloc snapshot 只记录采集时仍存活的分配。如果普通 workload 在函数返回前已经
释放主要对象，事后 snapshot 会漏掉真正热点。因此定义三阶段 callback：准备输入、
执行核心操作、验证结果，并在执行返回后、验证前保留 state/result 强引用完成快照。

### 实现与验证

- 新增通用 callback runner，可组合执行 cProfile、tracemalloc，或仅由外层采集进程
  I/O；导入、准备和可选预热不计入专项 profile。
- pipeline 新增可选 `profiler_callback` 配置。路由选择后实际执行 callback，生成
  `profiler_observation/profiler_evidence.json`，并把过滤后的证据加入模型上下文。
- 自动目标发现已有的 cProfile 结果会直接复用，避免重复运行。
- 模型上下文会删除仅用于实验验收的预期目标，完整原始证据仍保存在产物中。
- 服务器 Docker 烟雾结果：16 MiB 分配的 Top 1 为
  `memory_target.allocate_cache`，定位到 `memory_target.py:4`，占项目内追踪分配约
  `99.997%`。
- 结果路径：`artifacts/profile_callback_smoke_server/20260921_200224_931359`。
- Linux 完整回归：`66/66` 通过。

### 当前边界

受控 callback 已跑通，但还没有选择真实内存历史问题完成 DeepSeek 补丁闭环；I/O
也仍只有进程级总量，没有文件或调用位置 Top N。

## 2026-09-21：真实内存任务候选筛选——CPython tarfile

### 任务与版本

选择 CPython issue #102120：旧版 `tarfile` 在遍历归档时会把每个 `TarInfo` 保存在
`TarFile.members`，大量小文件会导致内存随条目数增长。官方 PR #102128 增加
`stream=True`，读取时不再缓存成员信息。

- Baseline：`097b7830cd67f039ff36ba4fa285d82d26e25e84`
- Human Fix：`50fce89d123b25e53fa8a0303a169e8887154a0e`
- 官方改动范围：`Lib/tarfile.py` 17 行，并增加对应标准库测试和文档。

### 轻量可行性结果

在不调用 LLM、不修改项目仓库的前提下，分别加载两个官方版本的 `tarfile.py`，读取
同一个包含 20,000 个空条目的归档，并在读取阶段采集 `tracemalloc`：

- Baseline：缓存 20,000 个成员，峰值约 `8.88 MB`。
- Human Fix（`stream=True`）：缓存 0 个成员，峰值约 `0.11 MB`。

这说明问题可复现、内存信号清晰、修复前后版本可固定，适合验证内存测量能力。
但进一步检查发现，官方修复新增的是调用者需要主动使用的 `stream=True`，不是同一调用
方式下的透明优化。若 benchmark 根据版本自动切换参数，会泄露官方解法且破坏同 workload
对比，因此暂不把它作为首个 DeepSeek 代码补丁闭环任务。

### 当前边界与下一步

当前闭环的候选接受条件仍以 pyperf 运行时间提升为主。内存任务不能直接沿用该规则，
否则可能拒绝“显著省内存但没有加速”的正确补丁。下一步先实现按任务类型选择接受指标：
内存任务以峰值内存下降为主，运行时间只用于防止严重回退；完成后再运行 DeepSeek 闭环。

## 2026-09-21：内存目标的接受条件

### 增量考虑

内存优化不能继续使用“必须加速 3%”作为接受条件。框架新增显式
`optimization_objective`，默认仍是 `runtime`；配置为 `memory` 时，候选以
`tracemalloc_peak_bytes` 的下降比例作为主指标，目标 benchmark 和原始 workload 的
运行时间只作为最大退化护栏。

### 实现与验证

- 新增 Baseline/候选/Human Fix 的内存对比结构，并写入 evaluation、CSV、summary、
  release candidate 和中文报告。
- 内存候选必须功能正确、资源测量成功、峰值内存达到最低下降比例；超过允许的运行时间
  退化会被拒绝。
- 显式内存目标会补充选择 tracemalloc；原始规则分类结果保持不变，并明确记录 profiler
  是分类选择还是实验目标要求。
- 原有 runtime 决策路径保持兼容。
- 本机全量回归 `71/71` 通过；Linux 服务器全量回归 `71/71` 通过。

### 候选复核

同时复核了 more-itertools PR #1155 的 `islice_extended` 优化。同一负索引 workload
在 Python 3.11 上测得 tracemalloc 峰值仅从约 `7.31 KB` 降到 `6.71 KB`（约 8%），
且该环境中运行时间反而增加，因此不选作第一个清晰的内存闭环样本。这一失败筛选保留，
避免为了尽快闭环而挑选证据不够强的任务。

## 2026-09-22：urllib 真实内存任务复测通过

筛选到 CPython PR #96763：`urllib.parse.unquote()` 与 `unquote_to_bytes()` 在旧实现中
会产生与输入规模同阶的大量中间对象；官方合并修复保持调用方式不变，改用
`bytearray` 和生成器。官方报告极端输入下 `unquote_to_bytes` 内存降至不足三分之一，
但可能慢约 10%～20%，适合验证“内存主指标 + 时间退化护栏”。

- Baseline：`1bb68ba6d9de6bb7f00aee11d135123163f15887`
- Human Fix：`2e279e85fece187b6058718ac7e82d1692461e26`
- 无 LLM 复测脚本：`scripts/validate_urllib_memory_task.py`
- 第一次服务器产物：`artifacts/urllib_memory_feasibility/server_20260921_01`
- 第一次服务器日志：`artifacts/urllib_memory_feasibility/server_20260921_01.log`
- 离线重跑产物：`artifacts/urllib_memory_feasibility/server_20260922_02`
- 离线重跑日志：`artifacts/urllib_memory_feasibility/server_20260922_02.log`

第一次运行在进入测量前因服务器访问 GitHub 时 SSL 超时而停止，不属于实验结果。
为消除服务器网络对实验的影响，脚本新增预下载源码输入：本机按固定提交下载、编译检查并
计算 SHA-256，服务器只使用离线副本测量。两个源码哈希分别为
`a7e6c9d8184d286dc5f4c0888bb6aeafab30590317fbac56bcb55960d686cfce` 和
`1002a50162a3d4e5660962db52dc36bc70c8bc347eb2fe9c6897e975f7c2912e`。

离线重跑在独立子进程中分别测量 `unquote` 和 `unquote_to_bytes` 五次，验证结果一致性、
tracemalloc 峰值与运行时间。本次不调用 DeepSeek，最终结论为 `PASS`：主 workload
`unquote_to_bytes` 的 Baseline 峰值中位数为 `106,010,964 bytes`，Human Fix 为
`24,615,734 bytes`，下降 `76.78%`；运行时间中位数由 `0.3025 s` 降至 `0.2766 s`，
改善 `8.56%`。该任务已经达到接入正式 callback、行为检查和 DeepSeek 内存闭环的门槛。

## 2026-09-22：第一个正式内存优化闭环启动

### 增量考虑

内存接受规则虽然已经实现，但原先传给性能分析 Agent 的基线摘要仍偏重运行时间。本轮将
`optimization_objective`、tracemalloc 峰值和接受阈值明确加入模型上下文；callback 的
峰值数据也一并提供，避免仅凭函数返回后的 snapshot 低估临时分配。

### 任务接线与预检

- 使用两个官方固定 `Lib/urllib/parse.py` 文件构建离线双提交任务仓库；官方 commit 与
  本地实验 commit 的映射保存在仓库 `.git/framework_refs.json` 中。
- 只允许修改 `Lib/urllib/parse.py`；测试、benchmark 和 harness 均不可修改。
- 新增 6 项行为测试、动态目标命中、固定 pyperf benchmark、tracemalloc 资源测量和
  `prepare/run/validate` 内存 callback。
- 首次预检发现缺少 `urllib/__init__.py` 会错误导入系统标准库；动态来源检查成功拦截，
  补齐包结构后 Baseline/Human Fix 全部预检通过。
- 本机框架回归 `71/71` 通过，Linux 服务器回归 `71/71` 通过。

### 正式运行

服务器已启动 1 个独立 Run、最多 3 轮的 DeepSeek 内存闭环。候选必须功能正确、峰值
内存至少下降 30%，且 pyperf 运行时间退化不超过 25% 才能接受。官方 Human Fix 仅用于
最终对照，不加入模型上下文。

- 配置：`config/cpython_urllib_memory_e2e.yaml`
- 第一次启动日志：`artifacts/cpython_urllib_memory_e2e/server_20260922_01.log`（服务器缺少
  `.env`，在实验开始前退出，未调用模型、未计入实验）
- 正式运行日志：`artifacts/cpython_urllib_memory_e2e/server_20260922_02.log`

### 闭环初始结果与补充检查

正式闭环完成 3 轮，共 9 次模型调用、114,741 tokens。三个候选均通过功能验证；第 1
轮被接受，框架内测得 tracemalloc 峰值由 `106,010,004` 降至 `4,800,033 bytes`
（下降 `95.47%`），pyperf 中位数改善 `0.37%`。第 2、3 轮相对当前最佳版本的内存
下降均为 0%，因此被拒绝并回滚。官方 Human Fix 在同轮测量中内存下降 `76.78%`、
运行时间改善 `28.10%`；DeepSeek 补丁更省内存，但没有复现官方补丁的时间优势。

检查报告时发现首次专项 profiler callback 因同目录 `_candidate.py` 未加入动态模块搜索
路径而跳过。该问题没有影响功能、pyperf、资源测量或接受决策，因为分析 Prompt 已包含
真实峰值内存；但不能把该轮宣称为 profiler 全部成功。修复通用 callback runner，并将
CPython `Lib/` 规范化为公开模块名后，无 LLM 补充复测通过：callback 峰值约 106 MB，
CPU Top 1 和内存 Top N 均为 `urllib.parse.unquote_to_bytes`。

- 正式闭环产物：`artifacts/cpython_urllib_memory_e2e/20260922_113024_737182`
- profiler 补充复测：`artifacts/cpython_urllib_profiler_retest/server_20260922_02`
- 冻结补丁独立复测第一次启动因相对输出路径无法映射进 Docker，在测量前停止；修复后
  使用 `standard_retest/server_20260922_02` 重跑完成（不调用 LLM）。

### 无 LLM 独立复测结果

三个版本均重新通过定向测试、完整受控测试和动态目标命中。标准 pyperf 每个版本包含
60 个测量值，内存分别在独立进程中测量 5 次：

- Baseline：中位时间 `0.103576 s`，峰值内存中位数 `106,010,004 bytes`。
- Human Fix：中位时间 `0.071581 s`，加速 `30.89%`；峰值 `24,614,366 bytes`，
  下降 `76.78%`。
- DeepSeek Fix：中位时间 `0.098419 s`，加速 `4.98%`；峰值 `4,800,033 bytes`，
  下降 `95.47%`。

Human Fix 与 DeepSeek Fix 的 pyperf 差异相对 Baseline 均达到显著。三个版本各自的 5 次
tracemalloc 峰值完全一致，说明该 workload 下的内存结论可稳定复现。DeepSeek 补丁比
官方修复进一步减少约 `19.81 MB` 峰值内存，但官方修复的正常运行速度明显更好。

资源测量命令启用了 tracemalloc；DeepSeek 的实现包含大量逐段 bytearray 扩展，其
tracemalloc 插桩 wall time 明显增加。该 wall time 反映 profiler 开销，正常速度结论只
采用独立标准 pyperf。当前功能范围仍是 6 项受控测试，并非完整 CPython 官方测试套件。
加入 callback 导入与 `Lib/` 布局回归后，Linux 服务器完整回归为 `73/73` 通过；本机
对应 pyperf 测试仍受 Codex macOS 沙箱禁止读取 `sysctl` 的环境限制。

## 2026-09-22：CPython workload 自动入口验证通过

为区分“人工指定目标函数”和“框架自动发现目标函数”两个入口，新增一次无 LLM 验证。
配置只提供 CPython Baseline 与 URL 解码 workload，不填写目标文件、目标函数或可修改文件。
框架在 Docker 中运行 workload，用 cProfile 排名后，本机和 Linux 服务器均自动将
`urllib.parse.unquote_to_bytes` 选为 Top 1，并将可修改范围收敛到
`Lib/urllib/parse.py`。本机与服务器的自身耗时占比分别为 59.50% 和 58.82%。

- 配置：`config/cpython_urllib_auto_target.yaml`
- 无 LLM 入口：`scripts/validate_auto_target_entry.py`
- 服务器结果：`artifacts/cpython_urllib_auto_target/server_20260922_01`
- LLM 调用：0 次；服务器完整回归：74/74 通过。

这说明同一个 CPython 任务既可以从人工目标入口进入，也可以从 workload 自动入口找回
目标函数。

## 2026-09-22：性能分类开始控制 profiler 与目标选择

自动入口的执行顺序已从“固定运行 cProfile”调整为“多规模资源测量 → 性能分类 →
profiler 路由 → 专项 Top N → 选择目标”。CPython workload 使用 20,000 和 200,000
两个规模测量，本机和 Linux 服务器均分类为高证据 `mixed`：既有 CPU 信号，也有内存
信号，I/O 信号为否。因此框架自动执行 cProfile 与 tracemalloc，并在确认存在内存信号、
本次目标为内存优化的前提下，使用 tracemalloc 报告选择目标。

服务器 tracemalloc Top 1 为 `urllib.parse.unquote_to_bytes` 的 `return b''.join(res)`，
占仓库内存活分配约 96.92%；框架自动将唯一可修改文件限制为 `Lib/urllib/parse.py`。
预期函数只用于排名完成后的验收，没有参与分类或排序。实验未调用 LLM，服务器完整回归
`76/76` 通过。

- 本机结果：`artifacts/cpython_urllib_routed_target/local_20260922_01`
- 服务器结果：`artifacts/cpython_urllib_routed_target/server_20260922_01`

当前 I/O 路由仍只有进程级读写总量，无法据此定位源码函数；只有 CPU 与内存 profiler
已经能直接参与自动目标选择。下一步应补充可归因到文件、调用或系统调用的 I/O 热点工具，
或者先在另一项 CPU/内存真实任务上复核路由泛化性。

## 2026-09-23：自动入口完整 DeepSeek 内存闭环通过

使用固定可信的 CPython URL 解码 workload，运行“多规模分类 → profiler 路由 → 自动目标
选择 → DeepSeek 补丁 → 功能验证 → 内存与 pyperf 验收”完整链路。配置没有目标文件、目标
函数或可修改文件。正式服务器运行的前置分类为高证据 `memory`，自动只执行 tracemalloc，
并从内存 Top 1 选择 `urllib.parse.unquote_to_bytes` 与 `Lib/urllib/parse.py`；之后才开始模型调用。

3 轮共调用模型 9 次、使用 108,205 tokens。3/3 候选功能正确：第 1 轮峰值内存下降
95.47%，被接受；第 2、3 轮相对当前最佳版本均没有继续降低内存，因此被拒绝并回滚。
冻结补丁的无 LLM 标准复测再次通过：Baseline、Human Fix、DeepSeek Fix 的内存峰值中位数
分别为 106,010,004、24,614,366、4,800,033 bytes；DeepSeek Fix 内存下降 95.47%，
pyperf 运行时间改善 3.02%。每个版本的内存均在独立进程中测量 5 次。

- 完整闭环：`artifacts/cpython_urllib_auto_memory_e2e/20260923_084643_204419`
- 无 LLM 复测：`artifacts/cpython_urllib_auto_memory_e2e/20260923_084643_204419/standard_retest/server_20260923_01`
- 冻结补丁：`artifacts/cpython_urllib_auto_memory_e2e/20260923_084643_204419/release_candidate/best.patch`

同一 workload 在前一轮服务器复测中曾因 CPU 比例略高而分类为 `mixed`，本次正式运行的
CPU 比例中位数为 0.7446，略低于 0.75 阈值，分类为 `memory`。两次都正确选择并执行了
tracemalloc，但说明 CPU/mixed 标签在阈值附近可能波动；后续应把“信号集合与最终 profiler
是否正确”作为主要验收，不把单一标签完全一致当成必要条件。
