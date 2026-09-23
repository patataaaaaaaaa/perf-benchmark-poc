from __future__ import annotations

from memory_target import allocate_cache


EXPECTED_ENTRIES = 64
ENTRY_BYTES = 256 * 1024


def prepare_workload() -> tuple[int, int]:
    return EXPECTED_ENTRIES, ENTRY_BYTES


def run_workload(prepared: tuple[int, int]) -> list[bytearray]:
    entries, entry_bytes = prepared
    return allocate_cache(entries, entry_bytes)


def validate_workload(result: list[bytearray]) -> dict[str, int]:
    if len(result) != EXPECTED_ENTRIES:
        raise AssertionError(f"Expected {EXPECTED_ENTRIES} entries, got {len(result)}")
    if any(len(item) != ENTRY_BYTES for item in result):
        raise AssertionError("An allocated cache entry has the wrong size")
    return {"entries": len(result), "bytes": sum(map(len, result))}
