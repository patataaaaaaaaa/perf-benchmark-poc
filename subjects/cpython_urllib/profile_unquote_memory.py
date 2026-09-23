from __future__ import annotations

from _candidate import load_candidate


REPEAT_COUNT = 200_000
EXPECTED_LENGTH = REPEAT_COUNT * 6
TARGET = load_candidate().unquote_to_bytes


def prepare_workload() -> str:
    return "Ł%01š%20" * REPEAT_COUNT


def run_workload(prepared: str) -> bytes:
    return TARGET(prepared)


def validate_workload(result: bytes) -> dict[str, int]:
    if not isinstance(result, bytes):
        raise AssertionError(f"Expected bytes, got {type(result).__name__}")
    if len(result) != EXPECTED_LENGTH:
        raise AssertionError(f"Expected {EXPECTED_LENGTH} bytes, got {len(result)}")
    return {"repeat_count": REPEAT_COUNT, "output_bytes": len(result)}
