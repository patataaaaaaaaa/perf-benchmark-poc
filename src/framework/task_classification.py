from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Literal, Mapping


TaskType = Literal["cpu_bound", "memory", "io", "mixed", "unknown"]
Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class PerformanceSample:
    """One resource observation for a workload at a known input scale."""

    wall_seconds: float
    user_cpu_seconds: float
    system_cpu_seconds: float
    cpu_to_wall_ratio: float | None = None
    peak_rss_bytes: int | None = None
    tracemalloc_peak_bytes: int | None = None
    read_bytes: int | None = None
    write_bytes: int | None = None
    read_count: int | None = None
    write_count: int | None = None
    input_size: int | None = None
    label: str | None = None
    out_of_memory: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> PerformanceSample:
        """Load either a flat sample or an evaluator ResourceResult payload."""

        command = value.get("command")
        metrics: Mapping[str, Any] = value
        if isinstance(command, Mapping):
            nested = command.get("metrics")
            if isinstance(nested, Mapping):
                metrics = nested

        workload = value.get("workload")
        input_size = value.get("input_size")
        if input_size is None and isinstance(workload, Mapping):
            input_size = workload.get("input_size")

        def optional_int(name: str) -> int | None:
            raw = metrics.get(name)
            return int(raw) if raw is not None else None

        ratio = metrics.get("cpu_to_wall_ratio")
        peak = value.get("tracemalloc_peak_bytes")
        if peak is None:
            peak = metrics.get("tracemalloc_peak_bytes")
        return cls(
            wall_seconds=float(metrics.get("wall_seconds", 0.0)),
            user_cpu_seconds=float(metrics.get("user_cpu_seconds", 0.0)),
            system_cpu_seconds=float(metrics.get("system_cpu_seconds", 0.0)),
            cpu_to_wall_ratio=float(ratio) if ratio is not None else None,
            peak_rss_bytes=optional_int("peak_rss_bytes"),
            tracemalloc_peak_bytes=int(peak) if peak is not None else None,
            read_bytes=optional_int("read_bytes"),
            write_bytes=optional_int("write_bytes"),
            read_count=optional_int("read_count"),
            write_count=optional_int("write_count"),
            input_size=int(input_size) if input_size is not None else None,
            label=str(value["label"]) if value.get("label") is not None else None,
            out_of_memory=bool(value.get("out_of_memory", False)),
        )

    @property
    def effective_cpu_ratio(self) -> float | None:
        if self.cpu_to_wall_ratio is not None:
            return self.cpu_to_wall_ratio
        if self.wall_seconds <= 0:
            return None
        return (self.user_cpu_seconds + self.system_cpu_seconds) / self.wall_seconds

    @property
    def io_bytes(self) -> int | None:
        values = (self.read_bytes, self.write_bytes)
        if all(value is None for value in values):
            return None
        return sum(value or 0 for value in values)

    @property
    def io_operations(self) -> int | None:
        values = (self.read_count, self.write_count)
        if all(value is None for value in values):
            return None
        return sum(value or 0 for value in values)


@dataclass(frozen=True)
class ClassificationThresholds:
    cpu_ratio: float = 0.75
    io_max_cpu_ratio: float = 0.60
    io_bytes: int = 1 * 1024 * 1024
    io_operations: int = 100
    minimum_wall_seconds: float = 0.05
    minimum_scale_ratio: float = 2.0
    memory_growth_ratio: float = 1.5
    rss_growth_bytes: int = 16 * 1024 * 1024
    tracemalloc_growth_bytes: int = 8 * 1024 * 1024


@dataclass(frozen=True)
class ClassificationResult:
    task_type: TaskType
    confidence: Confidence
    evidence: tuple[str, ...]
    signals: dict[str, bool]
    sample_count: int
    median_cpu_to_wall_ratio: float | None
    declared_goal: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _median(values: Iterable[float | int | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    return statistics.median(present) if present else None


def _memory_growth(
    samples: tuple[PerformanceSample, ...], thresholds: ClassificationThresholds
) -> tuple[bool, list[str], bool]:
    if any(sample.out_of_memory for sample in samples):
        return True, ["workload 出现内存耗尽"], True

    scaled = sorted(
        (sample for sample in samples if sample.input_size is not None),
        key=lambda sample: sample.input_size or 0,
    )
    if len(scaled) < 2:
        return False, ["缺少不同输入规模，不能仅凭一次峰值判定内存瓶颈"], False

    smallest, largest = scaled[0], scaled[-1]
    assert smallest.input_size is not None
    assert largest.input_size is not None
    if smallest.input_size <= 0 or (
        largest.input_size / smallest.input_size < thresholds.minimum_scale_ratio
    ):
        return False, ["输入规模跨度不足，无法判断内存增长趋势"], False

    evidence: list[str] = []
    strong = False
    for label, first, last, minimum_growth in (
        (
            "RSS",
            smallest.peak_rss_bytes,
            largest.peak_rss_bytes,
            thresholds.rss_growth_bytes,
        ),
        (
            "tracemalloc",
            smallest.tracemalloc_peak_bytes,
            largest.tracemalloc_peak_bytes,
            thresholds.tracemalloc_growth_bytes,
        ),
    ):
        if first is None or last is None or first <= 0:
            continue
        growth = last - first
        ratio = last / first
        if growth >= minimum_growth and ratio >= thresholds.memory_growth_ratio:
            evidence.append(
                f"{label} 随输入规模增长 {ratio:.2f} 倍（增加 {growth} bytes）"
            )
            strong = strong or growth >= 4 * minimum_growth

    if evidence:
        return True, evidence, strong
    return False, ["未观察到足够强的随规模内存增长"], False


def _io_activity(
    samples: tuple[PerformanceSample, ...],
    *,
    median_io_bytes: float | None,
    median_io_operations: float | None,
    thresholds: ClassificationThresholds,
) -> tuple[bool, str | None]:
    if median_io_bytes is not None and median_io_bytes >= thresholds.io_bytes:
        return True, f"进程读写字节中位数为 {median_io_bytes:.0f} bytes"

    # Python startup performs a mostly fixed number of file lookups. When byte
    # counters are unavailable or zero, require operation counts to grow with
    # the workload scale instead of treating that fixed startup cost as I/O.
    scaled = sorted(
        (
            sample
            for sample in samples
            if sample.input_size is not None and sample.io_operations is not None
        ),
        key=lambda sample: sample.input_size or 0,
    )
    if median_io_operations is None or median_io_operations < thresholds.io_operations:
        return False, None
    if len(scaled) < 2:
        return False, None
    first_operations = scaled[0].io_operations or 0
    last_operations = scaled[-1].io_operations or 0
    # Imports and interpreter startup can vary by a few dozen metadata reads
    # between otherwise identical containers. Require a materially larger,
    # scale-correlated increase before treating operation counts alone as I/O.
    minimum_growth = max(40, int(first_operations * 0.25))
    if last_operations - first_operations >= minimum_growth:
        return (
            True,
            "I/O 操作次数随输入规模增长 "
            f"{last_operations - first_operations} 次",
        )
    return False, None


def classify_performance_task(
    samples: Iterable[PerformanceSample],
    *,
    declared_goal: str | None = None,
    thresholds: ClassificationThresholds | None = None,
) -> ClassificationResult:
    """Classify a workload conservatively using reproducible resource rules.

    `confidence` describes rule-evidence strength; it is not a probability.
    The user's declared goal is retained as context but never overrides metrics.
    """

    observations = tuple(samples)
    if not observations:
        raise ValueError("At least one performance sample is required")
    limits = thresholds or ClassificationThresholds()

    cpu_ratios = [sample.effective_cpu_ratio for sample in observations]
    median_cpu = _median(cpu_ratios)
    median_wall = _median(sample.wall_seconds for sample in observations) or 0.0
    median_io_bytes = _median(sample.io_bytes for sample in observations)
    median_io_ops = _median(sample.io_operations for sample in observations)

    cpu_signal = bool(
        median_cpu is not None
        and median_cpu >= limits.cpu_ratio
        and median_wall >= limits.minimum_wall_seconds
    )
    io_amount_signal, io_evidence = _io_activity(
        observations,
        median_io_bytes=median_io_bytes,
        median_io_operations=median_io_ops,
        thresholds=limits,
    )
    io_signal = bool(
        io_amount_signal
        and median_cpu is not None
        and median_cpu <= limits.io_max_cpu_ratio
    )
    memory_signal, memory_evidence, memory_strong = _memory_growth(
        observations, limits
    )

    evidence: list[str] = []
    if cpu_signal:
        assert median_cpu is not None
        evidence.append(
            f"CPU time / wall time 中位数为 {median_cpu:.2f}，达到 CPU 型阈值"
        )
    elif median_cpu is None:
        evidence.append("缺少 CPU time / wall time 指标")
    else:
        evidence.append(
            f"CPU time / wall time 中位数为 {median_cpu:.2f}，未达到 CPU 型阈值"
        )

    if io_signal:
        detail = f"（{io_evidence}）" if io_evidence else ""
        evidence.append(f"检测到随 workload 变化的 I/O{detail}，且 CPU 比例较低")
    elif median_io_bytes is None and median_io_ops is None:
        evidence.append("当前平台没有提供进程 I/O 计数")

    if memory_signal:
        evidence.extend(memory_evidence)

    signals = {
        "cpu_bound": cpu_signal,
        "memory": memory_signal,
        "io": io_signal,
    }
    matched = [name for name, present in signals.items() if present]

    if len(matched) > 1:
        task_type: TaskType = "mixed"
        confidence: Confidence = "high" if memory_strong else "medium"
        evidence.append("同时存在多个瓶颈信号，不能只走单一分析路线")
    elif len(matched) == 1:
        task_type = matched[0]  # type: ignore[assignment]
        if task_type == "cpu_bound" and median_cpu is not None:
            confidence = "high" if median_cpu >= 0.90 else "medium"
        elif task_type == "memory":
            confidence = "high" if memory_strong else "medium"
        elif task_type == "io":
            strong_io = bool(
                median_io_bytes is not None
                and median_io_bytes >= 16 * limits.io_bytes
                and median_cpu is not None
                and median_cpu <= 0.40
            )
            confidence = "high" if strong_io else "medium"
        else:
            confidence = "medium"
    else:
        task_type = "unknown"
        confidence = "low"
        evidence.append("现有证据不足，保留为 unknown，不强制猜测")

    if declared_goal:
        evidence.append(f"用户声明的优化目标为 {declared_goal}；该信息未覆盖测量证据")

    return ClassificationResult(
        task_type=task_type,
        confidence=confidence,
        evidence=tuple(evidence),
        signals=signals,
        sample_count=len(observations),
        median_cpu_to_wall_ratio=median_cpu,
        declared_goal=declared_goal,
    )
