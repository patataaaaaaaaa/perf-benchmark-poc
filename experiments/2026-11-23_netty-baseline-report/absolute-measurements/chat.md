# 历史 GPT Chat逐场景绝对测量值

[返回汇报正文](../README.md)

本组覆盖 12 题、93 个场景。下表各值为同批次五个有效 JMH 区组分数的算术平均，最多保留 9 位有效数字。吞吐量越高越好，平均耗时和各项资源消耗越低越好。1 MiB = 1,048,576 字节。

## 2791f0f

### scheduleLots（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleLots` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 302.727489 | 9103443.43 | 6664255.37 | 245.788828 | 247.591109 |
| 开发者版 | 630.585891 | 5102670.97 | 6664249.44 | 253.721156 | 255.155141 |
| 候选版 | 685.994199 | 4721919.86 | 6664250.8 | 250.913656 | 252.663094 |

## 2ed95c9

### lookupHttp

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupHttp` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13.5500871 | 13.6132187 | 9.17145201e-06 | 113.548984 | 114.637453 |
| 开发者版 | 9.02419752 | 9.06563044 | 6.1069794e-06 | 113.050359 | 114.073844 |
| 候选版 | 14.3872519 | 14.4603781 | 9.73103653e-06 | 111.526875 | 112.590484 |

### lookupHttps

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupHttps` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21.8675836 | 21.9808721 | 1.48158332e-05 | 114.282672 | 115.274406 |
| 开发者版 | 9.39187095 | 9.43563988 | 6.35084943e-06 | 113.050719 | 113.997906 |
| 候选版 | 23.0071706 | 23.1213177 | 1.55573284e-05 | 111.840047 | 112.906281 |

### lookupNameAndValueMatchFirst

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchFirst` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13.2648888 | 13.3267788 | 9.0130149e-06 | 112.834266 | 113.874375 |
| 开发者版 | 8.60433866 | 8.65137052 | 5.85312837e-06 | 112.865766 | 113.987328 |
| 候选版 | 14.4006231 | 14.4666376 | 9.77794165e-06 | 112.057188 | 112.906625 |

### lookupNameAndValueMatchLast

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchLast` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 66.9616898 | 67.3291847 | 4.54695063e-05 | 113.558828 | 114.633766 |
| 开发者版 | 7.82244789 | 7.86576791 | 5.30875713e-06 | 112.577125 | 113.524516 |
| 候选版 | 63.62055 | 63.9566282 | 4.32034203e-05 | 112.761812 | 113.762828 |

### lookupNameOnlyMatchBeginTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchBeginTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13.1825559 | 13.2489714 | 8.94884609e-06 | 113.619672 | 114.665484 |
| 开发者版 | 4.20626882 | 4.23042487 | 2.85513365e-06 | 112.479922 | 113.492266 |
| 候选版 | 14.643317 | 14.7290372 | 9.95084521e-06 | 111.390625 | 112.297641 |

### lookupNameOnlyMatchEndTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchEndTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 10.8177678 | 10.876033 | 7.33361536e-06 | 113.224219 | 114.202156 |
| 开发者版 | 4.20922416 | 4.23447422 | 2.85635895e-06 | 112.517875 | 113.58725 |
| 候选版 | 11.7322376 | 11.7984962 | 7.96587306e-06 | 112.414953 | 113.606562 |

### lookupNoNameMatch

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNoNameMatch` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4.11245987 | 4.13529264 | 2.79148275e-06 | 111.968016 | 112.989656 |
| 开发者版 | 4.211443 | 4.23349533 | 2.85271461e-06 | 111.912844 | 112.927453 |
| 候选版 | 4.42577191 | 4.4468895 | 2.99839724e-06 | 111.869719 | 112.877094 |

## 5a9b28a

### plainNew

`io.netty.microbench.util.RecyclerBenchmark.plainNew` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 9.85067337 | 10.015621 | 80.0000066 | 223.900094 | 225.589922 |
| 开发者版 | 9.84716612 | 10.0139432 | 80.0000066 | 224.835437 | 226.691094 |
| 候选版 | 9.85465892 | 10.0159249 | 80.0000066 | 224.993891 | 227.305516 |

### producerConsumer

`io.netty.microbench.util.RecyclerBenchmark.producerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 53.4997903 | 53.4286343 | 0.0263996763 | 130.11275 | 131.244328 |
| 开发者版 | 52.6450139 | 52.5431788 | 0.00310761511 | 122.685531 | 123.333922 |
| 候选版 | 97.2221337 | 96.987983 | 0.00307302402 | 120.756406 | 121.690922 |

### recyclerGetAndOrphan

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndOrphan` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 15.3760963 | 15.5863869 | 83.0000104 | 225.80525 | 228.013813 |
| 开发者版 | 15.8703663 | 16.0866769 | 83.0000108 | 226.855781 | 228.762906 |
| 候选版 | 14.5455332 | 14.752453 | 83.0000099 | 226.151297 | 228.490031 |

### recyclerGetAndRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 27.3068965 | 27.5217077 | 1.85095593e-05 | 115.835781 | 116.796469 |
| 开发者版 | 27.8669739 | 28.1028763 | 1.88792416e-05 | 115.691187 | 116.650187 |
| 候选版 | 26.882924 | 27.1123712 | 1.82357243e-05 | 116.544422 | 117.500312 |

### recyclerGetAndUnguardedRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndUnguardedRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 26.857765 | 27.083727 | 1.82515908e-05 | 115.921422 | 116.801187 |
| 开发者版 | 28.1057727 | 28.3288261 | 1.90936303e-05 | 115.380312 | 116.376109 |
| 候选版 | 26.0554275 | 26.2820396 | 1.76985103e-05 | 116.8085 | 117.517688 |

### unguardedProducerConsumer

`io.netty.microbench.util.RecyclerBenchmark.unguardedProducerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 48.7328035 | 48.6459758 | 0.00164072616 | 120.895375 | 121.756531 |
| 开发者版 | 58.1905114 | 57.8910157 | 0.00823458539 | 127.669094 | 128.680172 |
| 候选版 | 78.9130307 | 78.8179822 | 0.00263738311 | 122.145828 | 123.090156 |

## 67d3a78

### arraysBytesEqual（size=10）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6.0349722 | 6.08678854 | 4.24881942e-06 | 100.502 | 101.433141 |
| 开发者版 | 6.03313447 | 6.08547645 | 4.25109017e-06 | 99.7703281 | 100.801 |
| 候选版 | 6.03490809 | 6.08480278 | 4.24568419e-06 | 99.8325156 | 100.803188 |

### arraysBytesEqual（size=50）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 17.8443545 | 17.9865506 | 1.25732255e-05 | 100.750406 | 101.732594 |
| 开发者版 | 17.8451351 | 17.9909934 | 1.25730161e-05 | 100.246656 | 101.260359 |
| 候选版 | 17.8410011 | 17.9831872 | 1.25610995e-05 | 100.592375 | 101.543453 |

### arraysBytesEqual（size=100）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 32.5573668 | 32.8193982 | 2.29320634e-05 | 99.7680625 | 100.844125 |
| 开发者版 | 32.5008552 | 32.7699814 | 2.29094502e-05 | 100.137297 | 101.120375 |
| 候选版 | 32.4880229 | 32.7685642 | 2.29009967e-05 | 100.023859 | 101.059922 |

### arraysBytesEqual（size=1000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 296.674108 | 299.275583 | 0.000209148505 | 99.9579219 | 100.943484 |
| 开发者版 | 296.68393 | 299.155077 | 0.000209221338 | 99.8548438 | 100.856313 |
| 候选版 | 296.600157 | 299.181846 | 0.000209086563 | 100.258938 | 101.303453 |

### arraysBytesEqual（size=10000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 2878.11495 | 2903.39469 | 0.00202907472 | 100.207094 | 101.296219 |
| 开发者版 | 2877.49705 | 2902.18166 | 0.00202768399 | 99.6115 | 100.704906 |
| 候选版 | 2877.03858 | 2902.32079 | 0.00202769223 | 99.98975 | 100.964062 |

### arraysBytesEqual（size=100000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 28768.6474 | 29022.088 | 0.0202800863 | 100.879172 | 101.763875 |
| 开发者版 | 28765.6259 | 29006.3985 | 0.0202712004 | 100.535047 | 101.634609 |
| 候选版 | 28719.9846 | 28969.6214 | 0.0202297432 | 100.066734 | 101.142828 |

### unsafeBytesEqual（size=10）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6.68533197 | 6.74181092 | 4.71399946e-06 | 112.688016 | 113.629859 |
| 开发者版 | 4.56390856 | 4.60145916 | 3.21572857e-06 | 112.590281 | 113.467875 |
| 候选版 | 4.86040745 | 4.90040069 | 3.42657092e-06 | 113.363594 | 114.223531 |

### unsafeBytesEqual（size=50）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 7.80476609 | 7.87074366 | 5.50431888e-06 | 112.181453 | 113.151438 |
| 开发者版 | 6.16179723 | 6.20973003 | 4.34570042e-06 | 112.284969 | 113.261344 |
| 候选版 | 6.09306791 | 6.14222064 | 4.29617802e-06 | 112.996234 | 113.935344 |

### unsafeBytesEqual（size=100）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 10.3215917 | 10.4041012 | 7.2824373e-06 | 112.366734 | 113.271453 |
| 开发者版 | 9.69730921 | 9.78072378 | 6.83843464e-06 | 112.359234 | 113.367156 |
| 候选版 | 9.9348605 | 10.017555 | 7.0074373e-06 | 112.619844 | 113.419859 |

### unsafeBytesEqual（size=1000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 68.5956747 | 69.1819388 | 4.83779973e-05 | 112.940719 | 113.770906 |
| 开发者版 | 67.1477867 | 67.7108394 | 4.73105784e-05 | 112.135172 | 113.124344 |
| 候选版 | 66.8061095 | 67.3234706 | 4.71137414e-05 | 112.850031 | 113.723328 |

### unsafeBytesEqual（size=10000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 594.609627 | 599.549129 | 0.000419262734 | 112.343469 | 113.245922 |
| 开发者版 | 593.169031 | 598.110378 | 0.000418267746 | 111.833891 | 112.680469 |
| 候选版 | 593.014778 | 597.869266 | 0.000418175776 | 112.007016 | 112.95525 |

### unsafeBytesEqual（size=100000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6578.28656 | 6634.60576 | 0.00463927545 | 112.916375 | 113.902203 |
| 开发者版 | 6575.4962 | 6631.92372 | 0.0046356437 | 111.616828 | 112.587406 |
| 候选版 | 6575.05038 | 6628.45916 | 0.00463604511 | 113.522875 | 114.344406 |

## 687308b

### longAscii

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longAscii` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.41464831 | 2452.97184 | 5976.00163 | 224.562437 | 227.591437 |
| 开发者版 | 1.77490035 | 574.364646 | 3192.00038 | 227.022672 | 229.478922 |
| 候选版 | 1.93136794 | 528.11318 | 3192.00035 | 227.077031 | 230.139141 |

### longAsciiFirst

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longAsciiFirst` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.0395379515 | 26137.2354 | 52680.0174 | 225.776672 | 228.521484 |
| 开发者版 | 0.0439037992 | 23308.8875 | 54016.0155 | 227.230578 | 229.704328 |
| 候选版 | 0.0441466501 | 23186.4141 | 54016.0155 | 226.266328 | 228.987625 |

### longUtf8

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longUtf8` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.0448208086 | 23489.9741 | 51480.0156 | 227.591141 | 229.493219 |
| 开发者版 | 0.0499766426 | 20473.465 | 51480.0136 | 226.257687 | 228.927844 |
| 候选版 | 0.0451251969 | 22682.1346 | 51480.0151 | 226.120734 | 228.702203 |

### shortAscii

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortAscii` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 19.1487881 | 52.9855788 | 152.000035 | 225.070859 | 228.155188 |
| 开发者版 | 22.4937635 | 45.1293934 | 152.00003 | 225.624922 | 227.968891 |
| 候选版 | 22.3591048 | 45.3671524 | 152.00003 | 225.388828 | 228.157719 |

### shortAsciiFirst

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortAsciiFirst` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 2.84439101 | 358.151171 | 848.000239 | 228.359359 | 230.188375 |
| 开发者版 | 3.65581496 | 277.39573 | 848.000185 | 229.451781 | 230.659078 |
| 候选版 | 3.25807087 | 311.237511 | 848.000207 | 225.826125 | 229.05125 |

### shortUtf8

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortUtf8` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 3.1024802 | 328.228113 | 840.000219 | 226.210187 | 229.097797 |
| 开发者版 | 3.91691069 | 258.925607 | 840.000172 | 229.071156 | 230.969312 |
| 候选版 | 3.43286559 | 295.406857 | 840.000196 | 226.414406 | 229.708 |

## 87ec2f8

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18038775.4 | 56.0778785 | 120.000037 | 6015.94039 | 6018.50922 |
| 开发者版 | 33532311.9 | 30.1205348 | 56.00002 | 5922.668 | 5924.98606 |
| 候选版 | 17351427.5 | 58.2263166 | 128.000039 | 6010.78613 | 6012.71328 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 8700534.68 | 116.029805 | 232.000077 | 5973.79788 | 5976.09753 |
| 开发者版 | 21597999.7 | 46.8567228 | 168.000031 | 6190.74109 | 6192.27509 |
| 候选版 | 11041990.1 | 91.748149 | 296.000061 | 6161.85188 | 6163.44775 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 396568.565 | 2539.35755 | 2216.0017 | 5314.31589 | 5314.82275 |
| 开发者版 | 2653836.3 | 379.443398 | 2088.00025 | 6213.44425 | 6215.78669 |
| 候选版 | 1535576.57 | 656.703069 | 3137.60044 | 6212.39639 | 6214.99066 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 32490.5567 | 30973.7434 | 20648.0208 | 4952.44784 | 4953.97483 |
| 开发者版 | 169231.554 | 5948.10677 | 30776.004 | 6213.59898 | 6215.66628 |
| 候选版 | 100938.21 | 11680.4839 | 30795.2078 | 6105.38016 | 6107.43108 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.34010867 | 2.95028e+09 | 4.2949682e+09 | 5452.50294 | 5476.33195 |
| 开发者版 | 0.859924778 | 1.30924e+09 | 3.2212262e+09 | 6633.3298 | 6656.24228 |
| 候选版 | 0.852220559 | 1.31604e+09 | 3.22122625e+09 | 6632.3363 | 6655.32694 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 14461503.6 | 70.0300086 | 184.000047 | 6093.30166 | 6095.21856 |
| 开发者版 | 23692260.1 | 42.8104742 | 96.0000297 | 6024.33194 | 6026.43508 |
| 候选版 | 24026659 | 42.212205 | 120.000028 | 6127.60339 | 6129.81952 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5189652.86 | 194.355645 | 296.000129 | 5809.19973 | 5811.46484 |
| 开发者版 | 15794357.5 | 64.0068873 | 208.000043 | 6161.8712 | 6163.68767 |
| 候选版 | 15683528.6 | 64.1855799 | 288.000043 | 6213.58106 | 6215.26819 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 409367.972 | 2459.35331 | 2216.00165 | 5352.43203 | 5353.90714 |
| 开发者版 | 1879319.75 | 536.899193 | 2128.00036 | 6212.72084 | 6214.81311 |
| 候选版 | 1622650.85 | 620.703205 | 3168.00041 | 6213.43169 | 6215.83994 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 40579.4375 | 24808.0837 | 20648.0166 | 5263.67612 | 5265.09014 |
| 开发者版 | 137969.677 | 7295.80833 | 30816.0049 | 6213.00681 | 6215.42063 |
| 候选版 | 137591.34 | 7317.13541 | 30816.0049 | 6213.27566 | 6215.32492 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.332985198 | 3.46724e+09 | 4.2949682e+09 | 5452.94119 | 5476.56731 |
| 开发者版 | 0.847985978 | 1.32644e+09 | 3.22122624e+09 | 6633.06697 | 6655.86331 |
| 候选版 | 0.850564796 | 1.31936e+09 | 3.22122624e+09 | 6632.27863 | 6655.48888 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21796378.5 | 46.2939305 | 56.0000309 | 5638.27931 | 5640.8873 |
| 开发者版 | 47275731.2 | 21.3892901 | 56.0000154 | 6079.41356 | 6081.71655 |
| 候选版 | 24935350.1 | 40.5458073 | 104.000029 | 6078.82059 | 6081.00623 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13008815.7 | 77.6055226 | 168.000052 | 6008.41264 | 6010.36198 |
| 开发者版 | 25720978.8 | 39.1543136 | 168.000026 | 6212.77098 | 6214.88133 |
| 候选版 | 13785932.3 | 73.3344138 | 216.000049 | 6132.36344 | 6134.42661 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1519326.74 | 669.85496 | 2097.60045 | 6157.74964 | 6159.47241 |
| 开发者版 | 2534029.95 | 397.340064 | 2088.00027 | 6213.37162 | 6215.52753 |
| 候选版 | 1232272.88 | 965.708072 | 2136.00064 | 6035.46578 | 6037.92472 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 156146.447 | 6511.44143 | 20558.4043 | 6168.76652 | 6170.79866 |
| 开发者版 | 206625.109 | 4872.13945 | 20520.0033 | 6212.74794 | 6214.77458 |
| 候选版 | 60827.6025 | 16672.169 | 20568.0111 | 5699.42188 | 5701.86767 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.86346608 | 1.21524e+09 | 4.29496816e+09 | 5480.7853 | 5484.10898 |
| 开发者版 | 1.55160526 | 666933333 | 2.14748402e+09 | 5581.70159 | 5584.33838 |
| 候选版 | 1.50141091 | 692033333 | 2.14748407e+09 | 5591.43969 | 5594.13744 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18657947.7 | 54.1422155 | 104.000036 | 5949.70641 | 5951.90586 |
| 开发者版 | 33523344.5 | 30.5909514 | 96.0000216 | 6148.74806 | 6150.80613 |
| 候选版 | 27042235.2 | 37.3737352 | 96.0000271 | 6078.01255 | 6080.19573 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 12680819.1 | 79.7589932 | 216.000054 | 6103.23147 | 6104.93417 |
| 开发者版 | 19189547.4 | 53.0077314 | 208.000035 | 6203.47756 | 6205.667 |
| 候选版 | 16083411.9 | 62.9587496 | 208.000042 | 6170.92958 | 6172.88883 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1742903.74 | 581.230075 | 2136.00039 | 6208.90086 | 6211.00236 |
| 开发者版 | 2014397.47 | 499.964694 | 2128.00033 | 6213.16847 | 6215.55619 |
| 候选版 | 1918357.01 | 525.348494 | 2128.00035 | 6212.23333 | 6214.31217 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 150597.108 | 6693.87716 | 20568.0045 | 6160.31098 | 6161.83173 |
| 开发者版 | 175854.62 | 5740.8889 | 20560.0038 | 6209.74366 | 6211.30358 |
| 候选版 | 175566.174 | 5751.8111 | 20560.0038 | 6209.23391 | 6211.02252 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.872521131 | 1.19464e+09 | 4.29496815e+09 | 5469.72852 | 5472.07348 |
| 开发者版 | 1.49194868 | 700513333 | 2.14748406e+09 | 5599.82786 | 5602.38092 |
| 候选版 | 1.49196577 | 695760000 | 2.14748406e+09 | 5590.06727 | 5592.77831 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21885567.4 | 46.1205852 | 56.0000306 | 5637.62644 | 5640.04088 |
| 开发者版 | 47267957 | 21.4013528 | 56.0000154 | 6079.14009 | 6081.28091 |
| 候选版 | 24944135.5 | 40.5099047 | 104.000029 | 6079.3702 | 6081.39678 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13076117.2 | 77.2438957 | 168.000052 | 6009.6527 | 6011.64617 |
| 开发者版 | 25715124.1 | 39.1611698 | 168.000026 | 6212.65355 | 6214.86919 |
| 候选版 | 13917526.6 | 72.7409856 | 216.000048 | 6132.86516 | 6134.97267 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1518932.99 | 669.897877 | 2097.60045 | 6158.07967 | 6159.8753 |
| 开发者版 | 2534793.09 | 397.104048 | 2088.00027 | 6213.53666 | 6215.55436 |
| 候选版 | 1594071.9 | 635.653592 | 2136.00042 | 6184.24838 | 6185.7835 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 162273.654 | 6223.30487 | 20568.0041 | 6182.77197 | 6184.66202 |
| 开发者版 | 206650.901 | 4871.26108 | 20520.0033 | 6212.97817 | 6215.10055 |
| 候选版 | 98413.0477 | 12502.6175 | 20568.0083 | 5897.03614 | 5899.12083 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.865012601 | 1.20924e+09 | 4.29496816e+09 | 5474.28455 | 5477.75775 |
| 开发者版 | 1.54199934 | 669520000 | 2.14748402e+09 | 5538.00303 | 5540.43531 |
| 候选版 | 1.49842267 | 713600000 | 2.14748407e+09 | 5607.94048 | 5610.34308 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18888681.5 | 53.5095421 | 104.000036 | 5956.51091 | 5958.66623 |
| 开发者版 | 35319701.4 | 28.6363031 | 96.000019 | 6170.27895 | 6171.99284 |
| 候选版 | 27027399.1 | 37.4090186 | 96.0000272 | 6078.02961 | 6080.28216 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 12734243.7 | 79.367907 | 216.000054 | 6103.13938 | 6105.25037 |
| 开发者版 | 19145334.2 | 53.1408273 | 208.000035 | 6203.00836 | 6205.44294 |
| 候选版 | 16260668.1 | 62.2533395 | 208.000041 | 6169.94791 | 6171.75295 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1757473.62 | 575.775699 | 2136.00038 | 6212.15347 | 6214.35928 |
| 开发者版 | 2032505.83 | 495.33272 | 2128.00033 | 6212.20925 | 6214.84012 |
| 候选版 | 1906606.92 | 528.811126 | 2128.00035 | 6212.52711 | 6214.56764 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 155558.142 | 6497.15099 | 20568.0043 | 6169.09052 | 6170.909 |
| 开发者版 | 175794.156 | 5742.17276 | 20560.0038 | 6208.82972 | 6210.95133 |
| 候选版 | 175540.769 | 5751.8934 | 20560.0038 | 6208.99502 | 6210.87559 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.874862636 | 1.19572e+09 | 4.29496816e+09 | 5480.98477 | 5483.99609 |
| 开发者版 | 1.49543772 | 720126667 | 2.14748407e+09 | 5561.59448 | 5564.16991 |
| 候选版 | 1.49447233 | 724133333 | 2.14748406e+09 | 5590.35703 | 5592.98662 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5233544.83 | 192.688375 | 176.000129 | 5358.17616 | 5359.34295 |
| 开发者版 | 8296277.13 | 122.035685 | 56.000082 | 4649.15056 | 4650.73831 |
| 候选版 | 7381179.42 | 136.615894 | 89.600091 | 4858.23313 | 4859.99678 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 3920555.34 | 260.144822 | 344.000175 | 5705.78128 | 5707.95828 |
| 开发者版 | 7563697.77 | 133.445443 | 168.000089 | 5663.3807 | 5665.80719 |
| 候选版 | 5758793.37 | 175.246344 | 248.000117 | 5756.50423 | 5758.56638 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1154358.87 | 985.039359 | 3224.00066 | 6150.82422 | 6152.99188 |
| 开发者版 | 2209862.49 | 455.512832 | 2088.0003 | 6212.98109 | 6215.29759 |
| 候选版 | 1492559.08 | 674.449843 | 3128.00045 | 6212.95272 | 6215.45373 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 83831.1616 | 14246.2411 | 30872.0095 | 6016.93058 | 6019.04761 |
| 开发者版 | 169776.814 | 5930.53362 | 30776.004 | 6214.08394 | 6215.97266 |
| 候选版 | 129819.211 | 7760.61158 | 30776.0052 | 6212.4715 | 6214.63583 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.658811215 | 1.54636e+09 | 5.36871001e+09 | 6525.8323 | 6529.50931 |
| 开发者版 | 0.855418332 | 1.318e+09 | 3.2212262e+09 | 5658.05153 | 5660.72975 |
| 候选版 | 0.842444549 | 1.33424e+09 | 3.22122625e+09 | 5657.67645 | 5660.14741 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5082732.36 | 201.061332 | 176.000134 | 5310.01753 | 5311.34842 |
| 开发者版 | 8159140.46 | 123.600637 | 96.0000826 | 5159.47061 | 5161.23794 |
| 候选版 | 7327695.72 | 137.664932 | 120.000092 | 5300.65667 | 5301.91142 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4653286.01 | 216.890223 | 344.000144 | 5835.87798 | 5838.10656 |
| 开发者版 | 6573429.97 | 153.983992 | 208.000102 | 5720.17584 | 5722.66055 |
| 候选版 | 5992453.57 | 168.633907 | 288.000112 | 5886.3417 | 5888.70389 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1263129.75 | 798.496378 | 3224.00053 | 6213.27152 | 6215.08577 |
| 开发者版 | 1607370.88 | 630.506572 | 2128.00042 | 6180.39916 | 6182.40133 |
| 候选版 | 1524788.49 | 660.045552 | 3168.00044 | 6212.696 | 6215.15997 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 123981.224 | 8147.95674 | 30872.0054 | 6213.56111 | 6215.32847 |
| 开发者版 | 136711.997 | 7363.60732 | 30816.0049 | 6212.22458 | 6215.03361 |
| 候选版 | 136842.049 | 7355.23593 | 30816.0049 | 6212.08808 | 6214.73478 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.66694141 | 1.52756e+09 | 5.36871001e+09 | 6526.52928 | 6529.64138 |
| 开发者版 | 0.837809514 | 1.3438e+09 | 3.22122624e+09 | 5657.78511 | 5660.33047 |
| 候选版 | 0.841424224 | 1.33652e+09 | 3.22122624e+09 | 5657.41192 | 5660.25438 |

## 8a8337e

### plainNew

`io.netty.microbench.util.RecyclerBenchmark.plainNew` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 9.84518326 | 10.0051067 | 80.0000066 | 224.069344 | 226.131156 |
| 开发者版 | 9.8465019 | 10.011342 | 80.0000066 | 224.071359 | 225.897562 |
| 候选版 | 9.85385722 | 10.0141194 | 80.0000066 | 224.554125 | 226.619641 |

### producerConsumer

`io.netty.microbench.util.RecyclerBenchmark.producerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 313.620198 | 310.765597 | 14.5124073 | 223.036531 | 225.537719 |
| 开发者版 | 277.72627 | 272.847079 | 11.2691204 | 220.869391 | 223.669453 |
| 候选版 | 286.770316 | 276.832546 | 11.0020069 | 222.109734 | 224.762641 |

### recyclerGetAndOrphan

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndOrphan` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 14.8244395 | 15.0376093 | 83.00001 | 225.750906 | 227.984438 |
| 开发者版 | 15.4265442 | 15.6419015 | 83.0000105 | 225.934328 | 228.319906 |
| 候选版 | 15.4478484 | 15.6639555 | 83.0000105 | 226.634203 | 229.269672 |

### recyclerGetAndRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21.598176 | 21.7641213 | 1.46125942e-05 | 115.634203 | 116.564922 |
| 开发者版 | 26.0826739 | 26.2957463 | 1.7688259e-05 | 115.839375 | 116.715953 |
| 候选版 | 17.89408 | 18.044716 | 1.21290317e-05 | 114.837953 | 115.878609 |

## 95b8db0

### mixedDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.mixedDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.43935096 | 706.538634 | 1472.00047 | 226.375797 | 229.556172 |
| 开发者版 | 1.50946428 | 670.60844 | 1368.00045 | 230.277688 | 234.973859 |
| 候选版 | 1.50339763 | 672.958054 | 1382.40045 | 225.834937 | 228.989578 |

### noDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.noDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 7.40286616 | 137.689447 | 512.000091 | 226.081875 | 228.543766 |
| 开发者版 | 7.02722135 | 144.684428 | 504.000096 | 226.787031 | 229.719984 |
| 候选版 | 7.18433741 | 142.468991 | 504.000095 | 227.600375 | 230.665719 |

### nonStandardDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.nonStandardDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.68068145 | 603.657049 | 1344.0004 | 226.054906 | 229.232078 |
| 开发者版 | 1.52657733 | 663.269878 | 1348.80044 | 242.744953 | 254.679984 |
| 候选版 | 1.87788528 | 570.727876 | 1182.40038 | 233.961469 | 242.010969 |

### onlyDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.onlyDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.43281753 | 708.002025 | 1451.20047 | 225.811797 | 229.096094 |
| 开发者版 | 1.77910153 | 568.964073 | 1208.00038 | 235.383594 | 240.731906 |
| 候选版 | 1.83892747 | 563.502629 | 1208.00038 | 229.467781 | 237.401859 |

## 9abeaf1

### executeMulti

`io.netty.microbench.channel.epoll.EpollSocketChannelBenchmark.executeMulti` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 315007.526 | 6328.59226 | 56.0097598 | 399.71725 | 400.907438 |
| 开发者版 | 532657.854 | 3851.09695 | 56.0058709 | 297.158906 | 298.483969 |
| 候选版 | 531967.34 | 3837.72033 | 56.0061491 | 305.686953 | 307.511906 |

### executeSingle

`io.netty.microbench.channel.epoll.EpollSocketChannelBenchmark.executeSingle` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 188668.197 | 6032.37675 | 56.0114927 | 368.094328 | 369.343656 |
| 开发者版 | 203273.907 | 5265.56429 | 56.0108244 | 352.706359 | 353.667937 |
| 候选版 | 205270.825 | 5244.66908 | 56.010866 | 345.849703 | 346.577734 |

### pingPong

`io.netty.microbench.channel.epoll.EpollSocketChannelBenchmark.pingPong` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 66530.1405 | 15207.3018 | 192.032733 | 238.432469 | 239.947797 |
| 开发者版 | 69642.8985 | 14542.7354 | 192.031279 | 260.230938 | 260.967625 |
| 候选版 | 69182.3914 | 14623.0454 | 192.03155 | 250.248766 | 251.160438 |

## ab8c4f2

### lookupNameAndValueMatchFirst

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchFirst` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 16.7483669 | 16.8344314 | 1.12836478e-05 | 113.600219 | 114.250625 |
| 开发者版 | 13.4118896 | 13.4768809 | 9.03791559e-06 | 112.980281 | 113.817438 |
| 候选版 | 15.4440855 | 15.5211091 | 1.03946996e-05 | 113.146828 | 113.924953 |

### lookupNameAndValueMatchLast

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchLast` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 63.0698711 | 63.398644 | 4.25562855e-05 | 112.12975 | 112.947297 |
| 开发者版 | 66.0577875 | 66.4008913 | 4.45060585e-05 | 113.269031 | 114.186156 |
| 候选版 | 60.5044546 | 60.8148437 | 4.07602787e-05 | 113.902266 | 114.839031 |

### lookupNameOnlyMatchBeginTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchBeginTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 130.222143 | 130.924266 | 8.77679372e-05 | 112.760484 | 113.445891 |
| 开发者版 | 12.6431953 | 12.7079355 | 8.52160722e-06 | 113.206406 | 113.852984 |
| 候选版 | 16.6812406 | 16.7713209 | 1.12715459e-05 | 113.062047 | 113.728328 |

### lookupNameOnlyMatchEndTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchEndTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 19.0730681 | 19.1758029 | 1.28462472e-05 | 113.756141 | 114.505031 |
| 开发者版 | 9.83173518 | 9.88071524 | 6.63606364e-06 | 112.930094 | 113.677187 |
| 候选版 | 16.5836045 | 16.6724337 | 1.1184361e-05 | 113.12625 | 114.032047 |

### lookupNoNameMatch

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNoNameMatch` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4.11011459 | 4.13249196 | 2.76367379e-06 | 113.081109 | 113.783859 |
| 开发者版 | 4.58937123 | 4.61553495 | 3.08206656e-06 | 112.373453 | 113.097391 |
| 候选版 | 4.11428234 | 4.13703399 | 2.76475515e-06 | 112.092375 | 113.036391 |

## b72fea3

### parseHttpHeaderDateFormatterNew（DATE_STRING=Sun, 27 Jan 2016 19:18:46 GMT）

`io.netty.handler.codec.DateFormatter2Benchmark.parseHttpHeaderDateFormatterNew` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5023989.47 | 200.206353 | 24.0001343 | 223.979344 | 225.716328 |
| 开发者版 | 5920820.64 | 169.896494 | 24.0001146 | 222.376578 | 224.915453 |
| 候选版 | 4672414.42 | 218.186406 | 24.0001464 | 221.665828 | 223.522312 |

### parseHttpHeaderDateFormatterNew（DATE_STRING=Sun, 27 Dec 2016 19:18:46 GMT）

`io.netty.handler.codec.DateFormatter2Benchmark.parseHttpHeaderDateFormatterNew` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4570527.64 | 220.103364 | 24.0001477 | 222.658266 | 224.595531 |
| 开发者版 | 5904958.04 | 170.361089 | 24.0001143 | 223.485109 | 225.177547 |
| 候选版 | 4446681.83 | 226.347604 | 24.0001521 | 222.238922 | 224.032328 |

## feb804d

### scheduleCancelLotsOutsideLoop（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleCancelLotsOutsideLoop` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 197.739865 | 10705429.3 | 12003421 | 231.027062 | 233.692172 |
| 开发者版 | 208.387056 | 12006596.5 | 7203455.8 | 231.100672 | 233.144312 |
| 候选版 | 205.339631 | 10530953.2 | 9603454.42 | 230.604141 | 232.901828 |

### scheduleLots（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleLots` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 660.522726 | 4805808.98 | 6664139.09 | 256.443188 | 257.695953 |
| 开发者版 | 629.986823 | 4901215.28 | 6664139.16 | 256.494875 | 258.284391 |
| 候选版 | 642.285532 | 4900111.86 | 6664139.18 | 257.85575 | 259.616469 |

### scheduleLotsOutsideLoop（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleLotsOutsideLoop` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 325.940462 | 7879400.45 | 9591620.06 | 231.610391 | 233.866844 |
| 开发者版 | 352.562296 | 8902706.63 | 7191700.82 | 231.281828 | 234.008703 |
| 候选版 | 353.073545 | 7479627.16 | 7191670.01 | 231.541078 | 234.542953 |
