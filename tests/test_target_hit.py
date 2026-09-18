import unittest

from src.benchmark.validator import check_target_hit
from src.target.loader import TargetSpec


SPEC = TargetSpec(
    id="sympy_expand_001",
    module="sympy",
    target="expand",
    qualified_name="sympy.expand",
    description="test",
)


class TargetHitTests(unittest.TestCase):
    def test_direct_import_and_call_is_true(self) -> None:
        code = "from sympy import expand\nvalue = expand(expr)\n"
        self.assertEqual(check_target_hit(code, SPEC), "true")

    def test_module_alias_call_is_true(self) -> None:
        code = "import sympy as sp\nvalue = sp.expand(expr)\n"
        self.assertEqual(check_target_hit(code, SPEC), "true")

    def test_bench_func_reference_is_true(self) -> None:
        code = (
            "import pyperf\n"
            "from sympy import expand\n"
            "runner = pyperf.Runner()\n"
            "runner.bench_func('expand', expand, expr)\n"
        )
        self.assertEqual(check_target_hit(code, SPEC), "true")

    def test_local_dummy_is_not_a_hit(self) -> None:
        code = "def expand(value):\n    return value\n\nexpand(1)\n"
        self.assertEqual(check_target_hit(code, SPEC), "false")

    def test_import_without_call_is_unknown(self) -> None:
        code = "from sympy import expand\n"
        self.assertEqual(check_target_hit(code, SPEC), "unknown")


if __name__ == "__main__":
    unittest.main()

