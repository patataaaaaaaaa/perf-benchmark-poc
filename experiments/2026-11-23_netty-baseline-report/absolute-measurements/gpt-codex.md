# GPT + Codex逐场景绝对测量值

[返回汇报正文](../README.md)

本组覆盖 12 题、93 个场景。下表各值为同批次五个有效 JMH 区组分数的算术平均，最多保留 9 位有效数字。吞吐量越高越好，平均耗时和各项资源消耗越低越好。1 MiB = 1,048,576 字节。

## 2791f0f

### scheduleLots（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleLots` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 312.494671 | 8866918.89 | 6664255.31 | 243.572141 | 246.043094 |
| 开发者版 | 593.6218 | 5297552.17 | 6664249.96 | 249.973656 | 251.276859 |
| 候选版 | 509.504736 | 5950967.07 | 6664251.89 | 247.382797 | 250.205156 |

## 2ed95c9

### lookupHttp

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupHttp` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 12.541548 | 12.6004592 | 8.47865963e-06 | 110.442328 | 111.537484 |
| 开发者版 | 9.09660295 | 9.13687377 | 6.15823864e-06 | 109.309219 | 110.356109 |
| 候选版 | 11.5836513 | 11.630688 | 7.83858234e-06 | 110.386359 | 111.309031 |

### lookupHttps

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupHttps` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18.3841135 | 18.4656309 | 1.24391839e-05 | 110.350187 | 111.298312 |
| 开发者版 | 9.11965822 | 9.16364675 | 6.1668407e-06 | 110.212844 | 111.189594 |
| 候选版 | 14.0527941 | 14.1134992 | 9.49867598e-06 | 109.356656 | 110.295531 |

### lookupNameAndValueMatchFirst

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchFirst` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 14.0279709 | 14.0934915 | 9.54119482e-06 | 111.406859 | 112.384609 |
| 开发者版 | 7.81150129 | 7.84736295 | 5.30524479e-06 | 108.769937 | 109.666969 |
| 候选版 | 11.4640331 | 11.5165936 | 7.80055387e-06 | 110.05675 | 110.87075 |

### lookupNameAndValueMatchLast

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchLast` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 66.7617383 | 67.0863825 | 4.5383825e-05 | 111.7855 | 112.7045 |
| 开发者版 | 7.81038665 | 7.85016343 | 5.30401535e-06 | 109.226891 | 110.354344 |
| 候选版 | 46.307155 | 46.4509509 | 3.13006442e-05 | 110.271078 | 111.207953 |

### lookupNameOnlyMatchBeginTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchBeginTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 14.949728 | 15.0209504 | 1.01793016e-05 | 111.084203 | 112.087547 |
| 开发者版 | 4.2069442 | 4.22689219 | 2.86146268e-06 | 109.5625 | 110.612938 |
| 候选版 | 10.3099611 | 10.3612231 | 7.00965628e-06 | 109.937359 | 110.825656 |

### lookupNameOnlyMatchEndTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchEndTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 10.4951235 | 10.5444964 | 7.12379701e-06 | 111.545375 | 112.598125 |
| 开发者版 | 4.20813795 | 4.2274013 | 2.856027e-06 | 109.629078 | 110.584234 |
| 候选版 | 10.1117634 | 10.152557 | 6.87019197e-06 | 109.7115 | 110.625672 |

### lookupNoNameMatch

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNoNameMatch` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4.17917065 | 4.19734657 | 2.82814127e-06 | 111.001875 | 111.965141 |
| 开发者版 | 4.20853837 | 4.22963736 | 2.85164425e-06 | 109.782797 | 110.731828 |
| 候选版 | 5.40005377 | 5.42271367 | 3.65802858e-06 | 110.879672 | 111.858609 |

## 5a9b28a

### plainNew

`io.netty.microbench.util.RecyclerBenchmark.plainNew` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 9.87691476 | 10.0392977 | 80.0000067 | 224.566937 | 226.824531 |
| 开发者版 | 9.91614937 | 10.0756713 | 80.0000067 | 224.555125 | 227.073875 |
| 候选版 | 9.88362554 | 10.0417824 | 80.0000067 | 224.850703 | 226.909891 |

### producerConsumer

`io.netty.microbench.util.RecyclerBenchmark.producerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 48.8878724 | 48.7361929 | 0.0052256881 | 123.476203 | 124.4045 |
| 开发者版 | 52.5716291 | 52.4575506 | 0.00440875632 | 125.143484 | 125.854312 |
| 候选版 | 83.5447977 | 83.2185186 | 0.00418277453 | 122.391891 | 123.18375 |

### recyclerGetAndOrphan

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndOrphan` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 15.3344352 | 15.5504183 | 83.0000104 | 226.622 | 228.777203 |
| 开发者版 | 15.9087037 | 16.1222582 | 83.0000108 | 226.535625 | 228.546703 |
| 候选版 | 14.754579 | 14.9625304 | 83.00001 | 225.932187 | 227.934359 |

### recyclerGetAndRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 27.8716811 | 28.094828 | 1.89115608e-05 | 116.848938 | 117.948906 |
| 开发者版 | 27.8965321 | 28.1296297 | 1.89030911e-05 | 116.566031 | 117.656844 |
| 候选版 | 26.5153951 | 26.7331592 | 1.7986808e-05 | 117.121781 | 118.049844 |

### recyclerGetAndUnguardedRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndUnguardedRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 26.3896596 | 26.6062275 | 1.79311052e-05 | 115.885094 | 116.859828 |
| 开发者版 | 28.3537045 | 28.5904105 | 1.92583992e-05 | 118.314281 | 119.040609 |
| 候选版 | 27.1642713 | 27.3931186 | 1.84785212e-05 | 117.306031 | 118.309891 |

### unguardedProducerConsumer

`io.netty.microbench.util.RecyclerBenchmark.unguardedProducerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 49.6735875 | 49.5631073 | 0.00275815849 | 122.912469 | 123.680469 |
| 开发者版 | 52.1840763 | 52.0752881 | 0.00336654325 | 123.895594 | 124.525859 |
| 候选版 | 101.21432 | 101.010092 | 0.00576628227 | 121.380734 | 122.051937 |

## 67d3a78

### arraysBytesEqual（size=10）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6.03890729 | 6.09192026 | 4.25143602e-06 | 98.1506562 | 99.0866719 |
| 开发者版 | 6.18316992 | 6.23794805 | 4.34974412e-06 | 99.1213594 | 99.9138437 |
| 候选版 | 6.04980397 | 6.10193174 | 4.26209126e-06 | 98.5723281 | 99.333 |

### arraysBytesEqual（size=50）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 17.8546013 | 18.0160184 | 1.25650879e-05 | 99.178 | 99.8793594 |
| 开发者版 | 17.8550726 | 18.0160809 | 1.2588062e-05 | 97.9918125 | 98.8023906 |
| 候选版 | 17.8603097 | 18.0211939 | 1.25882463e-05 | 99.4993125 | 100.202625 |

### arraysBytesEqual（size=100）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 32.5241623 | 32.8128195 | 2.29206766e-05 | 98.1344219 | 98.9263906 |
| 开发者版 | 32.5166958 | 32.7956839 | 2.29293351e-05 | 98.1997813 | 99.1098281 |
| 候选版 | 32.5197331 | 32.7934884 | 2.29068553e-05 | 98.5654844 | 99.4115781 |

### arraysBytesEqual（size=1000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 296.936095 | 299.595661 | 0.000209362469 | 98.5310469 | 99.3090313 |
| 开发者版 | 296.869049 | 299.491696 | 0.000209400713 | 98.1740469 | 99.0674375 |
| 候选版 | 296.884926 | 299.523875 | 0.000209248966 | 97.9121562 | 98.8802187 |

### arraysBytesEqual（size=10000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 2880.58869 | 2907.41999 | 0.00202994732 | 98.26025 | 99.1083594 |
| 开发者版 | 2880.3552 | 2907.09935 | 0.00203053686 | 98.3679531 | 99.249 |
| 候选版 | 2880.99324 | 2907.41129 | 0.00202937248 | 98.5057812 | 99.3250312 |

### arraysBytesEqual（size=100000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 28756.9041 | 29014.2336 | 0.0202698996 | 98.6956719 | 99.5094219 |
| 开发者版 | 28767.0334 | 29017.3917 | 0.0202530747 | 98.84275 | 99.7859062 |
| 候选版 | 28829.1415 | 29073.5007 | 0.0203033872 | 97.6746562 | 98.4673125 |

### unsafeBytesEqual（size=10）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6.68925247 | 6.74800652 | 4.71830103e-06 | 109.898703 | 110.870328 |
| 开发者版 | 4.54113285 | 4.57692808 | 3.19608965e-06 | 110.941672 | 111.618422 |
| 候选版 | 5.02719892 | 5.0700473 | 3.5435885e-06 | 110.26525 | 111.167359 |

### unsafeBytesEqual（size=50）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 7.13203525 | 7.19477701 | 5.02614826e-06 | 111.399531 | 112.344266 |
| 开发者版 | 6.16964502 | 6.22472594 | 4.34657837e-06 | 111.330781 | 112.327094 |
| 候选版 | 6.14530084 | 6.19712557 | 4.32770403e-06 | 112.035219 | 112.713469 |

### unsafeBytesEqual（size=100）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 10.2408385 | 10.3232257 | 7.21842737e-06 | 110.839281 | 111.828219 |
| 开发者版 | 9.94163197 | 10.0303357 | 7.00704826e-06 | 111.624281 | 112.364594 |
| 候选版 | 9.70381617 | 9.78686997 | 6.8449911e-06 | 110.848594 | 111.764062 |

### unsafeBytesEqual（size=1000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 68.6275313 | 69.1924386 | 4.83258063e-05 | 110.210984 | 111.17725 |
| 开发者版 | 67.1918877 | 67.7707334 | 4.73086932e-05 | 111.578719 | 112.515359 |
| 候选版 | 64.1330281 | 64.6737734 | 4.52345751e-05 | 110.829547 | 111.797484 |

### unsafeBytesEqual（size=10000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 594.711698 | 599.850505 | 0.000419082003 | 110.913766 | 111.826406 |
| 开发者版 | 593.967576 | 598.901395 | 0.0004188354 | 110.842516 | 111.853719 |
| 候选版 | 535.355875 | 539.807475 | 0.000377247547 | 111.365687 | 112.179406 |

### unsafeBytesEqual（size=100000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6583.40689 | 6640.41273 | 0.00464011602 | 111.544969 | 112.392281 |
| 开发者版 | 6581.8793 | 6636.7027 | 0.0046368396 | 111.294969 | 112.039984 |
| 候选版 | 6099.40894 | 6151.97543 | 0.00429865982 | 111.471703 | 112.381812 |

## 687308b

### longAscii

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longAscii` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.39899642 | 2536.14592 | 5976.00169 | 224.685125 | 227.768781 |
| 开发者版 | 1.79262874 | 568.582466 | 3192.00038 | 224.555047 | 228.400063 |
| 候选版 | 1.92683507 | 528.790272 | 3192.00035 | 227.304422 | 229.787937 |

### longAsciiFirst

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longAsciiFirst` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.0360121639 | 28284.2416 | 52680.0189 | 226.651359 | 229.007563 |
| 开发者版 | 0.0422322286 | 24402.2881 | 54016.0163 | 224.944 | 228.187531 |
| 候选版 | 0.0457749181 | 22500.4992 | 54016.015 | 226.093125 | 228.676609 |

### longUtf8

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longUtf8` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.0433910372 | 23807.3426 | 51480.0159 | 225.544734 | 228.218859 |
| 开发者版 | 0.0471278255 | 21876.9037 | 51480.0146 | 224.582469 | 227.777187 |
| 候选版 | 0.0472070493 | 21807.8398 | 51480.0145 | 226.406234 | 228.527781 |

### shortAscii

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortAscii` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 19.3483831 | 52.4621433 | 152.000035 | 225.793516 | 227.959422 |
| 开发者版 | 22.5279255 | 45.0149625 | 152.00003 | 225.352203 | 228.279219 |
| 候选版 | 23.0120322 | 44.2295297 | 147.200029 | 225.447203 | 227.933625 |

### shortAsciiFirst

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortAsciiFirst` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 2.81670923 | 361.388512 | 848.000241 | 228.671828 | 230.471109 |
| 开发者版 | 3.66225275 | 277.036503 | 848.000184 | 228.670266 | 230.833203 |
| 候选版 | 3.25850599 | 311.163487 | 848.000207 | 227.929766 | 230.030094 |

### shortUtf8

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortUtf8` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 2.97065801 | 341.194226 | 840.000227 | 226.878094 | 229.552594 |
| 开发者版 | 3.91972118 | 258.798136 | 840.000172 | 228.350609 | 230.573844 |
| 候选版 | 3.41497957 | 296.963703 | 840.000197 | 227.466578 | 229.311344 |

## 87ec2f8

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 17417501.5 | 59.0886826 | 120.000039 | 5974.73261 | 5976.72589 |
| 开发者版 | 33367021.8 | 30.2888961 | 56.0000202 | 5918.75689 | 5921.18502 |
| 候选版 | 25429999.2 | 39.8321908 | 80.0000265 | 5966.29508 | 5968.29923 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 8662685.69 | 116.726263 | 232.000078 | 5965.52348 | 5967.66647 |
| 开发者版 | 21488107 | 47.229575 | 168.000031 | 6186.7725 | 6188.27333 |
| 候选版 | 13344932.6 | 75.8251749 | 248.00005 | 6161.16883 | 6162.95677 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 629071.63 | 1790.23379 | 2177.6012 | 5643.7755 | 5645.30794 |
| 开发者版 | 2629660.41 | 382.90434 | 2088.00026 | 6213.41319 | 6215.84098 |
| 候选版 | 1543742 | 652.39032 | 3128.00044 | 6213.25231 | 6215.64069 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 39534.6167 | 26971.2267 | 20648.0181 | 5152.17775 | 5153.95925 |
| 开发者版 | 168068.939 | 5989.09438 | 30776.004 | 6213.4063 | 6215.42708 |
| 候选版 | 128753.875 | 7822.25298 | 30776.0052 | 6212.13666 | 6214.52294 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.338030886 | 2.96808e+09 | 4.2949682e+09 | 5452.92161 | 5476.40423 |
| 开发者版 | 0.852281911 | 1.31828e+09 | 3.2212262e+09 | 6633.00666 | 6656.01536 |
| 候选版 | 0.842554585 | 1.33164e+09 | 3.22122625e+09 | 6632.29802 | 6655.34113 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 14827636.6 | 68.1814529 | 184.000045 | 6100.51119 | 6102.56444 |
| 开发者版 | 22824071.6 | 44.3809622 | 96.0000294 | 6005.22886 | 6007.11005 |
| 候选版 | 22167143.7 | 45.7470686 | 120.000033 | 6083.6158 | 6085.67773 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5159649.25 | 195.648248 | 296.00013 | 5806.35091 | 5808.27948 |
| 开发者版 | 15734773.1 | 64.3860629 | 208.000043 | 6157.03731 | 6158.97983 |
| 候选版 | 14170785.7 | 71.4159889 | 288.000048 | 6211.96458 | 6214.20261 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 409440.525 | 2460.59673 | 2216.00165 | 5348.33906 | 5349.86502 |
| 开发者版 | 1853661.8 | 546.118069 | 2128.00036 | 6212.81734 | 6214.64061 |
| 候选版 | 1618515.93 | 621.99799 | 3168.00042 | 6213.03202 | 6215.78317 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 40487.7763 | 24858.3475 | 20648.0166 | 5257.81339 | 5259.16955 |
| 开发者版 | 137098.219 | 7343.04994 | 30816.0049 | 6212.30283 | 6214.75742 |
| 候选版 | 136853.72 | 7351.41357 | 30816.0049 | 6212.74817 | 6214.79927 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.331351405 | 3.54084e+09 | 4.2949682e+09 | 5446.84653 | 5470.94217 |
| 开发者版 | 0.841545949 | 1.33304e+09 | 3.22122624e+09 | 6632.822 | 6655.82134 |
| 候选版 | 0.840777318 | 1.33328e+09 | 3.22122624e+09 | 6632.57097 | 6655.51534 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21846533.1 | 46.211642 | 56.0000307 | 5636.004 | 5638.11947 |
| 开发者版 | 47078410 | 21.4731167 | 56.0000163 | 6075.63936 | 6077.63252 |
| 候选版 | 24200334.3 | 41.8943016 | 104.00003 | 6065.15805 | 6067.46625 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13026590.6 | 77.5786785 | 168.000052 | 6007.26641 | 6009.53106 |
| 开发者版 | 25568353 | 39.4136436 | 168.000026 | 6212.01797 | 6214.29295 |
| 候选版 | 14043741.7 | 72.1306564 | 216.000048 | 6133.12419 | 6134.90663 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1572781.39 | 649.771157 | 2107.20043 | 6169.68345 | 6171.18341 |
| 开发者版 | 2504374.77 | 402.243772 | 2088.00027 | 6213.50627 | 6215.33412 |
| 候选版 | 1939514.02 | 526.205792 | 2097.60035 | 6205.81858 | 6207.77861 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 161473.141 | 6253.46043 | 20568.0042 | 6181.85398 | 6183.37078 |
| 开发者版 | 205256.194 | 4905.30846 | 20520.0033 | 6212.61919 | 6214.72017 |
| 候选版 | 146673.197 | 8434.93939 | 20529.6056 | 6074.67383 | 6076.48764 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.859057447 | 1.21642e+09 | 4.29496816e+09 | 5468.74758 | 5471.75988 |
| 开发者版 | 1.52632072 | 663986667 | 2.14748403e+09 | 5635.42955 | 5638.04384 |
| 候选版 | 1.48819614 | 718600000 | 2.14748407e+09 | 5600.13609 | 5602.28203 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18553546.1 | 54.4462956 | 104.000036 | 5945.98664 | 5948.25766 |
| 开发者版 | 33227593.2 | 30.9189086 | 96.0000223 | 6143.18241 | 6145.10667 |
| 候选版 | 25197116 | 40.1717542 | 96.0000294 | 6038.65822 | 6040.69666 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 12784745 | 79.0347597 | 216.000053 | 6105.07688 | 6106.87414 |
| 开发者版 | 19913168.6 | 50.7655648 | 208.000034 | 6212.12233 | 6214.49258 |
| 候选版 | 15393219.9 | 66.0813176 | 208.000044 | 6150.9377 | 6152.97739 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1738237.19 | 581.459145 | 2136.00039 | 6207.10156 | 6208.75908 |
| 开发者版 | 2015858.64 | 499.567242 | 2128.00033 | 6212.81702 | 6214.97058 |
| 候选版 | 1885425.91 | 535.143723 | 2128.00036 | 6212.5513 | 6214.71869 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 149313.177 | 6764.9362 | 20568.0045 | 6155.16187 | 6157.11138 |
| 开发者版 | 174705.937 | 5779.40411 | 20560.0039 | 6205.26505 | 6207.11195 |
| 候选版 | 174269.01 | 5788.98467 | 20560.0039 | 6203.70744 | 6205.35845 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.871804026 | 1.19838e+09 | 4.29496815e+09 | 5475.29227 | 5478.59491 |
| 开发者版 | 1.47649309 | 690886667 | 2.14748407e+09 | 5647.41814 | 5649.90827 |
| 候选版 | 1.47242132 | 685980000 | 2.14748407e+09 | 5635.53992 | 5638.04394 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21826384.5 | 46.222195 | 56.0000308 | 5636.26911 | 5638.51753 |
| 开发者版 | 47076554.3 | 21.4981931 | 56.0000162 | 6076.25702 | 6078.06428 |
| 候选版 | 23055064 | 44.0728104 | 104.000031 | 6043.68473 | 6045.88459 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13003440.3 | 77.7184458 | 168.000052 | 6005.12723 | 6006.88069 |
| 开发者版 | 25593814.2 | 39.3804008 | 168.000026 | 6212.91091 | 6215.01111 |
| 候选版 | 12759444.3 | 82.9936239 | 216.000055 | 6085.09569 | 6087.10541 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1505770.19 | 675.444346 | 2097.60045 | 6154.12138 | 6155.80181 |
| 开发者版 | 2509592.18 | 401.19303 | 2088.00027 | 6212.80783 | 6215.24548 |
| 候选版 | 2035723.03 | 494.603818 | 2088.00033 | 6211.75228 | 6214.13506 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 161265.766 | 6266.57057 | 20568.0042 | 6181.75411 | 6183.50483 |
| 开发者版 | 205499.667 | 4899.58949 | 20520.0033 | 6213.07227 | 6215.23781 |
| 候选版 | 147358.854 | 8411.05641 | 20529.6056 | 6078.41555 | 6080.11783 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.85732738 | 1.22188e+09 | 4.29496816e+09 | 5493.13061 | 5496.20394 |
| 开发者版 | 1.52534304 | 677480000 | 2.14748402e+09 | 5591.39387 | 5593.94058 |
| 候选版 | 1.48513242 | 710853333 | 2.14748407e+09 | 5617.27598 | 5619.84797 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18385331.9 | 54.9509766 | 104.000037 | 5940.587 | 5942.59459 |
| 开发者版 | 33316704.9 | 30.8640735 | 96.000022 | 6142.78622 | 6144.79858 |
| 候选版 | 24842488.7 | 40.7228257 | 96.0000296 | 6039.65305 | 6041.41631 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 12776727.2 | 79.052835 | 216.000053 | 6104.1212 | 6106.04339 |
| 开发者版 | 19922913.2 | 50.7523617 | 208.000034 | 6212.56222 | 6214.66278 |
| 候选版 | 15431414 | 65.9110929 | 208.000044 | 6151.19492 | 6153.25473 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1656610.21 | 622.546153 | 2136.00042 | 6185.89483 | 6187.74941 |
| 开发者版 | 2008750.33 | 501.210718 | 2128.00033 | 6212.94739 | 6215.01383 |
| 候选版 | 1882219.01 | 536.47726 | 2128.00036 | 6212.18742 | 6214.68925 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 149354.028 | 6755.16195 | 20568.0045 | 6153.84163 | 6155.85725 |
| 开发者版 | 174764.856 | 5774.78085 | 20560.0039 | 6206.35341 | 6207.69852 |
| 候选版 | 174420.297 | 5787.21746 | 20560.0039 | 6204.81114 | 6206.59131 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.867024989 | 1.20874e+09 | 4.29496816e+09 | 5481.2912 | 5483.87142 |
| 开发者版 | 1.47845908 | 701740000 | 2.14748407e+09 | 5593.18667 | 5595.73592 |
| 候选版 | 1.47896467 | 714760000 | 2.14748407e+09 | 5578.95262 | 5581.51662 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5094217.56 | 199.147111 | 176.000133 | 5316.0727 | 5317.01336 |
| 开发者版 | 8764224.15 | 114.896056 | 56.0000771 | 4658.76006 | 4660.47233 |
| 候选版 | 7115470.06 | 142.04951 | 80.0000953 | 4709.46142 | 4711.00077 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 3993532.18 | 257.164918 | 344.000171 | 5715.10828 | 5717.50178 |
| 开发者版 | 7549095.21 | 133.694642 | 168.000089 | 5659.54364 | 5661.94738 |
| 候选版 | 5903954.94 | 171.006405 | 248.000114 | 5771.48175 | 5774.1388 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 696971.103 | 1634.02205 | 3224.00109 | 5960.60203 | 5962.9832 |
| 开发者版 | 2193594.48 | 458.963148 | 2088.00031 | 6213.6747 | 6215.20328 |
| 候选版 | 1452085.47 | 694.433067 | 3137.60046 | 6212.9003 | 6215.04278 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 87762.9578 | 13236.8213 | 30872.0092 | 6049.42383 | 6051.49014 |
| 开发者版 | 168910.94 | 5961.19563 | 30776.004 | 6213.19494 | 6215.46927 |
| 候选版 | 128510.114 | 7840.8645 | 30776.0052 | 6212.77553 | 6215.06103 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.65200795 | 1.56576e+09 | 5.36871001e+09 | 6525.8765 | 6529.33433 |
| 开发者版 | 0.847039052 | 1.32892e+09 | 3.2212262e+09 | 5660.28245 | 5662.94566 |
| 候选版 | 0.832185681 | 1.35244e+09 | 3.22122625e+09 | 5657.747 | 5660.21022 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5206517.56 | 193.837641 | 176.000129 | 5354.37861 | 5355.21338 |
| 开发者版 | 8141484.9 | 123.888011 | 96.0000829 | 5153.92506 | 5155.61336 |
| 候选版 | 7037641.91 | 143.751756 | 120.000096 | 5247.43484 | 5248.73414 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4042046.86 | 252.497031 | 344.000168 | 5730.48273 | 5732.51417 |
| 开发者版 | 6382718.1 | 158.727359 | 208.000106 | 5696.04697 | 5697.96623 |
| 候选版 | 5804681.48 | 175.017444 | 288.000116 | 5856.66338 | 5859.00941 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1217351.17 | 837.887354 | 3224.00056 | 6202.61258 | 6204.9512 |
| 开发者版 | 1600951.92 | 632.418215 | 2128.00042 | 6178.32236 | 6179.70091 |
| 候选版 | 1514359.97 | 665.182408 | 3168.00044 | 6212.66322 | 6214.93122 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 122435.669 | 8255.22876 | 30872.0055 | 6212.69638 | 6214.25414 |
| 开发者版 | 135973.907 | 7400.17079 | 30816.005 | 6212.37634 | 6214.91577 |
| 候选版 | 135547.874 | 7425.65957 | 30816.005 | 6212.61844 | 6214.94141 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.658670958 | 1.54292e+09 | 5.36871001e+09 | 6527.10959 | 6530.16469 |
| 开发者版 | 0.831651512 | 1.35184e+09 | 3.22122624e+09 | 5657.70181 | 5660.31684 |
| 候选版 | 0.832464449 | 1.34852e+09 | 3.22122624e+09 | 5657.52405 | 5659.8402 |

## 8a8337e

### plainNew

`io.netty.microbench.util.RecyclerBenchmark.plainNew` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 9.89978904 | 10.0682588 | 80.0000067 | 224.106516 | 226.986812 |
| 开发者版 | 9.91513982 | 10.0774207 | 80.0000067 | 224.278281 | 226.872687 |
| 候选版 | 9.92166469 | 10.0902218 | 80.0000067 | 224.003734 | 226.578734 |

### producerConsumer

`io.netty.microbench.util.RecyclerBenchmark.producerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 292.532413 | 288.333429 | 12.924666 | 222.790422 | 224.96925 |
| 开发者版 | 263.466574 | 258.406187 | 10.9502705 | 221.031094 | 223.172562 |
| 候选版 | 298.950407 | 294.762585 | 12.9343123 | 222.368437 | 224.530469 |

### recyclerGetAndOrphan

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndOrphan` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 14.5442281 | 14.7492438 | 83.0000099 | 225.794688 | 228.554781 |
| 开发者版 | 15.4205689 | 15.6369962 | 83.0000105 | 225.717859 | 228.285672 |
| 候选版 | 14.8402985 | 15.0529107 | 83.0000101 | 225.950922 | 228.652953 |

### recyclerGetAndRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21.5373468 | 21.7068122 | 1.45772598e-05 | 115.789313 | 116.812922 |
| 开发者版 | 27.6793084 | 27.90335 | 1.87718526e-05 | 116.478891 | 117.431359 |
| 候选版 | 26.842742 | 27.0636308 | 1.84312215e-05 | 115.986172 | 116.782406 |

## 95b8db0

### mixedDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.mixedDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.38659504 | 728.937305 | 1486.40049 | 225.424109 | 228.874641 |
| 开发者版 | 1.53078516 | 659.733269 | 1368.00044 | 226.360859 | 229.217078 |
| 候选版 | 1.46733126 | 687.863943 | 1376.00046 | 225.623953 | 228.618203 |

### noDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.noDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 7.5245076 | 134.648253 | 504.00009 | 226.047953 | 228.468766 |
| 开发者版 | 6.77024685 | 149.702667 | 504.0001 | 227.033187 | 229.906641 |
| 候选版 | 6.74119709 | 150.442783 | 504.0001 | 226.706328 | 229.560125 |

### nonStandardDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.nonStandardDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.76961753 | 572.633188 | 1336.00038 | 225.062078 | 228.200047 |
| 开发者版 | 1.52068841 | 664.350014 | 1368.00044 | 238.944516 | 254.423766 |
| 候选版 | 1.50346664 | 672.230637 | 1368.00045 | 233.609406 | 258.671094 |

### onlyDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.onlyDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.49887236 | 674.789802 | 1432.00045 | 226.422766 | 229.054375 |
| 开发者版 | 1.8738375 | 543.379514 | 1208.00036 | 235.541547 | 244.390625 |
| 候选版 | 1.83318286 | 562.957769 | 1208.00038 | 237.739734 | 241.914531 |

## 9abeaf1

### executeMulti

`io.netty.microbench.channel.epoll.EpollSocketChannelBenchmark.executeMulti` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 317934.688 | 6270.39088 | 56.0096661 | 434.013875 | 435.300625 |
| 开发者版 | 497100.053 | 4174.07176 | 56.0066951 | 315.072734 | 315.828625 |
| 候选版 | 521704.888 | 3934.13085 | 56.0067326 | 306.735328 | 307.436047 |

### executeSingle

`io.netty.microbench.channel.epoll.EpollSocketChannelBenchmark.executeSingle` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 187237.131 | 6065.45277 | 56.0118019 | 389.6105 | 391.770609 |
| 开发者版 | 202830.556 | 5288.9362 | 56.0105411 | 363.934609 | 366.094438 |
| 候选版 | 207523.542 | 5199.73913 | 56.0106888 | 353.998016 | 355.088156 |

### pingPong

`io.netty.microbench.channel.epoll.EpollSocketChannelBenchmark.pingPong` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 66425.1817 | 15210.7964 | 192.032421 | 247.446172 | 248.515703 |
| 开发者版 | 68946.8287 | 14668.699 | 192.031497 | 254.779375 | 255.619203 |
| 候选版 | 69101.4958 | 14613.1472 | 192.031599 | 255.613672 | 256.391109 |

## ab8c4f2

### lookupNameAndValueMatchFirst

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchFirst` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 16.3474131 | 16.427212 | 1.10201394e-05 | 107.875438 | 108.758297 |
| 开发者版 | 13.3472614 | 13.4139767 | 8.9922083e-06 | 107.889516 | 108.810828 |
| 候选版 | 15.4539644 | 15.5300653 | 1.0400929e-05 | 107.743594 | 108.73725 |

### lookupNameAndValueMatchLast

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchLast` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 60.7604846 | 61.0921624 | 4.09039513e-05 | 107.063937 | 107.970141 |
| 开发者版 | 66.1144039 | 66.4549908 | 4.44515066e-05 | 107.521812 | 108.639234 |
| 候选版 | 60.5555325 | 60.8905362 | 4.08300338e-05 | 107.629063 | 108.574172 |

### lookupNameOnlyMatchBeginTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchBeginTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 93.8657244 | 94.3657818 | 6.31719685e-05 | 108.283125 | 109.090797 |
| 开发者版 | 12.6704374 | 12.7402915 | 8.53439284e-06 | 108.119297 | 108.880219 |
| 候选版 | 18.6529985 | 18.7466771 | 1.25846411e-05 | 108.120688 | 108.886484 |

### lookupNameOnlyMatchEndTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchEndTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 22.3827927 | 22.5069743 | 1.50819892e-05 | 108.389344 | 109.323156 |
| 开发者版 | 9.84961377 | 9.90226855 | 6.64323401e-06 | 108.589422 | 109.540234 |
| 候选版 | 16.6150486 | 16.7135517 | 1.12096363e-05 | 107.719266 | 108.709031 |

### lookupNoNameMatch

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNoNameMatch` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4.11709492 | 4.14126309 | 2.77170361e-06 | 107.768047 | 108.710484 |
| 开发者版 | 4.11642694 | 4.13663228 | 2.76910195e-06 | 107.772594 | 108.671891 |
| 候选版 | 4.11696914 | 4.13818159 | 2.7659135e-06 | 108.265281 | 109.144859 |

## b72fea3

### parseHttpHeaderDateFormatterNew（DATE_STRING=Sun, 27 Jan 2016 19:18:46 GMT）

`io.netty.handler.codec.DateFormatter2Benchmark.parseHttpHeaderDateFormatterNew` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5032082.58 | 199.904888 | 24.0001343 | 223.250438 | 224.877266 |
| 开发者版 | 5969565.12 | 168.578252 | 24.0001138 | 222.045656 | 224.290984 |
| 候选版 | 4567179.35 | 220.134746 | 24.0001477 | 220.026438 | 221.776578 |

### parseHttpHeaderDateFormatterNew（DATE_STRING=Sun, 27 Dec 2016 19:18:46 GMT）

`io.netty.handler.codec.DateFormatter2Benchmark.parseHttpHeaderDateFormatterNew` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4570634.25 | 220.145223 | 24.0001477 | 222.492734 | 223.750172 |
| 开发者版 | 5882090.8 | 171.005922 | 24.0001149 | 221.85375 | 224.069297 |
| 候选版 | 4515431.68 | 222.792905 | 24.0001494 | 220.259078 | 222.175938 |

## feb804d

### scheduleCancelLotsOutsideLoop（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleCancelLotsOutsideLoop` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 201.025473 | 10673403.1 | 12003400.7 | 229.935484 | 232.449281 |
| 开发者版 | 208.957461 | 12332277 | 7203456.05 | 230.063562 | 232.999094 |
| 候选版 | 199.441743 | 10733499.2 | 9603449.61 | 229.218422 | 232.351844 |

### scheduleLots（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleLots` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 665.021934 | 4787534.31 | 6664139.09 | 254.79825 | 256.50125 |
| 开发者版 | 614.657315 | 5024237.2 | 6664139.26 | 251.607281 | 253.666266 |
| 候选版 | 669.508886 | 4780153.6 | 6664139.09 | 258.298016 | 259.649375 |

### scheduleLotsOutsideLoop（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleLotsOutsideLoop` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 329.552737 | 7843403.51 | 9591000.62 | 231.289344 | 233.989453 |
| 开发者版 | 349.577767 | 9367240.4 | 7191669.09 | 230.464063 | 233.603641 |
| 候选版 | 346.982599 | 7486681.29 | 7191219.8 | 230.6185 | 233.683125 |
