import unittest

from src.framework.task_classification import (
    PerformanceSample,
    classify_performance_task,
)


def sample(**overrides: object) -> PerformanceSample:
    values: dict[str, object] = {
        "wall_seconds": 1.0,
        "user_cpu_seconds": 0.9,
        "system_cpu_seconds": 0.05,
        "cpu_to_wall_ratio": 0.95,
        "peak_rss_bytes": 40 * 1024 * 1024,
        "tracemalloc_peak_bytes": 5 * 1024 * 1024,
        "read_bytes": 0,
        "write_bytes": 0,
        "read_count": 0,
        "write_count": 0,
    }
    values.update(overrides)
    return PerformanceSample(**values)  # type: ignore[arg-type]


class TaskClassificationTests(unittest.TestCase):
    def test_classifies_cpu_bound_workload(self) -> None:
        result = classify_performance_task([sample(), sample(cpu_to_wall_ratio=0.92)])
        self.assertEqual(result.task_type, "cpu_bound")
        self.assertEqual(result.confidence, "high")
        self.assertTrue(result.signals["cpu_bound"])

    def test_classifies_io_bound_workload(self) -> None:
        result = classify_performance_task(
            [
                sample(
                    user_cpu_seconds=0.2,
                    system_cpu_seconds=0.1,
                    cpu_to_wall_ratio=0.3,
                    read_bytes=32 * 1024 * 1024,
                    read_count=1000,
                )
            ]
        )
        self.assertEqual(result.task_type, "io")
        self.assertEqual(result.confidence, "high")

    def test_fixed_interpreter_io_count_is_not_an_io_signal(self) -> None:
        result = classify_performance_task(
            [
                sample(
                    cpu_to_wall_ratio=0.3,
                    input_size=10,
                    read_bytes=0,
                    write_bytes=0,
                    read_count=129,
                    write_count=0,
                ),
                sample(
                    cpu_to_wall_ratio=0.3,
                    input_size=100,
                    read_bytes=0,
                    write_bytes=0,
                    read_count=129,
                    write_count=0,
                ),
            ]
        )
        self.assertFalse(result.signals["io"])

    def test_small_interpreter_io_count_variation_is_not_an_io_signal(self) -> None:
        result = classify_performance_task(
            [
                sample(
                    cpu_to_wall_ratio=0.3,
                    input_size=16,
                    read_bytes=0,
                    write_bytes=0,
                    read_count=102,
                    write_count=0,
                ),
                sample(
                    cpu_to_wall_ratio=0.3,
                    input_size=64,
                    read_bytes=0,
                    write_bytes=0,
                    read_count=131,
                    write_count=0,
                ),
            ]
        )
        self.assertFalse(result.signals["io"])

    def test_memory_requires_scaling_evidence(self) -> None:
        single = classify_performance_task(
            [
                sample(
                    cpu_to_wall_ratio=0.2,
                    peak_rss_bytes=512 * 1024 * 1024,
                )
            ]
        )
        self.assertEqual(single.task_type, "unknown")

        scaled = classify_performance_task(
            [
                sample(
                    cpu_to_wall_ratio=0.3,
                    input_size=100,
                    peak_rss_bytes=32 * 1024 * 1024,
                    tracemalloc_peak_bytes=8 * 1024 * 1024,
                ),
                sample(
                    cpu_to_wall_ratio=0.3,
                    input_size=1000,
                    peak_rss_bytes=128 * 1024 * 1024,
                    tracemalloc_peak_bytes=64 * 1024 * 1024,
                ),
            ]
        )
        self.assertEqual(scaled.task_type, "memory")
        self.assertEqual(scaled.confidence, "high")

    def test_multiple_signals_are_mixed(self) -> None:
        result = classify_performance_task(
            [
                sample(input_size=100, peak_rss_bytes=32 * 1024 * 1024),
                sample(input_size=1000, peak_rss_bytes=128 * 1024 * 1024),
            ]
        )
        self.assertEqual(result.task_type, "mixed")
        self.assertTrue(result.signals["cpu_bound"])
        self.assertTrue(result.signals["memory"])

    def test_goal_is_context_not_an_override(self) -> None:
        result = classify_performance_task(
            [sample()], declared_goal="memory"
        )
        self.assertEqual(result.task_type, "cpu_bound")
        self.assertEqual(result.declared_goal, "memory")

    def test_loads_existing_resource_result_shape(self) -> None:
        parsed = PerformanceSample.from_mapping(
            {
                "command": {
                    "metrics": {
                        "wall_seconds": 2.0,
                        "user_cpu_seconds": 1.5,
                        "system_cpu_seconds": 0.1,
                        "cpu_to_wall_ratio": 0.8,
                        "peak_rss_bytes": 123,
                        "read_bytes": None,
                        "write_bytes": None,
                    }
                },
                "tracemalloc_peak_bytes": 456,
                "workload": {"input_size": 1000},
            }
        )
        self.assertEqual(parsed.input_size, 1000)
        self.assertEqual(parsed.tracemalloc_peak_bytes, 456)
        self.assertEqual(parsed.peak_rss_bytes, 123)


if __name__ == "__main__":
    unittest.main()
