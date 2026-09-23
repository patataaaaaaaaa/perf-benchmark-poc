from __future__ import annotations

import ast
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MemoryHotspot:
    rank: int
    qualified_name: str
    file: str
    line: int
    function: str
    size_bytes: int
    allocation_count: int
    size_percent: float
    source_line: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _relative(path: Path, root: Path) -> Path | None:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return None


def _module_name(relative_file: Path) -> str:
    parts = list(relative_file.with_suffix("").parts)
    if parts and parts[0] in {"src", "Lib"}:
        parts.pop(0)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _function_at_line(path: Path, line: int) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError):
        return "<module>"
    matches: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end = getattr(node, "end_lineno", node.lineno)
        if node.lineno <= line <= end:
            matches.append((end - node.lineno, node.name))
    return min(matches)[1] if matches else "<module>"


def parse_tracemalloc_snapshot(
    snapshot_path: Path,
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
    """Convert a tracemalloc snapshot into repository-local allocation Top N."""

    if limit < 1:
        raise ValueError("limit must be at least 1")
    repository = repository.resolve()
    recorded_root = (recorded_repository or repository).resolve()
    snapshot = tracemalloc.Snapshot.load(str(snapshot_path))
    grouped: dict[tuple[str, int], dict[str, Any]] = {}

    for trace in snapshot.traces:
        selected: tuple[Path, int] | None = None
        for frame in reversed(trace.traceback):
            filename = Path(frame.filename)
            if not filename.is_absolute():
                filename = recorded_root / filename
            relative = _relative(filename, recorded_root)
            if relative is None:
                continue
            if any(part in excluded_path_parts for part in relative.parts):
                continue
            selected = (relative, int(frame.lineno))
            break
        if selected is None:
            continue
        relative, line = selected
        key = (relative.as_posix(), line)
        item = grouped.setdefault(
            key,
            {"file": relative, "line": line, "size_bytes": 0, "count": 0},
        )
        item["size_bytes"] += int(trace.size)
        item["count"] += 1

    total = sum(int(item["size_bytes"]) for item in grouped.values())
    ordered = sorted(
        grouped.values(),
        key=lambda item: (-int(item["size_bytes"]), -int(item["count"]), str(item["file"])),
    )
    hotspots: list[dict[str, Any]] = []
    for rank, item in enumerate(ordered[:limit], start=1):
        relative = item["file"]
        assert isinstance(relative, Path)
        line = int(item["line"])
        source_path = repository / relative
        function = _function_at_line(source_path, line)
        try:
            source_line = source_path.read_text(encoding="utf-8").splitlines()[line - 1].strip()
        except (OSError, UnicodeError, IndexError):
            source_line = ""
        module = _module_name(relative)
        qualified_name = ".".join(
            part for part in (module, function) if part and part != "<module>"
        ) or module
        hotspot = MemoryHotspot(
            rank=rank,
            qualified_name=qualified_name,
            file=relative.as_posix(),
            line=line,
            function=function,
            size_bytes=int(item["size_bytes"]),
            allocation_count=int(item["count"]),
            size_percent=(int(item["size_bytes"]) / total * 100 if total else 0.0),
            source_line=source_line,
        )
        hotspots.append(hotspot.to_dict())

    return {
        "profile_format": "tracemalloc_snapshot",
        "ranking_metric": "size_bytes",
        "total_project_allocation_bytes": total,
        "project_allocation_location_count": len(grouped),
        "hotspots": hotspots,
    }
