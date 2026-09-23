from __future__ import annotations

import ast
import pstats
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Hotspot:
    rank: int
    qualified_name: str
    file: str
    line: int
    function: str
    primitive_calls: int
    total_calls: int
    self_time_seconds: float
    cumulative_time_seconds: float
    self_time_percent: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def module_name_from_path(relative_file: Path) -> str:
    module_parts = list(relative_file.with_suffix("").parts)
    # Repositories using a source-root directory import ``src/pkg/x.py`` or
    # CPython's ``Lib/urllib/x.py`` without that physical root in the public
    # module name.
    if module_parts and module_parts[0] in {"src", "Lib"}:
        module_parts.pop(0)
    if module_parts[-1] == "__init__":
        module_parts.pop()
    return ".".join(module_parts)


def _definition_qualname(source_path: Path, line: int, function: str) -> str:
    """Recover the enclosing class omitted by cProfile function names."""

    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError):
        return function
    matches: list[tuple[bool, tuple[str, ...]]] = []

    def visit(nodes: list[ast.stmt], classes: tuple[str, ...]) -> None:
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                visit(node.body, (*classes, node.name))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function:
                    start = min(
                        [node.lineno]
                        + [decorator.lineno for decorator in node.decorator_list]
                    )
                    end = int(getattr(node, "end_lineno", node.lineno))
                    matches.append((start <= line <= end, (*classes, node.name)))
                nested_classes = [
                    child for child in node.body if isinstance(child, ast.ClassDef)
                ]
                visit(nested_classes, classes)

    visit(tree.body, ())
    if not matches:
        return function
    matches.sort(key=lambda item: (not item[0], -len(item[1])))
    return ".".join(matches[0][1])


def _qualified_name(
    relative_file: Path,
    function: str,
    *,
    source_path: Path,
    line: int,
) -> str:
    module = module_name_from_path(relative_file)
    definition = _definition_qualname(source_path, line, function)
    return ".".join(value for value in (module, definition) if value)


def parse_cprofile(
    profile_path: Path,
    repository: Path,
    *,
    limit: int = 5,
    recorded_repository: Path | None = None,
    excluded_path_parts: tuple[str, ...] = (
        "tests",
        "test",
        "benchmarks",
        "benchmark",
    ),
) -> dict[str, Any]:
    """Return the hottest project functions from a cProfile data file.

    Ranking is deterministic and based on self time. Cumulative time is retained
    so a later agent can distinguish expensive functions from expensive callers.
    Only Python functions whose source file is inside ``repository`` are kept.
    """

    if limit < 1:
        raise ValueError("limit must be at least 1")
    repository = repository.resolve()
    recorded_root = (recorded_repository or repository).resolve()
    stats = pstats.Stats(str(profile_path))
    total_self_time = float(stats.total_tt)
    candidates: list[dict[str, Any]] = []

    for (filename, line, function), values in stats.stats.items():
        primitive_calls, total_calls, self_time, cumulative_time, _callers = values
        # cProfile uses pseudo filenames such as ``<built-in>`` and
        # ``<frozen importlib._bootstrap>``. They are runtime internals, not
        # files from the checked-out repository.
        if filename.startswith("<"):
            continue
        recorded_path = Path(filename)
        if not recorded_path.is_absolute():
            recorded_path = recorded_root / recorded_path
        recorded_path = recorded_path.resolve()
        if not _is_relative_to(recorded_path, recorded_root):
            continue
        relative_file = recorded_path.relative_to(recorded_root)
        if any(part in excluded_path_parts for part in relative_file.parts):
            continue
        if function.startswith("<"):
            continue
        candidates.append(
            {
                "qualified_name": _qualified_name(
                    relative_file,
                    function,
                    source_path=repository / relative_file,
                    line=int(line),
                ),
                "file": relative_file.as_posix(),
                "line": int(line),
                "function": function,
                "primitive_calls": int(primitive_calls),
                "total_calls": int(total_calls),
                "self_time_seconds": float(self_time),
                "cumulative_time_seconds": float(cumulative_time),
                "self_time_percent": (
                    float(self_time) / total_self_time * 100
                    if total_self_time > 0
                    else 0.0
                ),
            }
        )

    candidates.sort(
        key=lambda item: (
            -item["self_time_seconds"],
            -item["cumulative_time_seconds"],
            item["qualified_name"],
        )
    )
    hotspots = [
        Hotspot(rank=index, **item).to_dict()
        for index, item in enumerate(candidates[:limit], start=1)
    ]
    return {
        "profile_format": "cProfile",
        "ranking_metric": "self_time_seconds",
        "total_profiled_self_time_seconds": total_self_time,
        "project_function_count": len(candidates),
        "hotspots": hotspots,
    }


def contains_symbol(report: dict[str, Any], qualified_name: str) -> bool:
    return any(
        item.get("qualified_name") == qualified_name
        for item in report.get("hotspots", [])
    )


def select_top_hotspot(
    report: dict[str, Any], *, expected_symbol: str | None = None
) -> tuple[Path, str]:
    hotspots = report.get("hotspots") or []
    if not hotspots:
        raise ValueError("Profiler did not find any project-local hotspots")
    selected = hotspots[0]
    relative_file = Path(str(selected["file"]))
    if relative_file.is_absolute() or ".." in relative_file.parts:
        raise ValueError(f"Unsafe hotspot source path: {relative_file}")
    symbol = str(selected["qualified_name"])
    if expected_symbol and symbol != expected_symbol:
        raise ValueError(
            f"Top hotspot was {symbol!r}, expected {expected_symbol!r}"
        )
    return relative_file, symbol
