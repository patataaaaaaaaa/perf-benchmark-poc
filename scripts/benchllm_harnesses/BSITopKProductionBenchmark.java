package org.roaringbitmap;

import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;
import org.roaringbitmap.bsi.buffer.MutableBitSliceIndex;
import org.roaringbitmap.buffer.MutableRoaringBitmap;

@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
public class BSITopKProductionBenchmark {
  @Param({"1000", "10000"})
  public int count;
  @Param({"20", "200"})
  public int k;
  private MutableBitSliceIndex index;

  @Setup
  public void setup() {
    index = new MutableBitSliceIndex(1, 99);
    // Tied values exercise topK's final removal path changed by this task.
    for (int i = 0; i < count; i++) {
      index.setValue(i, 99);
    }
    if (index.topK(null, k).getCardinality() != k) {
      throw new IllegalStateException("Unexpected topK cardinality");
    }
  }

  @Benchmark
  public MutableRoaringBitmap topK() {
    return index.topK(null, k);
  }
}
