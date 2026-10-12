/** Minimal reproduction of the historical Netty/JUnit overload interaction.
 * No project tests or production files are changed by this probe.
 */
public final class SourceInferenceProbe {
    static void assertEquals(long expected, long actual) { }
    static void assertEquals(Object expected, Object actual) { }
    static <T> T readOutbound() { return null; }

    static void originalCall() {
        assertEquals(1L, readOutbound());
    }
}
