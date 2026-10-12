import java.io.*;
import java.nio.*;
import java.util.*;
import org.roaringbitmap.*;
import org.roaringbitmap.buffer.*;
import org.roaringbitmap.longlong.IntegerUtil;

/** Independent diagnostic probes; no candidate source is changed. */
public class FunctionalProbe {
  interface Check { void run() throws Exception; }
  static void check(String name, Check c) {
    try { c.run(); System.out.println("PASS\t" + name); }
    catch (Throwable e) { System.out.println("FAIL\t" + name + "\t" + e); }
  }
  static void eq(long expected, long actual, String where) {
    if (expected != actual) throw new AssertionError(where + ": expected=" + expected + ", actual=" + actual);
  }
  static int referenceShift(int v, int pos, int count) {
    byte[] bytes = {(byte)(v >>> 24), (byte)(v >>> 16), (byte)(v >>> 8), (byte)v};
    System.arraycopy(bytes, pos + 1, bytes, pos, count);
    return ((bytes[0] & 255) << 24) | ((bytes[1] & 255) << 16)
        | ((bytes[2] & 255) << 8) | (bytes[3] & 255);
  }
  static void shift() {
    check("shift_valid_inputs", () -> {
      Random r = new Random(20261009L);
      int[] special = {0, -1, Integer.MIN_VALUE, Integer.MAX_VALUE, 0xAABBCCDD, 0x01020304};
      for (int n = 0; n < 10006; n++) {
        int v = n < special.length ? special[n] : r.nextInt();
        for (int pos = 0; pos < 4; pos++) for (int count = 0; count < 4 - pos; count++)
          eq(referenceShift(v, pos, count), IntegerUtil.shiftLeftFromSpecifiedPosition(v, pos, count),
              "value=" + v + ",pos=" + pos + ",count=" + count);
      }
    });
    check("shift_invalid_input_exception_compatibility", () -> {
      int[][] cases = {{-1, 0}, {4, 0}, {0, -1}, {0, 4}, {2, 2}};
      for (int[] c : cases) {
        boolean throwsReference = false, throwsCandidate = false;
        try { referenceShift(0xAABBCCDD, c[0], c[1]); } catch (IndexOutOfBoundsException e) { throwsReference = true; }
        try { IntegerUtil.shiftLeftFromSpecifiedPosition(0xAABBCCDD, c[0], c[1]); } catch (IndexOutOfBoundsException e) { throwsCandidate = true; }
        eq(throwsReference ? 1 : 0, throwsCandidate ? 1 : 0, "pos=" + c[0] + ",count=" + c[1]);
      }
    });
  }
  static void containers() {
    check("mappeable_warm_cache_mutation_sequence", () -> {
      MappeableContainer c = new MappeableRunContainer(); BitSet expected = new BitSet(65536);
      Random r = new Random(20261009L);
      for (int n = 0; n < 4000; n++) {
        eq(expected.cardinality(), c.getCardinality(), "before step " + n);
        int x = r.nextInt(65536), lo = r.nextInt(65472), hi = lo + r.nextInt(64);
        switch (n % 6) {
          case 0: c = c.add((char)x); expected.set(x); break;
          case 1: c = c.remove((char)x); expected.clear(x); break;
          case 2: c = c.iadd(lo, hi); expected.set(lo, hi); break;
          case 3: c = c.iremove(lo, hi); expected.clear(lo, hi); break;
          case 4: c = c.inot(lo, hi); expected.flip(lo, hi); break;
          default: c = c.flip((char)x); expected.flip(x);
        }
        eq(expected.cardinality(), c.getCardinality(), "after step " + n);
        eq(expected.get(x) ? 1 : 0, c.contains((char)x) ? 1 : 0, "membership step " + n);
      }
    });
    check("run_warm_cache_mutation_sequence", () -> {
      Container c = new RunContainer(); BitSet expected = new BitSet(65536);
      Random r = new Random(20261009L);
      for (int n = 0; n < 4000; n++) {
        eq(expected.cardinality(), c.getCardinality(), "before step " + n);
        int x = r.nextInt(65536), lo = r.nextInt(65472), hi = lo + r.nextInt(64);
        switch (n % 6) {
          case 0: c = c.add((char)x); expected.set(x); break;
          case 1: c = c.remove((char)x); expected.clear(x); break;
          case 2: c = c.iadd(lo, hi); expected.set(lo, hi); break;
          case 3: c = c.iremove(lo, hi); expected.clear(lo, hi); break;
          case 4: c = c.inot(lo, hi); expected.flip(lo, hi); break;
          default: c = c.flip((char)x); expected.flip(x);
        }
        eq(expected.cardinality(), c.getCardinality(), "after step " + n);
        eq(expected.get(x) ? 1 : 0, c.contains((char)x) ? 1 : 0, "membership step " + n);
      }
    });
    check("mappeable_readExternal_after_cached_query", () -> {
      MappeableRunContainer target = new MappeableRunContainer(0, 2);
      eq(2, target.getCardinality(), "preload");
      ByteArrayOutputStream bytes = new ByteArrayOutputStream();
      try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
        new MappeableRunContainer(10, 15).writeExternal(out);
      }
      target.readExternal(new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray())));
      eq(5, target.getCardinality(), "after readExternal");
      eq(1, target.contains((char)14) ? 1 : 0, "loaded membership");
    });
    check("mappeable_shared_heap_buffer", () -> shared(false));
    check("mappeable_shared_direct_buffer", () -> shared(true));
  }
  static void shared(boolean direct) {
    CharBuffer buffer = direct ? ByteBuffer.allocateDirect(4).asCharBuffer() : CharBuffer.allocate(2);
    buffer.put(0, (char)0); buffer.put(1, (char)0);
    MappeableRunContainer a = new MappeableRunContainer(buffer, 1);
    MappeableRunContainer b = new MappeableRunContainer(buffer, 1);
    eq(1, a.getCardinality(), "cached query");
    b.add((char)1); // Extends the existing run in the shared buffer, without resizing.
    eq(1, a.contains((char)1) ? 1 : 0, "shared content changed");
    eq(2, a.getCardinality(), "count must match shared content");
  }
  static void checkedAdd() {
    for (boolean mutable : new boolean[]{false, true}) {
      for (int mode = 0; mode < 4; mode++) {
        final boolean m = mutable; final int kind = mode;
        check((m ? "mutable" : "roaring") + "_checkedAdd_mode" + kind, () -> addSequence(m, kind));
      }
    }
  }
  static void addSequence(boolean mutable, int mode) {
    RoaringBitmap plain = new RoaringBitmap(); MutableRoaringBitmap mapped = new MutableRoaringBitmap();
    Set<Integer> expected = new HashSet<>();
    int[] seeds = {0, 1, -1, Integer.MIN_VALUE, Integer.MAX_VALUE, 65535, 65536, 131071};
    for (int x : seeds) { plain.add(x); mapped.add(x); expected.add(x); }
    // 4094 values plus the seed 65535 give 4095 entries in the low-key array
    // container; subsequent additions exercise the 4096 -> 4097 transition.
    int limit = mode == 1 ? 10000 : mode == 2 ? 4094 : 0;
    for (int x = 0; x < limit; x++) { plain.add(x); mapped.add(x); expected.add(x); }
    if (mode == 1) { plain.runOptimize(); mapped.runOptimize(); }
    if (mode == 3) for (int x = 0; x < 12000; x += 2) { plain.add(x); mapped.add(x); expected.add(x); }
    Random r = new Random(20261009L);
    for (int n = 0; n < 2000; n++) {
      int x = n % 7 == 0 ? seeds[n % seeds.length] : n % 7 == 1 ? r.nextInt() : n % 7 == 2 ? 4090 + n % 20 : r.nextInt(20000);
      boolean wanted = expected.add(x);
      boolean got = mutable ? mapped.checkedAdd(x) : plain.checkedAdd(x);
      eq(wanted ? 1 : 0, got ? 1 : 0, "return step " + n);
      eq(0, (mutable ? mapped.checkedAdd(x) : plain.checkedAdd(x)) ? 1 : 0, "duplicate step " + n);
      eq(expected.size(), mutable ? mapped.getCardinality() : plain.getCardinality(), "count step " + n);
    }
    int[] values = mutable ? mapped.toArray() : plain.toArray();
    eq(expected.size(), values.length, "final size");
    for (int x : values) if (!expected.contains(x)) throw new AssertionError("unexpected final element " + x);
  }
  public static void main(String[] args) {
    if (args[0].equals("34bce1b")) shift();
    else if (args[0].equals("b5b4af6")) containers();
    else if (args[0].equals("53ba593")) checkedAdd();
    else throw new IllegalArgumentException(args[0]);
  }
}
