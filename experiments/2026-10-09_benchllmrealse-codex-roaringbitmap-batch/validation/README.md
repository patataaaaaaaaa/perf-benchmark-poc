# 三题的独立功能诊断

这不是新一轮 Agent 优化，也不是完整 JUnit 套件或性能测量。检查对象为已冻结的原版、开发者版和 10 个 Agent 补丁；未修改候选源码、未调用模型。

## 检查与结果

| 任务 | 检查方法 | 实际结果 |
| --- | --- | --- |
| 34bce1b | 6 个特殊整数 + 固定种子 10000 个随机整数，每个覆盖 10 个合法 pos/count 组合，以 byte[] + arraycopy 为参照 | 四个 Agent 和开发者版的 100060 次合法输入比较均通过 |
| 34bce1b | 负数位置、越界位置、负数/越界 count 的异常行为兼容性 | 开发者版与四个 Agent 都和原版不同；不能简单算作 Agent 独有的功能错误 |
| b5b4af6 | 每次修改前先查询，再做添加、删除、范围添加/删除/翻转、单元素翻转；两种容器各 4000 步，以 BitSet 为参照 | 原版、开发者版及四个 Agent 均通过 |
| b5b4af6 | 先查询，再通过 readExternal 在同一对象读入不同数据 | 各版本均通过；P3 的 readExternal 末尾确实有缓存失效处理 |
| b5b4af6 | 两个容器共享 heap/direct CharBuffer，先查询 A，再由 B 延长同一个 run | P1/P3/P4 均返回过期数量；原版、开发者版、P2 均通过 |
| 53ba593 | RoaringBitmap 与 MutableRoaringBitmap，各四种初始化场景，每种 2000 步新/重复混合添加；用 HashSet 校验返回值、数量与最终内容 | 原版、开发者版、P1/P2 均通过；包含 4096 到 4097 元素附近的数组→位图转换输入 |

checkedAdd 四种初始化场景为小集合、runOptimize 后的连续数据、接近数组容量转换阈值的数据、稀疏数据。输入含跨高位键、负整数与整数边界，并立即重复添加每个输入检查 false 返回值。并非穷尽所有输入或所有容器转换路径；P1 的额外 contains(subset) 修改没有由这一专项诊断全面覆盖。

缓存的两个随机操作序列接收并继续使用容器方法返回的对象，容器可以转换类型，因此不能把 4000 步都解释为一直在 RunContainer 内执行。它们不能替代缓存各内部路径的完整覆盖。

## 共享缓冲区的最小反例

```java
CharBuffer buffer = CharBuffer.wrap(new char[]{0, 0}); // 一个 run，只包含 0
MappeableRunContainer a = new MappeableRunContainer(buffer, 1);
MappeableRunContainer b = new MappeableRunContainer(buffer, 1);
a.getCardinality(); // 1，预热 A 的缓存
b.add((char) 1);    // 原地延长同一个 run，不需要扩容
a.contains((char) 1); // true：A 的内容也已经改变
a.getCardinality();   // 应为 2；P1/P3/P4 仍返回 1
```

这个反例使用公共构造函数，该函数注明容器由传入的 CharBuffer 支撑，源码直接保存其引用。缓存补丁没有感知经另一对象发生的底层修改，导致 contains 与 getCardinality 不一致。这是在共享缓冲区使用方式下可复现的语义回归；不能据此断言单对象、无共享的所有缓存使用都错误。

位移函数的非法参数则是不同性质的问题：已有说明没有明确非法参数的契约，开发者版也不再抛出原版异常。当前将其记录为兼容性差异，不直接否定合法输入的优化收益。

## 复现方式

服务器 Java：OpenJDK 11.0.32.1；编译参数 `javac --release 8`。随机种子固定为 20261009。

将本目录的 FunctionalProbe.java 和 run_probes.py 放到服务器的同一个诊断目录，然后执行：

```bash
python3 run_probes.py --batch-root /path/to/roaring-batch-20261009T085300Z
```

可加 `--task 34bce1b`、`--task b5b4af6` 或 `--task 53ba593` 单独检查。要求该批次已有 support/manifest.json、harness.jar 和冻结 workspaces。

程序在临时目录编译当前候选源码，放在 classpath 最前面，保证不会误测 harness.jar 中的原版类。不会写入候选工作区。输出逐版本 JSON 行，Java 程序用 PASS/FAIL 记录每项诊断，**进程退出码为 0 不等于全部诊断通过**，应检查 stdout 中的每项状态。

归档结果见 `../results/functional_probe.json`。本次未重跑 JMH，也未新增供 Agent 使用的 skill、MCP 工具或外层循环。
