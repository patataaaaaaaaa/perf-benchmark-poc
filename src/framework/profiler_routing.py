from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProfilerSelection:
    name: str
    evidence_type: str
    implementation_status: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ProfilerRoute:
    task_type: str
    selected_profilers: tuple[ProfilerSelection, ...]
    reason: str
    mode: str = "observe_only"
    selection_applied: bool = True
    execution_applied: bool = False
    optimization_decision_impact: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["selected_profilers"] = [
            profiler.to_dict() for profiler in self.selected_profilers
        ]
        return payload


PROFILERS = {
    "cpu_bound": ProfilerSelection(
        name="cprofile",
        evidence_type="python_function_time_top_n",
        implementation_status="ready",
    ),
    "memory": ProfilerSelection(
        name="tracemalloc",
        evidence_type="python_allocation_top_n",
        implementation_status="ready_parser",
    ),
    "io": ProfilerSelection(
        name="process_io",
        evidence_type="process_read_write_totals",
        implementation_status="aggregate_only",
    ),
}


def select_profiler_route(classification: Mapping[str, Any]) -> ProfilerRoute:
    """Build a deterministic, observation-only profiler selection plan."""

    task_type = str(classification.get("task_type", "unknown"))
    raw_signals = classification.get("signals")
    signals = raw_signals if isinstance(raw_signals, Mapping) else {}

    selected_keys: list[str]
    if task_type == "mixed":
        selected_keys = [
            key
            for key in ("cpu_bound", "memory", "io")
            if bool(signals.get(key))
        ]
    elif task_type in PROFILERS:
        selected_keys = [task_type]
    else:
        selected_keys = []

    selected = tuple(PROFILERS[key] for key in selected_keys)
    if selected:
        names = ", ".join(item.name for item in selected)
        reason = f"分类为 {task_type}，选择 {names} 收集对应热点证据"
    else:
        reason = "分类证据不足，暂不自动选择专项 profiler"
    return ProfilerRoute(
        task_type=task_type,
        selected_profilers=selected,
        reason=reason,
        selection_applied=bool(selected),
    )


def route_from_task_classification(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Route a pipeline task_classification.json payload without executing tools."""

    classification = payload.get("classification")
    if not isinstance(classification, Mapping):
        return {
            "status": "UNAVAILABLE",
            "mode": "observe_only",
            "selection_applied": False,
            "execution_applied": False,
            "optimization_decision_impact": False,
            "selected_profilers": [],
            "reason": "没有可用的性能分类结果",
        }
    result = select_profiler_route(classification).to_dict()
    result["status"] = "COMPLETE"
    return result


def require_objective_profiler(
    route: Mapping[str, Any], optimization_objective: str
) -> dict[str, Any]:
    """Ensure an explicit experiment objective has the evidence it requires.

    The measured classification remains unchanged.  This only adds the profiler
    required to explain an explicitly configured objective; it does not turn the
    profiler report itself into an acceptance metric.
    """

    result = dict(route)
    selected = [
        dict(item)
        for item in route.get("selected_profilers", [])
        if isinstance(item, Mapping)
    ]
    required = PROFILERS["memory"] if optimization_objective == "memory" else None
    if required is None:
        return result

    already_selected = any(item.get("name") == required.name for item in selected)
    if not already_selected:
        selected.append(required.to_dict())
        previous_reason = str(result.get("reason", "")).strip()
        addition = (
            "显式内存优化目标要求补充 tracemalloc 分配热点证据"
        )
        result["reason"] = (
            f"{previous_reason}；{addition}" if previous_reason else addition
        )
    result["selected_profilers"] = selected
    result["selection_applied"] = True
    result["status"] = "COMPLETE"
    result["objective_requirement"] = {
        "objective": optimization_objective,
        "profiler": required.name,
        "source": "explicit_experiment_objective",
        "already_selected_by_classification": already_selected,
    }
    return result


def select_target_profiler(
    classification: Mapping[str, Any],
    available_reports: Mapping[str, Any],
    *,
    optimization_objective: str,
) -> tuple[str, str]:
    """Choose the routed report used to select the source target.

    The configured objective only resolves a genuinely measured mixed signal;
    it cannot manufacture a memory or CPU signal that classification did not
    observe.
    """

    task_type = str(classification.get("task_type", "unknown"))
    raw_signals = classification.get("signals")
    signals = raw_signals if isinstance(raw_signals, Mapping) else {}

    if (
        optimization_objective == "memory"
        and bool(signals.get("memory"))
        and "tracemalloc" in available_reports
    ):
        return (
            "tracemalloc",
            "测量确认存在内存信号；混合任务按本次内存优化目标使用分配热点选目标",
        )
    if task_type == "memory" and "tracemalloc" in available_reports:
        return "tracemalloc", "任务分类为内存型，使用分配热点选目标"
    if bool(signals.get("cpu_bound")) and "cprofile" in available_reports:
        return "cprofile", "测量确认存在 CPU 信号，使用函数自身耗时热点选目标"
    if bool(signals.get("memory")) and "tracemalloc" in available_reports:
        return "tracemalloc", "测量确认存在内存信号，使用分配热点选目标"
    if task_type == "io":
        raise ValueError(
            "I/O classification currently has only process totals and cannot "
            "select a source function"
        )
    raise ValueError(
        "Classification did not produce a location-aware profiler report "
        "that can select a target"
    )
