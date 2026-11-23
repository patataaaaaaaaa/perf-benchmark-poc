# OpenCode 8K 有 RAG逐场景绝对测量值

[返回汇报正文](../README.md)

本组覆盖 8 题、76 个场景。下表各值为同批次五个有效 JMH 区组分数的算术平均，最多保留 9 位有效数字。吞吐量越高越好，平均耗时和各项资源消耗越低越好。1 MiB = 1,048,576 字节。

## 2791f0f

### scheduleLots（num=100000）

`io.netty.util.concurrent.ScheduleFutureTaskBenchmark.scheduleLots` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 304.709818 | 9050451.89 | 6664254.4 | 243.09625 | 246.398328 |
| 开发者版 | 670.537115 | 4864993.64 | 6664250.2 | 251.482328 | 253.358422 |
| 候选版 | 667.104986 | 4848311.65 | 6664250.09 | 248.152938 | 250.441688 |

## 5a9b28a

### plainNew

`io.netty.microbench.util.RecyclerBenchmark.plainNew` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 10.0018612 | 10.1602855 | 80.0000067 | 224.888844 | 227.258672 |
| 开发者版 | 10.0084289 | 10.1677192 | 80.0000067 | 224.561953 | 227.063641 |
| 候选版 | 10.0283943 | 10.1847772 | 80.0000067 | 224.542188 | 227.004484 |

### producerConsumer

`io.netty.microbench.util.RecyclerBenchmark.producerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 49.1162457 | 49.1034935 | 0.00469911518 | 126.476187 | 127.152328 |
| 开发者版 | 52.3087766 | 52.2200954 | 0.0051748126 | 126.262062 | 126.996828 |
| 候选版 | 92.5139375 | 92.4033348 | 0.0105298872 | 124.1845 | 124.837 |

### recyclerGetAndOrphan

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndOrphan` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 15.7252811 | 15.9487433 | 83.0000107 | 227.074563 | 229.042156 |
| 开发者版 | 15.9696667 | 16.1978034 | 83.0000108 | 225.240125 | 227.443625 |
| 候选版 | 14.6035666 | 14.8153507 | 83.0000099 | 226.317828 | 228.472859 |

### recyclerGetAndRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 27.1853399 | 27.4099529 | 1.83956286e-05 | 116.793375 | 117.75275 |
| 开发者版 | 28.0941587 | 28.3330359 | 1.9070103e-05 | 116.487812 | 117.573969 |
| 候选版 | 27.5517432 | 27.7846651 | 1.8638017e-05 | 118.401906 | 119.171375 |

### recyclerGetAndUnguardedRecycle

`io.netty.microbench.util.RecyclerBenchmark.recyclerGetAndUnguardedRecycle` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 26.4222245 | 26.6397277 | 1.7957261e-05 | 118.039625 | 118.731906 |
| 开发者版 | 27.6353363 | 27.8751595 | 1.87906551e-05 | 116.674078 | 117.723141 |
| 候选版 | 25.1729527 | 25.3849041 | 1.71782457e-05 | 116.861313 | 117.922172 |

### unguardedProducerConsumer

`io.netty.microbench.util.RecyclerBenchmark.unguardedProducerConsumer` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 46.8576131 | 46.8121731 | 0.0058833773 | 132.811984 | 133.336344 |
| 开发者版 | 51.1221165 | 51.0725463 | 0.0055586653 | 125.541109 | 126.338359 |
| 候选版 | 77.9811623 | 77.8834775 | 0.0082436128 | 126.135047 | 126.839125 |

## 67d3a78

### arraysBytesEqual（size=10）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6.04487819 | 6.10011157 | 4.26303639e-06 | 99.2465938 | 100.060875 |
| 开发者版 | 6.04195482 | 6.09854215 | 4.25570563e-06 | 99.1389063 | 99.9715156 |
| 候选版 | 6.04377543 | 6.09849807 | 4.25317991e-06 | 98.7042969 | 99.6147187 |

### arraysBytesEqual（size=50）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 17.85926 | 18.020611 | 1.25804991e-05 | 99.1392188 | 99.9653906 |
| 开发者版 | 17.8524423 | 18.0134959 | 1.25631288e-05 | 97.7848281 | 98.8709375 |
| 候选版 | 17.8616649 | 18.0181469 | 1.25912493e-05 | 98.7765781 | 99.6340469 |

### arraysBytesEqual（size=100）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 32.5501135 | 32.8349518 | 2.29365104e-05 | 98.3024688 | 99.1146562 |
| 开发者版 | 32.5250029 | 32.7907836 | 2.29093923e-05 | 97.4560312 | 98.2824531 |
| 候选版 | 32.53756 | 32.8269589 | 2.29370886e-05 | 99.0570469 | 99.8657656 |

### arraysBytesEqual（size=1000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 297.026125 | 299.815493 | 0.00020942336 | 98.6869375 | 99.5612031 |
| 开发者版 | 296.900535 | 299.540713 | 0.000209222852 | 98.8350625 | 99.7988125 |
| 候选版 | 297.058717 | 299.895408 | 0.00020930563 | 98.0678437 | 98.9246875 |

### arraysBytesEqual（size=10000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 2886.91982 | 2912.46372 | 0.00203423405 | 98.7764844 | 99.6182656 |
| 开发者版 | 2884.62224 | 2910.14581 | 0.0020309789 | 98.1821563 | 99.0649375 |
| 候选版 | 2885.20997 | 2912.49209 | 0.00203461514 | 98.983125 | 99.6848281 |

### arraysBytesEqual（size=100000）

`io.netty.microbench.internal.PlatformDependentBenchmark.arraysBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 28886.0797 | 29138.0949 | 0.0203668967 | 98.9080312 | 99.7918437 |
| 开发者版 | 28808.6361 | 29080.0018 | 0.0202973113 | 99.0781094 | 100.011656 |
| 候选版 | 28836.5383 | 29078.9402 | 0.0203261659 | 98.2842656 | 99.3080312 |

### unsafeBytesEqual（size=10）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6.70533941 | 6.75847805 | 4.7423213e-06 | 110.046188 | 110.928016 |
| 开发者版 | 4.5697626 | 4.60921928 | 3.21715995e-06 | 110.676172 | 111.515203 |
| 候选版 | 4.60498393 | 4.64255602 | 3.24532714e-06 | 111.416891 | 112.414313 |

### unsafeBytesEqual（size=50）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 7.05551187 | 7.11467041 | 4.97267916e-06 | 111.091469 | 111.978688 |
| 开发者版 | 6.17112452 | 6.22380056 | 4.34803592e-06 | 109.747219 | 110.718297 |
| 候选版 | 6.20725895 | 6.26022933 | 4.37111699e-06 | 111.326672 | 112.023313 |

### unsafeBytesEqual（size=100）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 10.2015706 | 10.2881317 | 7.1883495e-06 | 111.389828 | 111.984594 |
| 开发者版 | 10.0052121 | 10.0940133 | 7.05091612e-06 | 111.504844 | 112.388703 |
| 候选版 | 9.27016481 | 9.34307069 | 6.53869987e-06 | 110.010453 | 110.870516 |

### unsafeBytesEqual（size=1000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 68.6523879 | 69.2679319 | 4.83297068e-05 | 111.53025 | 112.389766 |
| 开发者版 | 67.2612332 | 67.8481055 | 4.74159449e-05 | 110.408984 | 111.421391 |
| 候选版 | 66.6326585 | 67.2686786 | 4.70115599e-05 | 111.592609 | 112.514953 |

### unsafeBytesEqual（size=10000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 596.011132 | 601.35474 | 0.000420212126 | 111.605375 | 112.570422 |
| 开发者版 | 594.420544 | 599.311993 | 0.000418970781 | 111.845703 | 112.715937 |
| 候选版 | 594.184314 | 599.33493 | 0.000418670814 | 110.277203 | 111.346234 |

### unsafeBytesEqual（size=100000）

`io.netty.microbench.internal.PlatformDependentBenchmark.unsafeBytesEqual` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 6593.97387 | 6647.06482 | 0.00464659487 | 110.893875 | 111.782906 |
| 开发者版 | 6589.03584 | 6643.3318 | 0.00464566216 | 111.134859 | 112.021734 |
| 候选版 | 6593.12756 | 6653.27532 | 0.00464611989 | 110.326766 | 111.388984 |

## 687308b

### longAscii

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longAscii` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.396729196 | 2548.54241 | 5976.0017 | 226.067219 | 227.913516 |
| 开发者版 | 1.75620526 | 580.39797 | 3192.00038 | 227.287859 | 228.729094 |
| 候选版 | 0.765982993 | 1332.41874 | 3192.00089 | 224.96875 | 228.017656 |

### longAsciiFirst

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longAsciiFirst` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.034389475 | 29679.0518 | 52680.0198 | 227.276203 | 229.671828 |
| 开发者版 | 0.0464102704 | 22352.7635 | 54016.0149 | 226.31375 | 228.722406 |
| 候选版 | 0.0371206521 | 28404.4211 | 54016.0189 | 225.303844 | 227.907828 |

### longUtf8

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.longUtf8` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.0413282953 | 24495.3971 | 51480.0163 | 225.099031 | 228.041156 |
| 开发者版 | 0.0495209878 | 20657.7066 | 51480.0138 | 226.349719 | 229.084547 |
| 候选版 | 0.0445539365 | 23646.7956 | 51480.0158 | 226.396578 | 228.909531 |

### shortAscii

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortAscii` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 20.1310409 | 50.4229078 | 152.000034 | 225.614234 | 227.981875 |
| 开发者版 | 23.208156 | 43.9754542 | 147.200029 | 225.959578 | 228.597516 |
| 候选版 | 19.024679 | 53.2907134 | 152.000035 | 224.909656 | 227.845484 |

### shortAsciiFirst

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortAsciiFirst` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 2.8270546 | 360.133948 | 848.00024 | 227.817672 | 230.135312 |
| 开发者版 | 3.59586298 | 282.255247 | 848.000188 | 228.106766 | 230.481453 |
| 候选版 | 2.77155338 | 382.295294 | 848.000255 | 225.501953 | 227.904359 |

### shortUtf8

`io.netty.handler.codec.http.QueryStringEncoderBenchmark.shortUtf8` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 3.09001697 | 329.38046 | 840.000219 | 226.595703 | 229.543891 |
| 开发者版 | 3.82847012 | 265.413216 | 840.000177 | 229.003359 | 231.117437 |
| 候选版 | 2.96379543 | 342.135581 | 840.000227 | 226.266609 | 229.299062 |

## 87ec2f8

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18276788.1 | 55.26106 | 120.000037 | 6009.73595 | 6011.55998 |
| 开发者版 | 33469219.2 | 30.1852133 | 56.0000201 | 5922.77678 | 5925.05252 |
| 候选版 | 18475191.8 | 54.6829819 | 128.00004 | 6039.43527 | 6041.398 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 8676263.19 | 116.43023 | 232.000078 | 5973.28653 | 5975.48305 |
| 开发者版 | 21547105.7 | 47.0920317 | 168.000031 | 6188.29291 | 6190.2258 |
| 候选版 | 10972269.2 | 92.1514987 | 296.000061 | 6160.68502 | 6162.40236 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 396264.925 | 2540.27364 | 2216.0017 | 5312.28334 | 5313.02464 |
| 开发者版 | 2647842.12 | 380.098436 | 2088.00025 | 6213.99048 | 6215.7087 |
| 候选版 | 1446376.86 | 696.239394 | 3128.00047 | 6212.52722 | 6215.13022 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 33653.5432 | 29963.3068 | 20648.0201 | 5004.91628 | 5006.28189 |
| 开发者版 | 169159.441 | 5951.06209 | 30776.004 | 6213.57688 | 6215.63275 |
| 候选版 | 121223.11 | 8337.28686 | 30776.0056 | 6212.028 | 6214.31488 |

### decodeString（bufferType=DIRECT，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.339111767 | 2.959e+09 | 4.2949682e+09 | 5453.19084 | 5476.86945 |
| 开发者版 | 0.861568907 | 1.30288e+09 | 3.2212262e+09 | 6632.59713 | 6655.67833 |
| 候选版 | 0.851114986 | 1.317e+09 | 3.22122625e+09 | 6632.96072 | 6655.93936 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 14575493.8 | 69.3989237 | 184.000046 | 6099.50789 | 6101.27598 |
| 开发者版 | 23011295.2 | 43.9225469 | 96.0000294 | 6011.87841 | 6014.15489 |
| 候选版 | 23281173.5 | 44.1057989 | 120.000029 | 6099.21333 | 6101.11525 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5168123.26 | 195.103914 | 296.00013 | 5806.41633 | 5808.49981 |
| 开发者版 | 15801419.3 | 63.9454975 | 208.000042 | 6161.72803 | 6163.46903 |
| 候选版 | 15412543.6 | 65.2867493 | 288.000044 | 6212.68725 | 6214.57816 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 409446.556 | 2458.9769 | 2216.00165 | 5349.00022 | 5350.59481 |
| 开发者版 | 1870663.66 | 539.579383 | 2128.00036 | 6212.75222 | 6214.79592 |
| 候选版 | 1633891.41 | 615.976915 | 3168.00041 | 6213.83206 | 6215.7837 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 40536.8677 | 24835.6283 | 20648.0166 | 5261.99075 | 5263.24505 |
| 开发者版 | 137848.832 | 7303.01926 | 30816.0049 | 6212.71763 | 6214.7387 |
| 候选版 | 138058.758 | 7293.36956 | 30816.0049 | 6212.96027 | 6215.10323 |

### decodeString（bufferType=DIRECT，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.331964643 | 3.53468e+09 | 4.2949682e+09 | 5453.22733 | 5476.9357 |
| 开发者版 | 0.848877469 | 1.32188e+09 | 3.22122624e+09 | 6632.35364 | 6655.546 |
| 候选版 | 0.850014859 | 1.31808e+09 | 3.22122624e+09 | 6632.32967 | 6655.24147 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21853485 | 46.1647954 | 56.0000307 | 5637.31161 | 5639.52702 |
| 开发者版 | 47168640.4 | 21.4396333 | 56.0000155 | 6079.13817 | 6080.98625 |
| 候选版 | 24838594.7 | 40.694492 | 104.000029 | 6079.27038 | 6081.3148 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13141007 | 76.8810336 | 177.600051 | 6030.77295 | 6033.23253 |
| 开发者版 | 25606112.1 | 39.3177783 | 168.000026 | 6211.89611 | 6214.493 |
| 候选版 | 13794417.1 | 73.307557 | 216.000049 | 6132.24906 | 6134.13731 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1591933.79 | 642.529882 | 2107.20043 | 6172.09683 | 6174.09734 |
| 开发者版 | 2525348.12 | 398.584542 | 2088.00027 | 6213.45317 | 6215.79542 |
| 候选版 | 1591277.72 | 636.253084 | 2136.00042 | 6182.88178 | 6184.81084 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 156085.508 | 6514.34757 | 20558.4043 | 6168.81802 | 6170.80803 |
| 开发者版 | 206846.197 | 4867.27902 | 20520.0033 | 6213.04864 | 6215.21166 |
| 候选版 | 82479.9687 | 13791.8733 | 20568.0092 | 5835.27947 | 5837.77967 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.861312165 | 1.21894e+09 | 4.29496816e+09 | 5468.84128 | 5472.05758 |
| 开发者版 | 1.54896719 | 668320000 | 2.14748403e+09 | 5618.24094 | 5620.44381 |
| 候选版 | 1.49662987 | 687500000 | 2.14748407e+09 | 5591.12827 | 5593.80336 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18547414.6 | 54.4557232 | 104.000036 | 5946.84853 | 5948.99108 |
| 开发者版 | 35179649.4 | 28.7301877 | 96.0000191 | 6169.73669 | 6171.67342 |
| 候选版 | 27025746.2 | 37.3771777 | 96.0000272 | 6077.87416 | 6080.05073 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 12833829.6 | 78.6652402 | 216.000053 | 6107.22528 | 6109.55975 |
| 开发者版 | 19910280.7 | 50.6587045 | 208.000034 | 6211.92548 | 6214.44272 |
| 候选版 | 16255418.1 | 62.176188 | 208.000041 | 6169.98331 | 6171.71586 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1762999.86 | 574.343434 | 2136.00038 | 6212.17155 | 6214.02895 |
| 开发者版 | 2026302.36 | 496.833228 | 2128.00033 | 6212.57405 | 6215.0428 |
| 候选版 | 1913581.99 | 526.393561 | 2128.00035 | 6212.40645 | 6214.76077 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 153115.192 | 6587.46093 | 20568.0044 | 6164.81786 | 6166.7143 |
| 开发者版 | 175417.573 | 5757.26194 | 20560.0038 | 6210.87575 | 6212.52152 |
| 候选版 | 174992.661 | 5769.157 | 20560.0038 | 6209.42859 | 6211.59706 |

### decodeString（bufferType=HEAP_OFFSET，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.871966627 | 1.20036e+09 | 4.29496816e+09 | 5480.96789 | 5484.21228 |
| 开发者版 | 1.48777661 | 706573333 | 2.14748406e+09 | 5579.69809 | 5582.21102 |
| 候选版 | 1.49103969 | 714060000 | 2.14748406e+09 | 5579.16506 | 5581.57405 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 21878947.7 | 46.0978786 | 56.0000307 | 5640.62172 | 5643.37862 |
| 开发者版 | 47096262.8 | 21.4749806 | 56.0000155 | 6078.93484 | 6080.92261 |
| 候选版 | 24892752.8 | 40.5739511 | 104.00003 | 6077.6922 | 6079.74169 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 13062007.3 | 77.2905058 | 168.000052 | 6008.83855 | 6011.04602 |
| 开发者版 | 25590890.3 | 39.3650768 | 168.000026 | 6212.77808 | 6214.53109 |
| 候选版 | 13842738.9 | 73.044287 | 216.000049 | 6133.72684 | 6135.7743 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1584807.61 | 644.970999 | 2107.20043 | 6172.78411 | 6174.83923 |
| 开发者版 | 2523196.09 | 399.022101 | 2088.00027 | 6213.20183 | 6215.94497 |
| 候选版 | 1588400.55 | 637.369878 | 2136.00042 | 6182.32055 | 6184.03997 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 156177.033 | 6503.00262 | 20558.4043 | 6170.14917 | 6171.90212 |
| 开发者版 | 206507.741 | 4875.70235 | 20520.0033 | 6213.21803 | 6214.92669 |
| 候选版 | 82624.3927 | 13775.4357 | 20568.0092 | 5837.77966 | 5839.88258 |

### decodeString（bufferType=HEAP，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.861758436 | 1.21276e+09 | 4.29496816e+09 | 5474.67566 | 5477.70188 |
| 开发者版 | 1.54225317 | 678360000 | 2.14748403e+09 | 5596.63927 | 5599.35511 |
| 候选版 | 1.49558189 | 697146667 | 2.14748407e+09 | 5549.6778 | 5551.95041 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 18500396 | 54.5587589 | 104.000036 | 5946.4217 | 5948.76052 |
| 开发者版 | 35211793.2 | 28.7112176 | 96.0000192 | 6170.07362 | 6172.31358 |
| 候选版 | 26996443.8 | 37.412408 | 96.0000274 | 6077.29434 | 6079.05641 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 12876398.9 | 78.4436186 | 216.000052 | 6109.57213 | 6111.6015 |
| 开发者版 | 19906288.1 | 50.6674591 | 208.000034 | 6212.53481 | 6214.70016 |
| 候选版 | 16272168.1 | 62.1510684 | 208.000041 | 6170.88767 | 6172.45791 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1659280.79 | 621.210812 | 2136.00041 | 6190.90339 | 6192.73597 |
| 开发者版 | 2032348.17 | 495.277867 | 2128.00033 | 6212.48897 | 6214.93061 |
| 候选版 | 1907974.4 | 528.280773 | 2128.00035 | 6212.71422 | 6214.64964 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 152985.612 | 6593.62605 | 20568.0044 | 6168.07414 | 6169.49402 |
| 开发者版 | 175786.548 | 5742.37094 | 20560.0038 | 6208.97642 | 6211.00653 |
| 候选版 | 175487.078 | 5748.52072 | 20560.0038 | 6208.02922 | 6210.10312 |

### decodeString（bufferType=HEAP，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.875817832 | 1.1952e+09 | 4.29496816e+09 | 5468.96731 | 5472.37355 |
| 开发者版 | 1.49088732 | 702546667 | 2.14748407e+09 | 5611.86389 | 5614.4257 |
| 候选版 | 1.4884454 | 708073333 | 2.14748407e+09 | 5556.54695 | 5559.09633 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5011860.33 | 201.942562 | 176.000135 | 5308.30044 | 5309.64417 |
| 开发者版 | 8754623.58 | 115.056937 | 56.0000771 | 4658.68269 | 4660.52817 |
| 候选版 | 7007849.06 | 143.959145 | 128.000096 | 5327.79909 | 5329.38933 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4223629.23 | 242.434606 | 344.000161 | 5762.89777 | 5765.06463 |
| 开发者版 | 7365972.54 | 137.326711 | 168.000091 | 5641.91086 | 5644.23805 |
| 候选版 | 5485275.3 | 184.650804 | 296.000123 | 5841.74473 | 5844.00598 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 551787.673 | 1829.35081 | 3224.00122 | 5905.17597 | 5907.49434 |
| 开发者版 | 2206699.98 | 456.01101 | 2088.00031 | 6213.48277 | 6215.80753 |
| 候选版 | 1157878.41 | 964.011567 | 3176.00064 | 6162.97764 | 6165.40705 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 128190.979 | 7848.93474 | 30872.0052 | 6213.50241 | 6215.52609 |
| 开发者版 | 169866.698 | 5928.57599 | 30776.004 | 6213.55111 | 6215.55748 |
| 候选版 | 79794.5361 | 15296.7998 | 30824.0102 | 6013.58367 | 6015.46348 |

### decodeString（bufferType=COMPOSITE，charsetName=US-ASCII，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.658784645 | 1.54724e+09 | 5.36871001e+09 | 6526.05387 | 6528.99902 |
| 开发者版 | 0.855761655 | 1.316e+09 | 3.2212262e+09 | 5657.97908 | 5660.65134 |
| 候选版 | 0.839850902 | 1.33952e+09 | 3.22122625e+09 | 5657.83842 | 5660.30452 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=8）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5336903.38 | 188.929859 | 176.000126 | 5381.75038 | 5383.02984 |
| 开发者版 | 8144636.31 | 123.780923 | 96.0000828 | 5156.86744 | 5158.56395 |
| 候选版 | 7067101.94 | 142.694986 | 120.000095 | 5256.73144 | 5258.02325 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=64）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4631275.14 | 217.988332 | 344.000147 | 5831.29512 | 5833.41108 |
| 开发者版 | 6543479.84 | 154.404772 | 208.000103 | 5720.47142 | 5722.55897 |
| 候选版 | 5947043.99 | 169.886511 | 288.000113 | 5879.78005 | 5882.21723 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=1024）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1266362.54 | 796.516349 | 3224.00053 | 6213.36737 | 6215.44944 |
| 开发者版 | 1608713.21 | 629.94809 | 2128.00042 | 6180.56472 | 6182.36463 |
| 候选版 | 1514386.54 | 664.676228 | 3168.00044 | 6212.77142 | 6215.34077 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=10240）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 120339.959 | 8397.90975 | 30872.0056 | 6212.68741 | 6215.13678 |
| 开发者版 | 136788.691 | 7358.35077 | 30816.0049 | 6213.04233 | 6215.10847 |
| 候选版 | 136246.599 | 7386.12821 | 30816.0049 | 6213.46522 | 6215.49863 |

### decodeString（bufferType=COMPOSITE，charsetName=UTF-8，size=1073741824）

`io.netty.buffer.ByteBufUtilDecodeStringBenchmark.decodeString` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 0.668800473 | 1.52414e+09 | 5.36871001e+09 | 6526.22184 | 6529.26372 |
| 开发者版 | 0.839776892 | 1.3394e+09 | 3.22122624e+09 | 5657.9525 | 5660.65397 |
| 候选版 | 0.836113257 | 1.34624e+09 | 3.22122624e+09 | 5657.58873 | 5660.51566 |

## 95b8db0

### mixedDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.mixedDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.39545446 | 724.55928 | 1472.00048 | 226.366047 | 229.594266 |
| 开发者版 | 1.50023652 | 673.950967 | 1368.00045 | 230.629844 | 234.661344 |
| 候选版 | 1.51371357 | 668.259362 | 1376.00044 | 225.709906 | 228.822656 |

### noDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.noDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 7.57395589 | 134.047736 | 512.000089 | 225.88175 | 228.482672 |
| 开发者版 | 6.96356141 | 145.787772 | 504.000097 | 227.711406 | 230.503859 |
| 候选版 | 6.90274544 | 147.072177 | 504.000098 | 227.465344 | 230.014031 |

### nonStandardDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.nonStandardDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.67848838 | 605.831195 | 1374.4004 | 225.559328 | 228.586266 |
| 开发者版 | 1.51035896 | 670.401511 | 1368.00045 | 245.867406 | 258.759375 |
| 候选版 | 1.69843783 | 621.214434 | 1284.80042 | 241.652312 | 253.741719 |

### onlyDecoding

`io.netty.handler.codec.http.QueryStringDecoderBenchmark.onlyDecoding` · 吞吐量（ops/us）

| 版本 | 吞吐量（ops/us） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 1.48467872 | 682.15427 | 1432.00045 | 226.271859 | 229.073047 |
| 开发者版 | 1.72142306 | 593.041664 | 1208.0004 | 234.612281 | 241.950891 |
| 候选版 | 1.70829278 | 596.291723 | 1208.0004 | 234.177391 | 240.585016 |

## ab8c4f2

### lookupNameAndValueMatchFirst

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchFirst` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 15.4860378 | 15.5575532 | 1.04188799e-05 | 107.257531 | 108.286391 |
| 开发者版 | 13.367808 | 13.4344962 | 9.00748814e-06 | 107.910594 | 108.890797 |
| 候选版 | 15.4611694 | 15.5330935 | 1.04118237e-05 | 108.20025 | 109.228609 |

### lookupNameAndValueMatchLast

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameAndValueMatchLast` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 60.6274306 | 60.9552197 | 4.08458371e-05 | 109.082234 | 109.9195 |
| 开发者版 | 67.1499553 | 67.5125066 | 4.52631165e-05 | 107.895375 | 108.871812 |
| 候选版 | 60.691154 | 60.9927493 | 4.08750212e-05 | 107.798781 | 108.634234 |

### lookupNameOnlyMatchBeginTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchBeginTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 107.519695 | 108.111746 | 7.25080527e-05 | 107.028266 | 107.891422 |
| 开发者版 | 12.6971179 | 12.7605408 | 8.54470793e-06 | 107.581531 | 108.56625 |
| 候选版 | 18.590031 | 18.6822443 | 1.25234496e-05 | 108.734172 | 109.553562 |

### lookupNameOnlyMatchEndTable

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNameOnlyMatchEndTable` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 19.2856284 | 19.4034956 | 1.29946272e-05 | 108.806828 | 109.716969 |
| 开发者版 | 9.85467731 | 9.90650611 | 6.64165055e-06 | 107.484 | 108.436406 |
| 候选版 | 16.8555501 | 16.9465936 | 1.1359785e-05 | 108.432906 | 109.391156 |

### lookupNoNameMatch

`io.netty.handler.codec.http2.HpackStaticTableBenchmark.lookupNoNameMatch` · 平均耗时（ns/op）

| 版本 | 平均耗时（ns/op） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4.12292592 | 4.14536924 | 2.77031808e-06 | 108.660734 | 109.580984 |
| 开发者版 | 4.12112795 | 4.14259048 | 2.77406924e-06 | 107.904609 | 108.892594 |
| 候选版 | 4.1198873 | 4.1427648 | 2.76776616e-06 | 108.616859 | 109.38175 |

## b72fea3

### parseHttpHeaderDateFormatterNew（DATE_STRING=Sun, 27 Jan 2016 19:18:46 GMT）

`io.netty.handler.codec.DateFormatter2Benchmark.parseHttpHeaderDateFormatterNew` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 5055507 | 198.839516 | 24.0001336 | 223.085859 | 224.977406 |
| 开发者版 | 5947203.04 | 169.166675 | 24.0001143 | 222.047906 | 223.989859 |
| 候选版 | 6274003.09 | 160.588907 | 24.0001085 | 221.893594 | 223.411703 |

### parseHttpHeaderDateFormatterNew（DATE_STRING=Sun, 27 Dec 2016 19:18:46 GMT）

`io.netty.handler.codec.DateFormatter2Benchmark.parseHttpHeaderDateFormatterNew` · 吞吐量（ops/s）

| 版本 | 吞吐量（ops/s） | CPU 时间（ns/op） | 堆分配（B/op） | 驻留内存（MiB） | 内存高水位采样（MiB） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原版 | 4567873.4 | 220.194918 | 24.0001478 | 222.454656 | 223.809938 |
| 开发者版 | 5881828.31 | 171.05967 | 24.0001146 | 221.423063 | 223.968 |
| 候选版 | 6232093.78 | 161.732109 | 24.0001089 | 221.794719 | 223.556031 |
