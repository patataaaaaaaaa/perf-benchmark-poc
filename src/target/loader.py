from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TargetSpec:
    id: str
    module: str
    target: str
    description: str
    qualified_name: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class TargetContext:
    spec: TargetSpec
    source_code: str
    source_file: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.spec.to_dict(),
            "source_file": self.source_file,
            "source_code": self.source_code,
        }


def load_targets(path: Path) -> list[TargetSpec]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Target file must contain a JSON list: {path}")

    targets: list[TargetSpec] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("Each target entry must be a JSON object")
        required = {"id", "module", "target", "description"}
        missing = required - item.keys()
        if missing:
            raise ValueError(f"Target entry is missing fields: {sorted(missing)}")
        qualified_name = item.get(
            "qualified_name", f"{item['module']}.{item['target']}"
        )
        targets.append(
            TargetSpec(
                id=str(item["id"]),
                module=str(item["module"]),
                target=str(item["target"]),
                description=str(item["description"]),
                qualified_name=str(qualified_name),
            )
        )
    return targets


def _resolve_object(spec: TargetSpec) -> Any:
    module = importlib.import_module(spec.module)

    if spec.qualified_name.startswith(f"{spec.module}."):
        remaining = spec.qualified_name[len(spec.module) + 1 :]
    else:
        remaining = spec.target

    obj: Any = module
    try:
        for part in remaining.split("."):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        if hasattr(module, spec.target):
            return getattr(module, spec.target)
        raise AttributeError(
            f"Cannot resolve {spec.qualified_name!r} from module {spec.module!r}"
        )


def collect_target_context(spec: TargetSpec) -> TargetContext:
    obj = _resolve_object(spec)
    try:
        source_code = inspect.getsource(obj)
    except (OSError, TypeError):
        source_code = (
            f"# inspect.getsource() was unavailable for {spec.qualified_name}.\n"
            f"# Signature: {inspect.signature(obj)}\n"
            f"# Docstring:\n{inspect.getdoc(obj) or '(none)'}\n"
        )

    try:
        source_file = inspect.getsourcefile(obj) or inspect.getfile(obj)
    except (OSError, TypeError):
        source_file = None

    return TargetContext(
        spec=spec,
        source_code=source_code,
        source_file=source_file,
    )

