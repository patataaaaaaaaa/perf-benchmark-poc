import org.roaringbitmap.IntIterator;
import org.roaringbitmap.bsi.buffer.MutableBitSliceIndex;
import org.roaringbitmap.buffer.MutableRoaringBitmap;

/** Diagnoses the unchanged original/developer versions; never applies a fix. */
public class TopKProbe {
  public static void main(String[] args) {
    for (int count : new int[]{1000, 10000}) {
      for (int k : new int[]{20, 200}) {
        MutableBitSliceIndex index = new MutableBitSliceIndex(1, 99);
        for (int i = 0; i < count; i++) index.setValue(i, 99);
        try {
          int actual = index.topK(null, k).getCardinality();
          System.out.println("topK count=" + count + " k=" + k + " actual=" + actual
              + " status=" + (actual == k ? "PASS" : "FAIL"));
        } catch (RuntimeException e) {
          System.out.println("topK count=" + count + " k=" + k + " status=EXCEPTION " + e);
        }
      }
    }
    MutableRoaringBitmap bitmap = new MutableRoaringBitmap();
    for (int i = 0; i < 1000; i++) bitmap.add(i);
    IntIterator iterator = bitmap.getIntIterator();
    int remainingToRemove = 980;
    int removed = 0;
    while (iterator.hasNext() && remainingToRemove > 0) {
      bitmap.remove(iterator.next());
      remainingToRemove--;
      removed++;
    }
    System.out.println("iterator_external_remove expectedCardinality=20 actualCardinality="
        + bitmap.getCardinality() + " removed=" + removed + " remainingToRemove=" + remainingToRemove);
  }
}
