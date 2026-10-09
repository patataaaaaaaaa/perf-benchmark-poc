package org.roaringbitmap.art;

import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;

@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
public class Node16ProductionBenchmark {
  @Param({"0", "7", "8", "15"})
  public int pos;
  private Node16 node;

  @Setup
  public void setup() {
    node = new Node16(0);
    node.firstV = 0x0001020304050607L;
    node.secondV = 0x08090a0b0c0d0e0fL;
    node.count = 16;
    if (node.getChildKey(pos) != (byte) pos) {
      throw new IllegalStateException("Unexpected child key");
    }
  }

  @Benchmark
  public byte getChildKey() {
    return node.getChildKey(pos);
  }
}
