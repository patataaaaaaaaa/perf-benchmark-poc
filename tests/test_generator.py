import unittest

from src.benchmark.generator import extract_candidate


class ExtractCandidateTests(unittest.TestCase):
    def test_extracts_python_fence(self) -> None:
        result = extract_candidate("```python\nprint('ok')\n```")
        self.assertEqual(result.code, "print('ok')\n")
        self.assertFalse(result.skipped)

    def test_preserves_plain_source(self) -> None:
        result = extract_candidate("import pyperf\n")
        self.assertEqual(result.code, "import pyperf\n")

    def test_extracts_skip(self) -> None:
        result = extract_candidate("SKIP: requires a network service")
        self.assertTrue(result.skipped)
        self.assertEqual(result.skip_reason, "requires a network service")


if __name__ == "__main__":
    unittest.main()

