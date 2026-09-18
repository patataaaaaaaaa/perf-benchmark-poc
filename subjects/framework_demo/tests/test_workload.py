from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from demo_subject.workload import center_values  # noqa: E402


class CenterValuesTests(unittest.TestCase):
    def test_known_values(self) -> None:
        self.assertEqual(center_values([1.0, 2.0, 3.0]), [-1.0, 0.0, 1.0])

    def test_empty_values(self) -> None:
        self.assertEqual(center_values([]), [])

    def test_input_is_not_mutated(self) -> None:
        values = [2.5, 4.5, 9.0]
        original = list(values)
        center_values(values)
        self.assertEqual(values, original)

    def test_result_is_centered(self) -> None:
        result = center_values(tuple(range(20)))
        self.assertAlmostEqual(sum(result), 0.0)


if __name__ == "__main__":
    unittest.main()

