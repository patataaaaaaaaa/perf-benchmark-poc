# 官方路线与当前适配路线核对（2026-10-11）

本轮响应用户对大量环境失败的疑问，只读核对公开官方脚本、服务器上的官方脚本副本及本地适配器；没有执行官方脚本、停止队列、改运行参数或增加模型调用。

## 结论

目前不是“只把 call_llms 换成 CodexCLI”。我们还重写了任务状态准备、依赖路径、测试启动及正式测量。
这些差异中已经发现明确的适配缺陷，不能把全部失败归给 benchmark、Java 或 Agent。
尚未对失败题完成官方原生执行路线的逐题对照，因此也不能宣称官方路线一定全部可运行。

## 已确认差异

| 项目 | 官方公开脚本与服务器副本 | 当前适配器 | 风险/已见问题 |
|---|---|---|---|
| 原版状态 | run_jmh先checkout fix，再mixed reset到parent，仅restore元数据source_code指定的生产文件；其他工作区文件仍为fix版本 | 完整fix-parent工作区，仅补缺失benchmark/test文件 | 官方保留的其他文件可能涉及API/构建依赖；当前两个harness/API失败可能与状态差异有关，但需要逐题diff验证因果 |
| 构建/测试 | 项目Maven/Gradle入口及模块测试 | reactor准备后自组装依赖路径，重新编译指定生产源码overlay，并直接启动JUnit/TestNG | Netty缺未重打包JCTools；Presto跨模块test-classes污染导致监听器不兼容 |
| 历史环境 | 脚本本身含SNAPSHOT替换、格式检查绕过、Kafka特例等；README先要求四项目能正常编译 | 浅历史仓库、私有缓存、自选工具版本 | 缺Git历史、旧插件/镜像、版本解析仍需环境适配；不是Python依赖安装就能解决 |
| 网络 | 官方测试直接在宿主项目环境启动，本身没有此Codex网络沙箱前置门槛 | 所有新题必须先在断网Agent沙箱通过选定测试 | 需要本机测试服务的Kafka案例被挡在模型调用前，不等于模型失败 |
| JMH | Netty/Presto/Kafka脚本预热10、测量50、fork1；Presto/Kafka另指定每次1秒 | 预热5、测量10、fork2、每次1秒 | 当前是自定义统一协议，不是完全复现官方测量配置 |

官方原版与完整parent不等价，属于研究条件而不是谁天然更正确：复现论文应先匹配其任务状态；严格parent评测可保留为另一个明确披露的条件，不能悄悄混用。

## 对先前表述的纠正

之前记录“官方JMH仍2fork、5warmup、10measurement”不准确，现更正为“使用官方benchmark案例，在我们自定义2/5/10协议下进行三版本测量”。
现有数据保留，不抹去历史参数，不认定全部无效；在确认任务状态、依赖/测试路径可靠前，不直接对照论文数值或声称严格复现。
正在运行的批次不热修改参数。若改协议，单独命名新批次，并对三版本一致重测；既有patch通常可以复用，不必重新付费生成。

## 建议后续路线（尚未执行）

在独立工作区选Netty缺依赖、Presto监听器以及harness/API不兼容代表题，先做不付费的官方路线对照。
记录官方工作区构造、依赖版本、测试实际发现数量与返回码、JMH配置和输出，再与当前路线比较。
原生路线先跑通后，以最小接入替换patch生成环节；复用项目原生构建测试入口，给Agent暴露相同的test/benchmark工具。
保留会话、目录、费用、超时和记录管理；隔离执行作为外层环境，不由统一适配器重新猜各项目的依赖与测试语义。
官方脚本含git reset/clean等命令且存在路径/命令细节需要核验，不能直接在共享仓库或已有Agent工作区运行。

## 核对来源

- [官方README](https://github.com/icetlab/BenchLLMRealSE/blob/main/README.md)
- [run_unit_test.py](https://github.com/icetlab/BenchLLMRealSE/blob/main/run_unit_test.py)
- [Netty JMH脚本](https://github.com/icetlab/BenchLLMRealSE/blob/main/Scripts/run_jmh/netty.sh)
- [Presto JMH脚本](https://github.com/icetlab/BenchLLMRealSE/blob/main/Scripts/run_jmh/presto.sh)
- [Kafka JMH脚本](https://github.com/icetlab/BenchLLMRealSE/blob/main/Scripts/run_jmh/kafka.sh)

服务器BenchLLMRealSE是无.git的文件副本，无法读取commit指纹；此次没有伪造版本号。副本对应脚本SHA256如下，已核对其原版构造及JMH参数与上述公开代码相同：

- netty.sh: 295184e61ea1a13747cd32637f5eb2958fe9692449416087e19e96bf4da4f499
- presto.sh: c3f945f468fc9b4cb77d9ef33032f8390514c59fb1c4b34c698bfb9073eca11e
- kafka.sh: 06ace328dfd22ad97daedf0ac511bf67dca187516752b0cf831aa4d5bf3411d2

本地实现证据：scripts/run_benchllm_full_batch.py的prepare_project及全target目录拼接；scripts/benchllm_project_tools.py的overlay及测试runner；scripts/benchllm_java_tools.py的jmh_command。

