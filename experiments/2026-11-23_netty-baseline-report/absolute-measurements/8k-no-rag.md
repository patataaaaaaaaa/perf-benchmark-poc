# OpenCode 8K 无 RAG逐场景绝对测量值

[返回汇报正文](../README.md)

本组覆盖 8 题、76 个场景。下表各值为同批次五个有效 JMH 区组分数的算术平均，最多保留 9 位有效数字。吞吐量越高越好，平均耗时和各项资源消耗越低越好。1 MiB = 1,048,576 字节。

## 2791f0f

### scheduleLots（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleLots` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 306.649193 | 9012767.15 | 6664254.26 | 243.645828 | 245.737156 |
| 开发者版 | 703.199227 | 4649735.06 | 6664250.18 | 247.512734 | 249.837969 |
| 候选版 | 633.731294 | 5036855.44 | 6664250.65 | 250.568422 | 252.387891 |

## 5a9b28a

### plainNew

`io.netty.microbench.util.RecyclerBenchmark.plainNew` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 9.93281594 | 10.0949024 | 80.0000067 | 224.24625 | 226.651047 |
| 开发者版 | 9.92624465 | 10.0884582 | 80.0000067 | 224.744562 | 227.214406 |
| 候选版 | 9.96557892 | 10.1252711 | 80.0000067 | 224.443391 | 226.702594 |

### producerConsumer

`io.netty.microbench.util.RecyclerBenchmark.producerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 56.09837 | 56.0470629 | 0.0141016871 | 134.652344 | 135.770297 |
| 开发者版 | 53.7272665 | 53.6159679 | 0.00863537927 | 125.776297 | 126.556969 |
| 候选版 | 94.1844423 | 94.0959064 | 0.00564843701 | 121.449906 | 122.279172 |

### recyclerGetAndOrphan

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndOrphan` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 15.5198836 | 15.7379737 | 83.0000105 | 226.25975 | 228.136828 |
| 开发者版 | 16.1640961 | 16.3922526 | 83.0000109 | 226.603906 | 228.550656 |
| 候选版 | 14.5453223 | 14.7502 | 83.0000099 | 226.677437 | 228.903984 |

### recyclerGetAndRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 26.8633551 | 27.0912608 | 1.81971117e-05 | 117.214875 | 118.143281 |
| 开发者版 | 28.3200372 | 28.5565515 | 1.92608816e-05 | 118.046219 | 118.935453 |
| 候选版 | 26.589868 | 26.8184042 | 1.80027901e-05 | 117.542016 | 118.193172 |

### recyclerGetAndUnguardedRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndUnguardedRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 27.7961744 | 28.0408212 | 1.88814728e-05 | 116.963484 | 117.840594 |
| 开发者版 | 28.3976509 | 28.6436867 | 1.93037096e-05 | 117.573844 | 118.636484 |
| 候选版 | 26.8393028 | 27.071775 | 1.82400585e-05 | 117.761016 | 118.512125 |

### unguardedProducerConsumer

`io.netty.microbench.util.RecyclerBenchmark.unguardedProducerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 57.8206274 | 57.6996772 | 0.110078056 | 145.238672 | 146.401859 |
| 开发者版 | 51.29055 | 51.2394139 | 0.00328648676 | 123.72025 | 124.49575 |
| 候选版 | 98.6125879 | 98.4551668 | 0.00616646296 | 123.453063 | 124.333328 |

## 67d3a78

### arraysBytesEqual（size=10）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6.04170078 | 6.09312014 | 4.25490277e-06 | 99.5623594 | 100.28625 |
| 开发者版 | 6.04320582 | 6.09303297 | 4.25201727e-06 | 97.2371719 | 98.0581406 |
| 候选版 | 6.04644972 | 6.09966447 | 4.254961e-06 | 99.0125 | 99.731125 |

### arraysBytesEqual（size=50）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 17.860291 | 18.020461 | 1.25884869e-05 | 99.3955469 | 100.035906 |
| 开发者版 | 17.8627477 | 18.0145155 | 1.25789086e-05 | 99.1376719 | 99.9300781 |
| 候选版 | 17.8635546 | 18.0201004 | 1.25919493e-05 | 98.313 | 99.1642813 |

### arraysBytesEqual（size=100）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 32.5445194 | 32.8352847 | 2.2930102e-05 | 98.6857188 | 99.3559063 |
| 开发者版 | 32.5438996 | 32.8238331 | 2.29446293e-05 | 99.3335312 | 100.093641 |
| 候选版 | 32.5478702 | 32.8405225 | 2.29341277e-05 | 97.7974375 | 98.62275 |

### arraysBytesEqual（size=1000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 296.977653 | 299.701136 | 0.000209361439 | 99.5429063 | 100.235766 |
| 开发者版 | 297.204358 | 300.058438 | 0.000209516305 | 99.1021719 | 99.9258125 |
| 候选版 | 296.998374 | 299.860538 | 0.000209246147 | 99.8550156 | 100.517781 |

### arraysBytesEqual（size=10000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 2885.10396 | 2912.15352 | 0.00203380829 | 98.5731562 | 99.4940156 |
| 开发者版 | 2887.98738 | 2915.10931 | 0.00203404463 | 99.6545625 | 100.408406 |
| 候选版 | 2885.94999 | 2913.16453 | 0.00203569832 | 100.514125 | 100.942078 |

### arraysBytesEqual（size=100000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 28763.1421 | 28996.962 | 0.0202405849 | 98.4734375 | 99.0850156 |
| 开发者版 | 28875.5817 | 29143.1463 | 0.0203487001 | 99.3625625 | 100.165641 |
| 候选版 | 28822.8562 | 29071.421 | 0.0203029462 | 99.9512656 | 100.579781 |

### unsafeBytesEqual（size=10）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6.69348178 | 6.75352829 | 4.71626172e-06 | 111.088484 | 111.944781 |
| 开发者版 | 4.55258795 | 4.59185382 | 3.21042121e-06 | 110.692766 | 111.578984 |
| 候选版 | 4.88430158 | 4.9252064 | 3.44025752e-06 | 109.623328 | 110.604531 |

### unsafeBytesEqual（size=50）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 7.09316936 | 7.15162113 | 5.02117397e-06 | 111.936781 | 112.758547 |
| 开发者版 | 6.12732313 | 6.17944558 | 4.31420422e-06 | 110.779422 | 111.701047 |
| 候选版 | 6.05158742 | 6.10312043 | 4.2648844e-06 | 111.628078 | 112.282656 |

### unsafeBytesEqual（size=100）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 10.1610455 | 10.2471588 | 7.15339549e-06 | 110.260937 | 111.194906 |
| 开发者版 | 9.66115619 | 9.74217948 | 6.81155561e-06 | 111.603953 | 112.356484 |
| 候选版 | 9.28230428 | 9.36351635 | 6.53404906e-06 | 110.640953 | 111.470094 |

### unsafeBytesEqual（size=1000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 68.6253171 | 69.2319141 | 4.83924972e-05 | 111.206297 | 112.213719 |
| 开发者版 | 67.2756162 | 67.8741904 | 4.74056946e-05 | 110.560859 | 111.471609 |
| 候选版 | 66.9695725 | 67.5446243 | 4.71993772e-05 | 110.918219 | 111.747297 |

### unsafeBytesEqual（size=10000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 595.497483 | 600.476867 | 0.000419120285 | 110.579766 | 111.474016 |
| 开发者版 | 594.842023 | 599.724904 | 0.000419450725 | 109.58975 | 110.642328 |
| 候选版 | 594.750181 | 599.669766 | 0.000419229802 | 111.411313 | 112.401375 |

### unsafeBytesEqual（size=100000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6591.72934 | 6646.38107 | 0.0046508828 | 112.545844 | 113.297813 |
| 开发者版 | 6589.42789 | 6647.23896 | 0.00464068672 | 111.945344 | 112.965766 |
| 候选版 | 6127.50363 | 6177.7193 | 0.00431913431 | 112.301141 | 113.126766 |

## 687308b

### longAscii

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longAscii` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.398035453 | 2541.72131 | 5976.00169 | 224.474875 | 227.624953 |
| 开发者版 | 1.75870097 | 579.46644 | 3192.00038 | 226.899 | 229.347094 |
| 候选版 | 0.820652563 | 1234.1783 | 3192.00082 | 224.753172 | 227.771219 |

### longAsciiFirst

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longAsciiFirst` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.0370940998 | 27406.2 | 52680.0183 | 225.303031 | 228.339453 |
| 开发者版 | 0.0409867367 | 24850.0872 | 54016.0166 | 225.626688 | 228.72575 |
| 候选版 | 0.0348069777 | 29212.1191 | 54016.0195 | 224.753469 | 227.867391 |

### longUtf8

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longUtf8` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.0401670817 | 25283.0313 | 51480.0168 | 225.378891 | 228.000063 |
| 开发者版 | 0.0472517935 | 21666.0446 | 51480.0144 | 225.953719 | 229.077922 |
| 候选版 | 0.0491455593 | 21154.6096 | 51480.0141 | 225.12275 | 228.169781 |

### shortAscii

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortAscii` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 19.5949242 | 51.8381317 | 152.000034 | 225.994484 | 227.784797 |
| 开发者版 | 22.3779312 | 45.3468191 | 152.00003 | 225.325187 | 228.091453 |
| 候选版 | 20.1767367 | 50.2791176 | 152.000033 | 225.522953 | 228.383047 |

### shortAsciiFirst

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortAsciiFirst` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 2.73188815 | 370.362725 | 848.000247 | 228.133609 | 230.326203 |
| 开发者版 | 3.59928035 | 281.989425 | 848.000188 | 226.822516 | 229.690531 |
| 候选版 | 2.78689163 | 371.896341 | 848.000248 | 225.645422 | 228.380438 |

### shortUtf8

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortUtf8` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 3.09788881 | 328.596878 | 840.000219 | 226.719219 | 229.216422 |
| 开发者版 | 3.90032356 | 259.956566 | 840.000173 | 228.977703 | 230.480109 |
| 候选版 | 2.96833644 | 341.46779 | 840.000227 | 226.342031 | 229.869109 |

## 87ec2f8

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18285616.6 | 55.178684 | 120.000037 | 6014.18892 | 6015.91422 |
| 开发者版 | 33483105.5 | 30.1573074 | 56.0000201 | 5923.02859 | 5925.29297 |
| 候选版 | 18547933.5 | 54.4673143 | 128.000041 | 6042.4943 | 6044.36606 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 8762604.05 | 115.238776 | 232.000077 | 5976.81911 | 5978.74505 |
| 开发者版 | 21573138.7 | 46.9070766 | 168.000031 | 6189.76125 | 6191.48605 |
| 候选版 | 11166517 | 90.7161755 | 296.00006 | 6165.28795 | 6167.38564 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 549152.846 | 2038.74968 | 2190.40136 | 5536.48338 | 5537.76058 |
| 开发者版 | 2646448.28 | 380.224178 | 2088.00025 | 6214.31217 | 6216.29052 |
| 候选版 | 1447013.12 | 695.428338 | 3128.00047 | 6212.55447 | 6214.5418 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 32483.7191 | 30969.3539 | 20648.0207 | 4951.65303 | 4952.86697 |
| 开发者版 | 169383.815 | 5945.40735 | 30776.004 | 6212.6947 | 6215.04717 |
| 候选版 | 121254.623 | 8328.83062 | 30776.0055 | 6211.73008 | 6213.80467 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.339429522 | 2.95688e+09 | 4.2949682e+09 | 5453.41923 | 5476.85531 |
| 开发者版 | 0.863315768 | 1.2994e+09 | 3.2212262e+09 | 6632.71334 | 6655.99852 |
| 候选版 | 0.850624806 | 1.31772e+09 | 3.22122625e+09 | 6632.86436 | 6655.94563 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 14656367.5 | 68.9917642 | 184.000046 | 6100.45211 | 6102.48711 |
| 开发者版 | 24124027.2 | 42.0960528 | 96.0000305 | 6030.05764 | 6032.40511 |
| 候选版 | 22471775.4 | 45.1755648 | 120.000031 | 6089.72378 | 6091.68903 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5178358.02 | 194.764896 | 296.00013 | 5808.89144 | 5810.90786 |
| 开发者版 | 15611302.9 | 64.7481484 | 208.000043 | 6156.92311 | 6158.84592 |
| 候选版 | 15489867.7 | 64.997772 | 288.000044 | 6212.87609 | 6215.16961 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 410707.838 | 2452.00778 | 2216.00164 | 5353.48089 | 5354.79742 |
| 开发者版 | 1874110.7 | 538.341803 | 2128.00036 | 6212.4633 | 6214.35258 |
| 候选版 | 1637041.53 | 614.84033 | 3168.00041 | 6213.87991 | 6216.02656 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 40540.7782 | 24817.6111 | 20648.0166 | 5261.32197 | 5262.64266 |
| 开发者版 | 137963.416 | 7293.1312 | 30816.0049 | 6213.09763 | 6215.20898 |
| 候选版 | 137861.695 | 7299.98025 | 30816.0049 | 6213.68458 | 6215.54095 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.332390116 | 3.53504e+09 | 4.2949682e+09 | 5452.7115 | 5476.33798 |
| 开发者版 | 0.850028685 | 1.31908e+09 | 3.22122624e+09 | 6632.85617 | 6655.97644 |
| 候选版 | 0.849320652 | 1.3206e+09 | 3.22122624e+09 | 6632.79037 | 6655.77714 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21927260.4 | 46.0135663 | 56.0000306 | 5643.7933 | 5645.99536 |
| 开发者版 | 47162168.9 | 21.4480317 | 56.0000155 | 6078.76359 | 6080.76216 |
| 候选版 | 25421039.5 | 39.8640641 | 104.000028 | 6090.01178 | 6091.89922 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13019680.1 | 77.5444114 | 168.000052 | 6009.8073 | 6011.86947 |
| 开发者版 | 25651072.1 | 39.2575406 | 168.000026 | 6212.42894 | 6214.59328 |
| 候选版 | 14389068.2 | 70.2928797 | 216.000047 | 6143.39034 | 6145.31511 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1592091.94 | 642.602769 | 2107.20043 | 6172.8622 | 6174.55267 |
| 开发者版 | 2527522.33 | 398.327938 | 2088.00027 | 6213.12005 | 6215.54744 |
| 候选版 | 1652004.2 | 610.960022 | 2136.00041 | 6192.28442 | 6194.72255 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 162342.833 | 6215.63231 | 20568.0042 | 6184.65358 | 6186.51703 |
| 开发者版 | 206828.94 | 4864.23345 | 20520.0033 | 6212.91308 | 6214.84192 |
| 候选版 | 64545.6975 | 15607.029 | 20568.0104 | 5750.58163 | 5753.06219 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.864068227 | 1.21086e+09 | 4.29496816e+09 | 5474.031 | 5477.77412 |
| 开发者版 | 1.56091821 | 685166667 | 2.14748403e+09 | 5555.39344 | 5557.66642 |
| 候选版 | 1.49936542 | 690600000 | 2.14748407e+09 | 5582.31123 | 5584.73311 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18571243.8 | 54.3708673 | 104.000036 | 5949.29491 | 5951.25381 |
| 开发者版 | 35200479.2 | 28.7312779 | 96.0000192 | 6168.86291 | 6170.40467 |
| 候选版 | 27424594.9 | 36.9177147 | 96.0000257 | 6083.44502 | 6085.36055 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 12850419.4 | 78.6302103 | 216.000052 | 6109.71445 | 6111.60128 |
| 开发者版 | 19946090.1 | 50.5845845 | 208.000034 | 6213.0818 | 6215.2227 |
| 候选版 | 16361350.2 | 61.8600379 | 208.000041 | 6173.31395 | 6175.40697 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1761757.08 | 575.019215 | 2136.00038 | 6212.51847 | 6214.54647 |
| 开发者版 | 2029025.37 | 496.166956 | 2128.00033 | 6212.19423 | 6214.48475 |
| 候选版 | 1919651.13 | 525.114152 | 2128.00035 | 6212.31477 | 6214.56211 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 151565.197 | 6647.23923 | 20568.0044 | 6162.60281 | 6164.64216 |
| 开发者版 | 175715.335 | 5745.18645 | 20560.0038 | 6210.40744 | 6212.274 |
| 候选版 | 175608.108 | 5753.68095 | 20560.0038 | 6210.46322 | 6212.59156 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.876202378 | 1.18958e+09 | 4.29496811e+09 | 5481.90212 | 5484.5832 |
| 开发者版 | 1.49058841 | 709413333 | 2.14748406e+09 | 5581.91864 | 5584.62667 |
| 候选版 | 1.49150071 | 699560000 | 2.14748407e+09 | 5608.91944 | 5611.35386 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21916352.3 | 46.0442675 | 56.0000307 | 5641.63112 | 5643.91734 |
| 开发者版 | 47164011.5 | 21.458535 | 56.0000155 | 6079.24856 | 6081.25644 |
| 候选版 | 25148053.2 | 40.3141412 | 104.000029 | 6084.55164 | 6086.69534 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13084254.7 | 77.1503774 | 168.000052 | 6008.93811 | 6011.05145 |
| 开发者版 | 25596276.7 | 39.3533204 | 168.000026 | 6212.80575 | 6214.66906 |
| 候选版 | 14473690.2 | 69.9309687 | 216.000047 | 6145.46619 | 6147.40869 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1517816.56 | 670.185958 | 2097.60045 | 6159.15345 | 6160.89673 |
| 开发者版 | 2523065.2 | 399.046859 | 2088.00027 | 6213.9637 | 6215.92655 |
| 候选版 | 1652407.73 | 610.788634 | 2136.00041 | 6193.28342 | 6195.04987 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 162501.274 | 6206.77786 | 20568.0041 | 6184.18188 | 6185.99405 |
| 开发者版 | 206784.3 | 4867.2622 | 20520.0033 | 6213.13677 | 6215.43766 |
| 候选版 | 62989.6166 | 16056.1737 | 20568.0107 | 5731.51005 | 5733.88159 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.858249444 | 1.22322e+09 | 4.29496816e+09 | 5475.27737 | 5478.10723 |
| 开发者版 | 1.53588555 | 659680000 | 2.14748403e+09 | 5599.96653 | 5602.62855 |
| 候选版 | 1.49943681 | 699153333 | 2.14748407e+09 | 5582.34397 | 5584.83619 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18622454.4 | 54.2115647 | 104.000036 | 5950.02823 | 5952.17961 |
| 开发者版 | 33270842.8 | 30.8727762 | 96.0000221 | 6148.74836 | 6150.47436 |
| 候选版 | 27465378.9 | 36.9018889 | 96.0000254 | 6084.64348 | 6086.64019 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 12838572.1 | 78.6097942 | 216.000052 | 6109.01814 | 6111.05856 |
| 开发者版 | 19932025 | 50.6236061 | 208.000034 | 6212.37181 | 6214.55083 |
| 候选版 | 16327647.4 | 62.0181357 | 208.000041 | 6173.78091 | 6176.18039 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1653982.1 | 622.612109 | 2136.00041 | 6189.69642 | 6191.45691 |
| 开发者版 | 2025768.71 | 496.833354 | 2128.00033 | 6213.47797 | 6215.50219 |
| 候选版 | 1923516.23 | 523.884744 | 2128.00035 | 6212.72781 | 6214.63198 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 150227.805 | 6709.29563 | 20568.0045 | 6158.9283 | 6161.26964 |
| 开发者版 | 175759.458 | 5746.94279 | 20560.0038 | 6209.78967 | 6211.8527 |
| 候选版 | 175816.187 | 5743.96661 | 20560.0038 | 6210.80806 | 6212.90955 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.873731695 | 1.19576e+09 | 4.29496816e+09 | 5480.53809 | 5483.72898 |
| 开发者版 | 1.49064279 | 708160000 | 2.14748407e+09 | 5609.09464 | 5611.54769 |
| 候选版 | 1.49139825 | 686740000 | 2.14748407e+09 | 5573.82766 | 5576.50981 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5263326.51 | 191.560122 | 176.000128 | 5365.85752 | 5367.37339 |
| 开发者版 | 8739994.42 | 115.202039 | 56.0000772 | 4655.04436 | 4656.67531 |
| 候选版 | 7025327.01 | 143.644273 | 128.000096 | 5330.56917 | 5331.82164 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4008837.86 | 255.499762 | 344.00017 | 5722.84266 | 5725.12959 |
| 开发者版 | 7557605.02 | 133.442747 | 168.000089 | 5665.87528 | 5668.28036 |
| 候选版 | 5722487.46 | 177.032074 | 296.000117 | 5880.16463 | 5882.24353 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1307156.29 | 770.462069 | 3224.00051 | 6212.87847 | 6215.16322 |
| 开发者版 | 2188872.29 | 459.997283 | 2088.00031 | 6212.80228 | 6215.01777 |
| 候选版 | 1229185.67 | 823.135084 | 3176.00055 | 6212.00581 | 6214.54406 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 84062.9476 | 14227.871 | 30872.0095 | 6017.27342 | 6019.47486 |
| 开发者版 | 170034.191 | 5919.34894 | 30776.004 | 6213.47786 | 6215.77563 |
| 候选版 | 62763.0252 | 18596.3359 | 30824.0124 | 5911.61503 | 5913.75686 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.658342081 | 1.5478e+09 | 5.36871001e+09 | 6526.93958 | 6529.96033 |
| 开发者版 | 0.855451074 | 1.3178e+09 | 3.2212262e+09 | 5658.05431 | 5660.80078 |
| 候选版 | 0.846247321 | 1.32852e+09 | 3.22122625e+09 | 5657.96267 | 5660.74011 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5260153.77 | 191.726334 | 176.000128 | 5365.68995 | 5366.75527 |
| 开发者版 | 7928483.51 | 127.418977 | 96.0000852 | 5116.75117 | 5118.2535 |
| 候选版 | 7086009.33 | 142.344672 | 120.000095 | 5261.96116 | 5263.43873 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4645772.47 | 217.417754 | 344.000145 | 5835.4053 | 5837.60056 |
| 开发者版 | 6555517.03 | 154.310391 | 208.000103 | 5720.84837 | 5722.90195 |
| 候选版 | 5965164.53 | 169.359952 | 288.000113 | 5883.14769 | 5885.41317 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1221979.53 | 833.22271 | 3224.00056 | 6204.15486 | 6206.29573 |
| 开发者版 | 1610261.99 | 629.976816 | 2128.00042 | 6182.16327 | 6183.92567 |
| 候选版 | 1532107.72 | 657.396525 | 3168.00044 | 6213.0038 | 6215.51233 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 122837.024 | 8219.39263 | 30872.0055 | 6212.74563 | 6215.0015 |
| 开发者版 | 136730.573 | 7357.74044 | 30816.0049 | 6212.64848 | 6214.91031 |
| 候选版 | 136422.682 | 7381.45903 | 30816.0049 | 6212.10895 | 6214.76709 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.669534948 | 1.52844e+09 | 5.36871001e+09 | 6526.77122 | 6529.76527 |
| 开发者版 | 0.840101544 | 1.33896e+09 | 3.22122624e+09 | 5657.61756 | 5660.40258 |
| 候选版 | 0.841374193 | 1.33812e+09 | 3.22122624e+09 | 5658.00011 | 5660.39625 |

## 95b8db0

### mixedDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.mixedDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.25903221 | 810.631156 | 1472.00054 | 226.736984 | 229.630922 |
| 开发者版 | 1.41486697 | 719.250536 | 1368.00048 | 226.109344 | 228.934484 |
| 候选版 | 1.45905619 | 697.171505 | 1368.00047 | 225.632094 | 228.533563 |

### noDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.noDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 7.55203579 | 134.325298 | 504.000089 | 226.385437 | 228.799859 |
| 开发者版 | 6.96276187 | 145.821974 | 504.000097 | 227.305047 | 230.050156 |
| 候选版 | 6.86029259 | 148.010827 | 504.000098 | 227.382547 | 229.423391 |

### nonStandardDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.nonStandardDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.68244746 | 602.677597 | 1336.0004 | 225.486953 | 228.789172 |
| 开发者版 | 1.59395418 | 638.052557 | 1291.20043 | 231.897719 | 248.451891 |
| 候选版 | 1.51048787 | 670.365864 | 1348.80045 | 237.9465 | 254.822484 |

### onlyDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.onlyDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.47510532 | 686.102772 | 1432.00046 | 225.604484 | 228.782031 |
| 开发者版 | 1.71648491 | 594.634175 | 1208.0004 | 234.677375 | 238.353016 |
| 候选版 | 1.77227906 | 571.114944 | 1208.00038 | 230.816531 | 234.568781 |

## ab8c4f2

### lookupNameAndValueMatchFirst

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchFirst` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 15.4595373 | 15.5365136 | 1.04000445e-05 | 108.589 | 109.592203 |
| 开发者版 | 13.3765884 | 13.4502753 | 9.01267976e-06 | 108.192 | 109.174344 |
| 候选版 | 16.293524 | 16.3767965 | 1.09595128e-05 | 108.731141 | 109.608047 |

### lookupNameAndValueMatchLast

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchLast` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 60.5911509 | 60.8936458 | 4.07860797e-05 | 108.399125 | 109.218625 |
| 开发者版 | 65.9315817 | 66.2585144 | 4.43906607e-05 | 107.965234 | 108.970703 |
| 候选版 | 46.0304768 | 46.2790723 | 3.09663738e-05 | 107.802516 | 108.770766 |

### lookupNameOnlyMatchBeginTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchBeginTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 114.921384 | 115.526293 | 7.75737764e-05 | 107.5815 | 108.580281 |
| 开发者版 | 12.632349 | 12.6958949 | 8.49534223e-06 | 108.23275 | 109.107391 |
| 候选版 | 16.4381243 | 16.5238296 | 1.1082157e-05 | 107.515578 | 108.444672 |

### lookupNameOnlyMatchEndTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchEndTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 19.0085933 | 19.1128101 | 1.28074675e-05 | 108.466234 | 109.347156 |
| 开发者版 | 9.84077061 | 9.90027442 | 6.64175199e-06 | 108.441953 | 109.3265 |
| 候选版 | 15.8236546 | 15.91545 | 1.06684601e-05 | 107.259078 | 108.163469 |

### lookupNoNameMatch

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNoNameMatch` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4.11598201 | 4.13849146 | 2.76970228e-06 | 108.986297 | 109.727734 |
| 开发者版 | 4.11622874 | 4.13907141 | 2.76774347e-06 | 107.384891 | 108.42425 |
| 候选版 | 4.14899148 | 4.17029202 | 2.79103069e-06 | 108.416844 | 109.278281 |

## b72fea3

### parseHttpHeaderDateFormatterNew（DATE_STRING=Sun, 27 Jan 2016 19:18:46 GMT）

`io.netty.handler.codec.DateFormatter2Benchmark.parseHttpHeaderDateFormatterNew` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5125519.09 | 196.241967 | 24.0001317 | 222.328391 | 224.281219 |
| 开发者版 | 5984439.31 | 167.980732 | 24.000113 | 222.086016 | 224.249813 |
| 候选版 | 6242617.32 | 161.338402 | 24.0001088 | 221.192656 | 222.895781 |

### parseHttpHeaderDateFormatterNew（DATE_STRING=Sun, 27 Dec 2016 19:18:46 GMT）

`io.netty.handler.codec.DateFormatter2Benchmark.parseHttpHeaderDateFormatterNew` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4568509.34 | 220.125758 | 24.0001478 | 222.563594 | 223.939437 |
| 开发者版 | 5889819.8 | 170.799529 | 24.0001152 | 221.482016 | 223.76025 |
| 候选版 | 6239735.32 | 161.512492 | 24.0001091 | 221.358937 | 223.436125 |
