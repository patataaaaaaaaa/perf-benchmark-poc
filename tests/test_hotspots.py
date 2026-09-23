import cProfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.framework.hotspots import contains_symbol, parse_cprofile, select_top_hotspot


class _FakeStats:
    total_tt = 10.0

    def __init__(self, _path: str) -> None:
        self.stats = {}


class HotspotTests(unittest.TestCase):
    def test_src_layout_is_removed_from_qualified_name(self) -> None:
        with TemporaryDirectory() as temporary:
            repository = Path(temporary)
            source = repository / "src" / "package" / "module.py"
            source.parent.mkdir(parents=True)
            source.write_text("def target():\n    return 1\n", encoding="utf-8")
            profile = repository / "profile.prof"
            profiler = cProfile.Profile()
            namespace: dict[str, object] = {}
            exec(compile(source.read_text(), str(source), "exec"), namespace)
            profiler.runcall(namespace["target"])
            profiler.dump_stats(str(profile))

            report = parse_cprofile(profile, repository)
            self.assertEqual(
                report["hotspots"][0]["qualified_name"], "package.module.target"
            )

    def test_cpython_lib_layout_is_removed_from_qualified_name(self) -> None:
        with TemporaryDirectory() as temporary:
            repository = Path(temporary)
            source = repository / "Lib" / "urllib" / "parse.py"
            source.parent.mkdir(parents=True)
            source.write_text("def target():\n    return 1\n", encoding="utf-8")
            profile = repository / "profile.prof"
            profiler = cProfile.Profile()
            namespace: dict[str, object] = {}
            exec(compile(source.read_text(), str(source), "exec"), namespace)
            profiler.runcall(namespace["target"])
            profiler.dump_stats(str(profile))

            report = parse_cprofile(profile, repository)
            self.assertEqual(
                report["hotspots"][0]["qualified_name"],
                "urllib.parse.target",
            )

    def test_filters_non_project_and_test_code_then_ranks_self_time(self) -> None:
        with TemporaryDirectory() as temporary:
            repository = Path(temporary).resolve()
            fake = _FakeStats("unused")
            fake.stats = {
                (str(repository / "pkg" / "core.py"), 10, "slow"): (
                    1,
                    5,
                    6.0,
                    7.0,
                    {},
                ),
                (str(repository / "pkg" / "helper.py"), 20, "helper"): (
                    1,
                    2,
                    2.0,
                    9.0,
                    {},
                ),
                (str(repository / "tests" / "test_core.py"), 3, "test_slow"): (
                    1,
                    1,
                    9.0,
                    9.0,
                    {},
                ),
                ("/outside/library.py", 1, "external"): (1, 1, 8.0, 8.0, {}),
                ("<frozen importlib._bootstrap>", 1, "find_spec"): (
                    1,
                    1,
                    7.0,
                    7.0,
                    {},
                ),
            }
            with patch("src.framework.hotspots.pstats.Stats", return_value=fake):
                report = parse_cprofile(
                    repository / "profile.prof", repository, limit=5
                )

        self.assertEqual(report["project_function_count"], 2)
        self.assertEqual(
            [item["qualified_name"] for item in report["hotspots"]],
            ["pkg.core.slow", "pkg.helper.helper"],
        )
        self.assertEqual(report["hotspots"][0]["self_time_percent"], 60.0)
        self.assertTrue(contains_symbol(report, "pkg.core.slow"))
        self.assertFalse(contains_symbol(report, "pkg.missing"))

    def test_maps_container_paths_back_to_repository(self) -> None:
        with TemporaryDirectory() as temporary:
            repository = Path(temporary).resolve()
            fake = _FakeStats("unused")
            fake.stats = {
                ("/workspace/pkg/core.py", 10, "slow"): (1, 2, 5.0, 6.0, {})
            }
            with patch("src.framework.hotspots.pstats.Stats", return_value=fake):
                report = parse_cprofile(
                    repository / "profile.prof",
                    repository,
                    recorded_repository=Path("/workspace"),
                )
        self.assertEqual(report["hotspots"][0]["file"], "pkg/core.py")
        self.assertEqual(report["hotspots"][0]["qualified_name"], "pkg.core.slow")

    def test_class_method_keeps_enclosing_class_in_qualified_name(self) -> None:
        with TemporaryDirectory() as temporary:
            repository = Path(temporary).resolve()
            source = repository / "pkg" / "core.py"
            source.parent.mkdir(parents=True)
            source.write_text(
                "class Cursor:\n"
                "    def __next__(self):\n"
                "        return 1\n",
                encoding="utf-8",
            )
            fake = _FakeStats("unused")
            fake.stats = {
                (str(source), 2, "__next__"): (1, 4, 5.0, 6.0, {})
            }
            with patch("src.framework.hotspots.pstats.Stats", return_value=fake):
                report = parse_cprofile(
                    repository / "profile.prof", repository, limit=5
                )

        self.assertEqual(
            report["hotspots"][0]["qualified_name"],
            "pkg.core.Cursor.__next__",
        )

    def test_limit_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 1"):
            parse_cprofile(Path("missing.prof"), Path.cwd(), limit=0)

    def test_selects_top_hotspot_without_using_expected_symbol_for_ranking(self) -> None:
        report = {
            "hotspots": [
                {
                    "file": "pkg/core.py",
                    "qualified_name": "pkg.core.slow",
                },
                {
                    "file": "pkg/other.py",
                    "qualified_name": "pkg.other.second",
                },
            ]
        }
        path, symbol = select_top_hotspot(
            report, expected_symbol="pkg.core.slow"
        )
        self.assertEqual(path, Path("pkg/core.py"))
        self.assertEqual(symbol, "pkg.core.slow")

    def test_rejects_unexpected_top_hotspot(self) -> None:
        report = {
            "hotspots": [
                {"file": "pkg/core.py", "qualified_name": "pkg.core.wrong"}
            ]
        }
        with self.assertRaisesRegex(ValueError, "Top hotspot"):
            select_top_hotspot(report, expected_symbol="pkg.core.expected")


if __name__ == "__main__":
    unittest.main()
