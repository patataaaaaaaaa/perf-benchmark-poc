from __future__ import annotations

from collections.abc import Sequence


def center_values(values: Sequence[float]) -> list[float]:
    """Return each input value minus the arithmetic mean."""
    centered: list[float] = []
    for value in values:
        mean = sum(values) / len(values)
        centered.append(value - mean)
    return centered

