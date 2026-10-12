# 55 题不付费准备分类

批次 `failed55-prepare-20261010T123140Z`，2026-10-10 22:43（北京时间）已结束。
7 题可准备，48 题未通过。下面只给这 48 题分类。可准备不等于 Agent 已经运行。

## 运行器或适配器问题（8）

这些题没有证明项目本身不可构建。

| 题 | 现象 |
| --- | --- |
| Kafka `39eb31f` | 准备进程重启后工作区已存在。运行器拒绝继续，没有进入 Gradle。 |
| Kafka `59a75f4` | `build.gradle` 写的是 `gradleVersion = "$versions.gradle"`。适配器只认识字面版本号。 |
| Kafka `9bb2f78`、`c8af740`、`e2e2c62` | 下载 Gradle 时 `URLError` 超时。 |
| Presto `659c3ee`、`9e010a7` | `git fetch` 三次后仍退出 128。 |
| Presto `c3cb7a9` | Maven 已经 `BUILD SUCCESS`。随后适配器找不到 `classpath-presto-main.txt`。 |

## 项目构建或评测门禁（40）

| 类 | 题 | 说明 |
| --- | --- | --- |
| Presto 浅历史 | `000fa29` `20dcaed` `239f726` `290f5be` `297b089` `3a4f2e3` `4e71bf3` `53aa7f6` `60a5a5c` `6908344` `8abba9e` `8d7f587` `a26f440` `aed4c9a` `b54d248` `bfb18d6` `ee74e4b` `efd0834` `fa655f6` `fdb7611` | 父提交上的本地 tag 没有阻止 `git-commit-id-plugin` 走到浅历史之外。20 题。 |
| FindBugs 2.5.2 | `3f63ade` `46d219f` | `-Dfindbugs.skip=true` 没有拦住该插件。2 题。 |
| Netty 无关测试编译 | `2791f0f` `687308b` `83a19d5` `87ec2f8` `95b8db0` `9abeaf1` `ab8c4f2` `b2eaab0` `b72fea3` `dd69a81` `deea51e` `e542a2c` `feb804d` | 排除 `PendingWriteQueueTest` 后，`ByteToMessageCodecTest` 或 `ByteToMessageDecoderTest` 仍编译失败。13 题。 |
| 基准接口 | Netty `7b91edd` | 官方基准调用原版私有 `getIPv6ByName`。不把方法改成 public，也不删基准。 |
| Kafka JMH 编译 | `8dff0b1` | Gradle 5.6.2 已能运行。`AclAuthorizerBenchmark` 编译找不到符号。 |
| Kafka 旧插件 | `c7bc8f7` | 无 wrapper 时已解析到 Gradle 3.5。随后 `grgit`、`gradle-versions-plugin`、`shadow` 无法解析。 |
| 原版测试失败 | Kafka `4fa5bdc`、`e3ccf20` | 构建已完成。沙箱里 4 个测试容器、42 个测试全部失败。这是测试门禁，不是不能构建。 |

## 尚未实施的适配修改

1. 本批次中断留下的工作区应清理后重试，不能把“工作区已存在”记成题目失败。
2. 解析 `gradleVersion = "$versions.gradle"` 这种间接版本。
3. Gradle 下载超时单独重试；超时不是项目构建失败。
4. Presto `c3cb7a9` 在 Maven 成功后改用实际生成的 classpath 文件。
5. `git-commit-id-plugin` 需要另一种跳过方式。不能把修复提交拉进 Agent 工作区。
6. FindBugs 2.5.2 改用该版本真正识别的跳过方式，三版本一致。
7. 无关测试排除改为循环，直到没有新的非本题测试编译错误。当前一轮不够。

## 测试排除清单

只排除不在本题指定测试里的文件，三版本使用同一清单：

- `**/PendingWriteQueueTest.java`
- `**/ByteToMessageCodecTest.java`
- `**/ByteToMessageDecoderTest.java`

不排除 Netty `7b91edd` 的 `GetIpV6ByNameBenchmark`。不删除 Kafka `4fa5bdc` 和 `e3ccf20` 里失败的测试。
