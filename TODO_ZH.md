# 项目进度与待办清单

本文件用于长期记录框架的实现进度和暂定设计。完成任务后只把
`[ ]` 修改为 `[x]`，不得删除已经完成的条目；如果设计发生变化，保留原条目并在其下方补充说明。

## 一、已经完成

- [x] 验证 DeepSeek V4 Pro 可以生成 pyperf benchmark。
- [x] 验证 benchmark 失败后可以把真实错误反馈给模型进行自动修复。
- [x] 验证 benchmark 能通过语法、导入、运行和目标命中检查。
- [x] 在 More-itertools 的 `triplewise()` 历史性能问题上跑通代码优化闭环。
- [x] 实现候选补丁的修改文件白名单和 unified diff 检查。
- [x] 实现定向测试、完整单元测试和额外行为检查。
- [x] 实现运行时间、CPU、内存、I/O 和模型成本的基础记录。
- [x] 实现补丁接受、拒绝、回退以及最大循环次数控制。
- [x] 将模型生成阶段与无 LLM 标准复测阶段分开。
- [x] 使用固定 workload 和 `cProfile` 完成第一版自动热点定位。
- [x] 在不向排名逻辑提供 `target_symbol` 的情况下，将 `triplewise()` 定位为第一热点。
- [x] 将 profiler 原始结果整理为统一的 `Hotspot` 结构并输出 JSON。
- [x] 跑通“只给仓库、不指定目标函数和 testcase”的自主入口：扫描 150 个场景，
  DeepSeek 选择并生成 workload，沙箱验收后进入自动热点与优化闭环。
- [x] 修复类方法热点丢失类作用域的问题，支持解析、导入和提取
  `more_itertools.more.peekable.__next__` 这类目标。

## 二、当前 Hotspot 属性

第一版 `Hotspot` 用于表达一个被 profiler 发现的候选热点函数，目前包含：

- [x] `rank`：热点排名。
- [x] `qualified_name`：函数完整名称。
- [x] `file`：函数所在的仓库相对路径。
- [x] `line`：函数定义行号。
- [x] `function`：函数简称。
- [x] `primitive_calls`：排除递归重复计算后的调用次数。
- [x] `total_calls`：包含递归调用的总次数。
- [x] `self_time_seconds`：函数自身耗时。
- [x] `cumulative_time_seconds`：函数及其下层调用的累计耗时。
- [x] `self_time_percent`：函数自身耗时占整个 profile 的比例。

当前字段足够验证“框架能否从 workload 中自动发现 Python 函数热点”，但暂时不能覆盖完整的性能诊断。

## 三、热点分析待完善项

- [x] 当前规则：只保留目标仓库内的 Python 函数，排除测试和 benchmark 文件。
- [x] 当前规则：按 `self_time_seconds` 从高到低排序，选择 Top 1 作为修改目标。
- [x] 当前规则由框架确定，不让 LLM 任意猜测目标；Top N 证据仍提供给分析 Agent。
- [ ] 记录热点函数的直接调用者 `callers`。
- [ ] 记录热点函数的直接被调用者 `callees`。
- [ ] 记录调用边的调用次数和耗时，形成简化调用图。
- [ ] 同时考虑自身耗时和累计耗时，避免只选择入口函数或包装函数。
- [ ] 设计稳定的热点筛选规则，例如项目源码过滤、最低耗时占比和最小调用次数。
- [ ] 识别并降低模块导入、初始化代码对热点排名的干扰。
- [ ] 为名称相同但定义位置不同的函数建立稳定标识。
- [x] 记录多次 profile 的排名波动，而不是只依赖单次运行。
- [ ] 对比 `self time`、`cumulative time`、调用次数和多次运行稳定性，优化 Top 1 选择规则。
- [x] 将 profiler Top N、选择结果和耗时数据转换为 DeepSeek 可读的精简上下文。
- [ ] 让 DeepSeek 根据 Top N 热点、调用关系和源码选择优化目标，并保存选择理由。
- [ ] 区分“高频正常路径”与“可优化性能根因”，避免把机械放大的 `__next__` 等方法
  直接等同于性能缺陷。
- [ ] Top 1 连续两轮无提升时，自动尝试 Top 2/Top 3 或切换 workload，而不是只围绕
  同一目标继续生成补丁。

## 四、Workload 与性能工具

- [x] 明确 workload 是“让项目完成什么工作”的可执行场景，不是运行后产生的指标或日志。
- [x] 定义 workload 的基本组成：入口、输入、操作、规模、正确结果和运行约束。
- [x] 定义来源优先级：真实问题复现/trace、已有 benchmark、testcase、examples、LLM 候选。
- [x] 每个 workload 记录来源、可信度和是否经过人工确认；LLM 生成项默认低可信。
- [x] 明确区分 workload 和 profiler：workload 定义执行场景，profiler 负责采集数据。
- [x] 第一版复用 Python 内置 `cProfile`，不自行实现性能采集器。
- [x] 使用 pyperf 负责优化前后的稳定运行时间测量。
- [x] 使用 psutil 记录进程 CPU、RSS 内存和平台支持的 I/O 指标。
- [x] 使用 tracemalloc 单独记录 Python 内存分配峰值。
- [x] 优先复用目标仓库已有 benchmark 或性能测试作为 workload；已用 attrs 官方 benchmark 验证。
- [x] 第一份 `triplewise` workload 根据历史问题中的核心场景人工编写；现已另有一份 testcase 派生候选用于对照。
- [x] 扫描仓库中的 benchmark、testcase 和 examples，输出结构化 workload 候选。
- [x] 将 testcase 派生候选转换为统一 `WorkloadSpec`。
- [x] 让 DeepSeek 根据仓库测试证据补全候选执行脚本，且不直接标记为真实 workload。
- [x] 验证候选能运行、结果正确、确实执行目标仓库代码、重复运行基本稳定。
- [x] 提供显式人工确认与冻结入口；要求审阅者、理由和准确 SHA-256，候选证据保持不变。
- [ ] 一个项目有多个入口时保留多个 workload，不强行合并为一个“万能场景”。
- [ ] 自主入口不要只选择一个 testcase；保留多个候选 workload，并比较代表性、
  profiler 结论和最终可优化性。
- [ ] 评估普通 testcase 是否具有代表性；没有代表性时使用单独 workload。
- [x] 增加第一版 workload 意图保真门禁：发现关键对象构造被替换时标记 `REVIEW_REQUIRED` 并禁止冻结。
- [ ] 后续扩展保真检查，继续比较容器规模、操作序列和主 case，而不只检查关键构造器名称。
- [x] 为第一版 testcase 派生 workload 统一输入描述、结果校验和可重复运行接口。
- [x] 支持从配置文件执行一个明确指定的 workload。
- [ ] 后续再评估 py-spy、Scalene 或 Linux perf，不在第一版同时接入。
- [ ] 为 CPU、内存和 I/O 分别保存指标，不把它们强行合并成一个总分。

## 四点一、多维瓶颈分类

当前只实现了基于 `cProfile` 的运行时间热点 Top N。CPU、内存和 I/O 已有
workload 进程级总量，但尚未归因到具体函数或代码位置。后续保持不同类型指标
独立展示，不直接合并成一个模糊的“综合热点分数”。

- [x] 输出 Python 函数运行时间 Top N，包括自身耗时、累计耗时和调用次数。
- [x] 记录整个 workload 的 wall time、user/system CPU、峰值 RSS 和可用 I/O 总量。
- [x] 记录整个 workload 的 tracemalloc peak。
- [x] 增加第一版可解释规则分类器，输出 `cpu_bound`、`memory`、`io`、`mixed` 或 `unknown`。
- [x] 分类结果同时保存 `high/medium/low` 证据强度和中文判断依据；该强度不是统计概率。
- [x] 用户声明的优化目标只作为上下文保存，不覆盖实际测量证据。
- [x] 使用纯计算、内存增长和文件读写三个 Docker 受控 workload 验证分类路由。
- [x] 在固定 Linux 服务器上复测三类受控 workload，分类结果 3/3 正确，完整回归 57/57 通过。
- [x] 在服务器 Docker 中增加真实项目样本：openpyxl 检出 CPU+内存混合信号，fsspec 检出 I/O 信号。
- [x] 真实任务按“目标资源信号是否检出”验收，同时保留 `mixed` 结果，不强制单标签。
- [x] I/O 规则排除 Python 解释器固定启动读数，要求真实读写字节或随输入规模增长的操作数。
- [x] 使用第二组独立真实任务校准第一版规则：cachetools 内存与 smart_open I/O 各复测三次。
- [x] 根据真实误报将“仅 I/O 操作次数”的增长门槛收紧到至少 40 次且 25%，受控三类样本回放仍正确。
- [ ] 当前阈值仍是第一版启发式规则；继续随真实任务增加记录误报和漏报，不宣称已经训练完成。
- [ ] 在积累带标签的真实任务后，对比规则分类器、Jev 和 DeepSeek 的准确率、延迟、费用及置信度校准；当前不训练小模型。
- [x] 将分类器以观察模式接入主 pipeline：优先读取原始 workload baseline，输出 `task_classification.json`，但不改变现有决策。
- [x] 增加独立内存任务和独立 I/O 任务并完成稳定性复测，已具备实现观察式 profiler 路由的条件。
- [x] 实现观察式 profiler 选择计划：CPU→cProfile、内存→tracemalloc、I/O→进程 I/O，mixed→组合选择。
- [x] 执行观察式 profiler 计划并保存统一热点证据：CPU 可复用 cProfile，配置 callback 后可执行 tracemalloc，I/O 先复用进程总量。
- [x] 第一版路由只决定采集什么证据，不直接改变补丁接受条件；结果稳定后再升级为正式控制流。
- [x] 将分类与 profiler 路由前移到自动目标选择之前；CPU/内存分类结果现在会实际决定
  执行 cProfile、tracemalloc 或二者，并由匹配的 Top N 选择目标函数。
- [x] CPython `urllib` 多规模 workload 自动检出 CPU+内存混合信号，执行两种 profiler，
  最终由 tracemalloc Top 1 找回 `unquote_to_bytes`；本机与服务器均通过。
- [x] 完成自动入口的 DeepSeek 完整内存闭环：不提供目标函数，自动分类并用 tracemalloc
  选中 `unquote_to_bytes`，3/3 候选功能正确、1/3 被接受；无 LLM 标准复测确认峰值内存
  下降 95.47%、pyperf 运行时间改善 3.02%。
- [ ] CPU 比例在 0.75 阈值附近会使同一任务在 `memory` 与 `mixed` 间波动；后续按信号集合
  和 profiler 路由正确性验收，并用更多重复或阈值滞回减少标签抖动。
- [x] 实现 tracemalloc snapshot 的 Python 内存分配 Top N 解析器，包含文件、行号、函数、分配大小和次数。
- [x] 定义 `prepare_workload/run_workload/validate_workload` callback，并在对象释放前采集 tracemalloc snapshot。
- [x] 在服务器 Docker 受控仓库中验证 callback：16 MiB 分配的 Top 1 精确定位到目标函数与源码行。
- [x] 复核 CPython `tarfile` 历史内存问题：固定 Baseline `097b7830`、Human Fix
  `50fce89d` 并完成轻量复现；但官方修复需要调用者新增 `stream=True`，暂不作为
  “同一 workload 透明优化”的首个闭环任务。
- [x] 增加“内存优化”专用接受条件：功能正确、原始 workload 正确、峰值内存明显下降；
  运行时间只作为护栏，不再错误地要求内存任务必须加速。
- [x] 显式内存目标会确保执行 tracemalloc，即使单次资源分类没有检出内存增长；
  分类原始结论仍保留，不会被改写。
- [ ] 继续筛选一个调用方式不变、官方修复透明降低内存的历史任务，编写可信 callback
  与行为检查后运行完整 DeepSeek 内存优化闭环。
- [x] CPython `urllib.parse.unquote_to_bytes`（PR #96763）完成无 LLM 离线复测：同一
  workload、固定官方 Baseline/Human Fix、5 次独立进程测量；峰值内存下降 76.78%，
  运行时间改善 8.56%，达到接入正式内存闭环的门槛。
- [x] 为 `urllib.parse.unquote_to_bytes` 编写正式 profiler callback、行为检查和内存任务
  配置；Baseline/Human Fix 均通过 6 项行为测试、动态目标命中和资源测量。
- [x] `urllib.parse.unquote_to_bytes` 完成 3 轮 DeepSeek 内存优化闭环：3/3 候选功能
  正确，第 1 轮被接受；框架内测得峰值内存下降 95.47%，运行时间改善 0.37%，后两轮
  因内存没有继续下降而正确拒绝并回滚。
- [x] 修复 callback 同目录 helper 导入和 CPython `Lib/` 模块名称规范化；无 LLM
  profiler 补充复测通过，CPU Top 1 与内存 Top N 均命中目标函数。
- [x] 完成冻结 `best.patch` 的无 LLM 独立标准复测：三个版本均通过功能检查；
  DeepSeek Fix 的峰值内存下降 95.47%、正常 pyperf 运行时间改善 4.98%，5 次内存
  样本完全一致；Human Fix 分别为下降 76.78% 和加速 30.89%。
- [ ] 扩大 `urllib` 行为测试或在完整 CPython 仓库中运行官方测试，确认受控任务切片之外
  的兼容性；当前不能仅凭 6 项受控测试宣称补丁已达到可直接上游合并的质量。
- [ ] 区分 Python CPU 热点与系统 CPU 总量，避免把 wall time 直接当作 CPU 时间。
- [ ] 评估使用 py-spy 或 Scalene 生成低开销 CPU Top N，不在第一版重复实现 profiler。
- [x] 对 I/O 先判断任务是否属于 I/O 型；CPU 型任务只保留进程级 I/O 总量。
- [ ] I/O 型真实任务再增加文件、调用或系统调用级别的 I/O 热点证据。
- [ ] 将不同类型的 Top N 分别传给性能分析 Agent，并要求它先判断瓶颈类型再提出修改。
- [ ] 记录优化前后各类指标变化，识别“运行时间变快但内存或 I/O 变差”的情况。

## 五、基础沙箱

- [x] 实现一个最小可用的 Docker 沙箱运行器。
- [x] workload、测试、benchmark 和候选代码都在沙箱内执行。
- [x] 当前热点发现 workload 在沙箱内执行。
- [x] DeepSeek API 密钥只保留在沙箱外的主控进程中，宿主环境变量不自动传入。
- [x] 沙箱配置为默认禁止网络访问。
- [x] 使用非 root 用户运行代码。
- [x] 配置执行时间、CPU、内存和进程数限制，并截断保存的超量输出。
- [x] 当前热点发现任务使用独立的一次性工作目录。
- [x] 不使用 Git worktree；实验代码使用 detached HEAD 的独立 clone。
- [x] clone 不再使用 `--shared`，避免缓存清理或 Git GC 使实验副本失效。
- [x] 执行结束后保存必要日志、补丁和指标，并默认删除实验代码副本。
- [x] 无 LLM 复测需要时，可由基线 commit 与已校验的 `best.patch` 重建临时副本。
- [x] 增加“接受→拒绝→再次接受”的回滚测试，确认拒绝候选后恢复上一最佳补丁。
- [x] 生成 `release_candidate`，记录最佳补丁哈希、基线提交和两类性能证据。
- [x] 提供显式发布命令：只在干净且基线匹配的目标分支应用补丁并重跑功能测试。
- [x] 发布阶段不自动 merge 或 push，最终合并保留人工确认。
- [x] 验证超时程序、超内存程序和尝试访问网络的程序会被正确阻止。
- [ ] 在 Docker 不可用时提供明确失败信息，不静默回退到不安全执行。

## 六、自动热点到优化闭环

- [x] 配置支持 `target_mode: auto`，不再强制人工填写 `target_symbol`。
- [x] 自动热点阶段输出稳定的目标文件和目标函数接口。
- [x] 将自动选择的目标传给 benchmark 生成阶段。
- [x] 将目标源码、必要 imports、相关测试和 profiler 证据传给性能分析 Agent。
- [x] 将自动选择的目标传给动态目标命中验证。
- [x] 保留目标 microbenchmark，用于解释目标函数本身的变化。
- [x] 保留原始 workload，作为最终端到端性能接受条件。
- [x] 只有功能正确、目标 microbenchmark 和原始 workload 都明显变快时才接受补丁。
- [x] 自动优化失败时回退到当前最佳版本，并把真实失败信息传给下一轮。
  More-itertools 自主 workload bad case 中两个功能正确但变慢的补丁均被拒绝，
  最佳版本保持 Baseline。

## 七、简化验证顺序

- [x] 已知仓库、已知 workload：确认 profiler 能重新找到 `triplewise()`。
- [x] 使用简化沙箱运行同一个 workload，并得到与本机直接运行一致的热点结论。
- [x] 在沙箱中模拟超时、超内存和网络访问，验证限制生效。
- [x] 把自动发现的 `triplewise()` 接入现有优化闭环。
- [x] 去掉人工目标配置，完成一次从 workload 到最终补丁的端到端运行。
- [x] 在第二个真实仓库 attrs 中，从已有 benchmark 派生 workload，并稳定找回 `attrs.asdict()` 热点。
- [x] 在 CPython `urllib` 任务中去掉人工目标提示，仅凭 workload 使用 cProfile 自动找回
  `urllib.parse.unquote_to_bytes` Top 1；本机与服务器结果一致，且全程不调用 LLM。
- [ ] 增加 2～3 个具有已知性能修复的真实任务，形成无 RAG 基线。
- [ ] 比较不同任务中的热点定位准确性、功能正确率和性能提升率。
- [ ] 在无 RAG 基线稳定后加入 RAG，并进行同条件对照实验。

## 八、当前明确不做

- [x] 第一版不自动扫描整个测试集并猜测哪个 testcase 最适合作为 workload。
  阶段调整：基础闭环稳定后已在隔离实验中实现该自主入口；首个 bad case 说明
  “能选择并运行”不等于“选择有代表性且可优化”，后续按多候选方案继续完善。
- [ ] 第一版不同时接入多个 profiler。
- [ ] 第一版不构造复杂的综合性能总分。
- [ ] 第一版不让模型修改测试、benchmark 或实验框架。
- [ ] 在基础沙箱完成前，不执行来源不明的仓库和 workload。
- [ ] 没有真实问题描述、运行记录或人工确认时，不宣称 LLM 候选代表真实业务 workload。
