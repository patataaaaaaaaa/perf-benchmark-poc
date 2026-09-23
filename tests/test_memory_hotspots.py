import tempfile
import tracemalloc
import unittest
from pathlib import Path

from src.framework.memory_hotspots import _module_name, parse_tracemalloc_snapshot


class MemoryHotspotTests(unittest.TestCase):
    def test_cpython_lib_layout_is_removed_from_module_name(self) -> None:
        self.assertEqual(
            _module_name(Path("Lib/urllib/parse.py")), "urllib.parse"
        )

    def test_parses_repository_allocation_top_n(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            source = repository / "src" / "samplepkg" / "worker.py"
            source.parent.mkdir(parents=True)
            source.write_text(
                "def allocate():\n"
                "    return [bytearray(4096) for _ in range(64)]\n",
                encoding="utf-8",
            )
            namespace: dict[str, object] = {}
            tracemalloc.start(5)
            try:
                exec(compile(source.read_text(), str(source), "exec"), namespace)
                held = namespace["allocate"]()  # type: ignore[operator]
                self.assertEqual(len(held), 64)
                snapshot_path = repository / "snapshot.dat"
                tracemalloc.take_snapshot().dump(str(snapshot_path))
            finally:
                tracemalloc.stop()

            report = parse_tracemalloc_snapshot(snapshot_path, repository, limit=3)

            self.assertEqual(report["profile_format"], "tracemalloc_snapshot")
            self.assertTrue(report["hotspots"])
            top = report["hotspots"][0]
            self.assertEqual(top["file"], "src/samplepkg/worker.py")
            self.assertEqual(top["function"], "allocate")
            self.assertEqual(top["qualified_name"], "samplepkg.worker.allocate")
            self.assertGreater(top["size_bytes"], 200_000)


if __name__ == "__main__":
    unittest.main()
