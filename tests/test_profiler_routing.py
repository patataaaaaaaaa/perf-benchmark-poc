import unittest

from src.framework.profiler_routing import (
    require_objective_profiler,
    route_from_task_classification,
    select_profiler_route,
    select_target_profiler,
)


class ProfilerRoutingTests(unittest.TestCase):
    def test_mixed_memory_objective_selects_measured_memory_report(self) -> None:
        profiler, reason = select_target_profiler(
            {
                "task_type": "mixed",
                "signals": {"cpu_bound": True, "memory": True, "io": False},
            },
            {"cprofile": {}, "tracemalloc": {}},
            optimization_objective="memory",
        )
        self.assertEqual(profiler, "tracemalloc")
        self.assertIn("内存", reason)

    def test_memory_objective_cannot_invent_unmeasured_memory_signal(self) -> None:
        profiler, _reason = select_target_profiler(
            {
                "task_type": "cpu_bound",
                "signals": {"cpu_bound": True, "memory": False, "io": False},
            },
            {"cprofile": {}, "tracemalloc": {}},
            optimization_objective="memory",
        )
        self.assertEqual(profiler, "cprofile")

    def test_selects_one_profiler_for_single_type(self) -> None:
        route = select_profiler_route({"task_type": "memory", "signals": {"memory": True}})
        self.assertEqual([item.name for item in route.selected_profilers], ["tracemalloc"])
        self.assertTrue(route.selection_applied)
        self.assertFalse(route.execution_applied)
        self.assertFalse(route.optimization_decision_impact)

    def test_mixed_selects_all_present_signals(self) -> None:
        route = select_profiler_route(
            {
                "task_type": "mixed",
                "signals": {"cpu_bound": True, "memory": True, "io": False},
            }
        )
        self.assertEqual(
            [item.name for item in route.selected_profilers],
            ["cprofile", "tracemalloc"],
        )

    def test_unavailable_classification_does_not_guess(self) -> None:
        route = route_from_task_classification({"status": "UNAVAILABLE"})
        self.assertEqual(route["status"], "UNAVAILABLE")
        self.assertFalse(route["selection_applied"])
        self.assertEqual(route["selected_profilers"], [])

    def test_memory_objective_adds_required_profiler_without_changing_type(self) -> None:
        route = route_from_task_classification(
            {
                "classification": {
                    "task_type": "cpu_bound",
                    "signals": {"cpu_bound": True, "memory": False},
                }
            }
        )
        result = require_objective_profiler(route, "memory")
        self.assertEqual(result["task_type"], "cpu_bound")
        self.assertEqual(
            [item["name"] for item in result["selected_profilers"]],
            ["cprofile", "tracemalloc"],
        )
        self.assertEqual(
            result["objective_requirement"]["source"],
            "explicit_experiment_objective",
        )


if __name__ == "__main__":
    unittest.main()
