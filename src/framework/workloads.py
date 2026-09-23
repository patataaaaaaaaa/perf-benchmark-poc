from __future__ import annotations

import ast
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


IGNORED_PARTS = {
    ".git",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "site-packages",
}


@dataclass(frozen=True)
class WorkloadCandidate:
    candidate_id: str
    source: str
    path: str
    command: tuple[str, ...] | None
    confidence: str
    directly_runnable: bool
    requires_adaptation: bool
    reason: str
    signals: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["command"] = list(self.command) if self.command else None
        return value


@dataclass(frozen=True)
class TestScenario:
    scenario_id: str
    source_path: str
    source_symbol: str
    source_code: str
    called_names: tuple[str, ...]
    assertion_count: int
    source: str = "existing_test"
    referenced_names: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["called_names"] = list(self.called_names)
        value["referenced_names"] = list(self.referenced_names)
        return value


@dataclass(frozen=True)
class WorkloadSpec:
    workload_id: str
    source: str
    source_path: str
    source_symbol: str
    script_path: str
    command: tuple[str, ...]
    target_symbol: str
    input_description: str
    expected_behavior: str
    confidence: str
    adaptation_type: str
    fidelity_status: str
    llm_adapted: bool
    automatic_validation_passed: bool
    human_confirmed: bool
    experiment_locked: bool
    frozen: bool
    script_sha256: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["command"] = list(self.command)
        return value


def workload_script_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class FidelityAssessment:
    adaptation_type: str
    fidelity_status: str
    source_constructors: tuple[str, ...]
    missing_in_generated: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_constructors"] = list(self.source_constructors)
        value["missing_in_generated"] = list(self.missing_in_generated)
        return value


def assess_workload_fidelity(
    source_scenario: str, generated_workload: str
) -> FidelityAssessment:
    """Conservative v0 check for model-introduced input-structure drift.

    User-defined constructor names in the repository scenario must remain
    visible in the generated workload. This does not prove semantic equality;
    it only identifies clear structural substitutions that require review.
    """

    source_tree = ast.parse(source_scenario)
    generated_tree = ast.parse(generated_workload)
    constructors = sorted(
        {
            name
            for node in ast.walk(source_tree)
            if isinstance(node, ast.Call)
            and (name := _called_name(node)) is not None
            and name.rsplit(".", 1)[-1][:1].isupper()
        }
    )
    generated_names = {
        node.id for node in ast.walk(generated_tree) if isinstance(node, ast.Name)
    }
    missing = tuple(
        name
        for name in constructors
        if name.rsplit(".", 1)[-1] not in generated_names
    )
    if missing:
        return FidelityAssessment(
            adaptation_type="structure_changed",
            fidelity_status="REVIEW_REQUIRED",
            source_constructors=tuple(constructors),
            missing_in_generated=missing,
        )
    return FidelityAssessment(
        adaptation_type="scale_only",
        fidelity_status="PASS",
        source_constructors=tuple(constructors),
        missing_in_generated=(),
    )


def _expression_name(value: ast.expr) -> str | None:
    parts: list[str] = []
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, ast.Name):
        parts.append(value.id)
        return ".".join(reversed(parts))
    return None


def _called_name(node: ast.Call) -> str | None:
    return _expression_name(node.func)


def _is_test_function(node: ast.AST) -> bool:
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
        "test"
    )


def _is_test_class(node: ast.ClassDef) -> bool:
    return node.name.startswith("Test") or node.name.endswith("Tests") or any(
        (isinstance(base, ast.Attribute) and base.attr == "TestCase")
        or (isinstance(base, ast.Name) and base.id == "TestCase")
        for base in node.bases
    )


def extract_test_scenarios(
    repository: Path,
    relative_path: Path,
    query: str | None,
    *,
    source_kind: str = "existing_test",
    scenario_symbol: str | None = None,
) -> list[TestScenario]:
    """Extract repository-owned test blocks that call the queried API.

    This is evidence extraction only: the returned source has not yet been
    scaled, executed as a workload, or judged representative by a person.
    """

    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("relative_path must stay inside the repository")
    source_path = repository / relative_path
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(relative_path))
    query_tail = query.rsplit(".", 1)[-1] if query else None
    scenarios: list[TestScenario] = []

    for node in tree.body:
        candidate: ast.AST | None = None
        symbol: str | None = None
        if isinstance(node, ast.ClassDef) and _is_test_class(node):
            test_methods = [child for child in node.body if _is_test_function(child)]
            if test_methods:
                candidate = node
                symbol = node.name
        elif _is_test_function(node):
            candidate = node
            symbol = node.name
        if candidate is None or symbol is None:
            continue
        if scenario_symbol is not None and symbol != scenario_symbol:
            continue

        calls = sorted(
            {
                name
                for child in ast.walk(candidate)
                if isinstance(child, ast.Call)
                and (name := _called_name(child)) is not None
            }
        )
        references = sorted(
            {
                name
                for child in ast.walk(candidate)
                if isinstance(child, ast.Attribute)
                and (name := _expression_name(child)) is not None
            }
        )
        evidence_names = {*calls, *references}
        if query is not None:
            assert query_tail is not None
            if not any(
                name == query or name.rsplit(".", 1)[-1] == query_tail
                for name in evidence_names
            ):
                continue
        assertions = sum(
            isinstance(child, ast.Assert)
            or (
                isinstance(child, ast.Call)
                and (name := _called_name(child)) is not None
                and name.rsplit(".", 1)[-1].startswith("assert")
            )
            for child in ast.walk(candidate)
        )
        segment = ast.get_source_segment(source, candidate)
        if not segment:
            continue
        scenarios.append(
            TestScenario(
                scenario_id=f"{source_kind}:{relative_path.as_posix()}::{symbol}",
                source_path=relative_path.as_posix(),
                source_symbol=symbol,
                source_code=segment,
                called_names=tuple(calls),
                assertion_count=int(assertions),
                source=source_kind,
                referenced_names=tuple(references),
            )
        )
    return scenarios


def _has_main_guard(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare) or len(test.ops) != 1:
            continue
        if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
            continue
        if not isinstance(test.ops[0], ast.Eq) or len(test.comparators) != 1:
            continue
        comparator = test.comparators[0]
        if isinstance(comparator, ast.Constant) and comparator.value == "__main__":
            return True
    return False


def _imports(tree: ast.AST) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".", 1)[0])
    return result


def _source_type(relative: Path) -> str | None:
    lowered_parts = tuple(part.lower() for part in relative.parts)
    name = relative.name.lower()
    if any(part in {"benchmark", "benchmarks", "bench"} for part in lowered_parts):
        return "existing_benchmark"
    if name.startswith(("bench_", "benchmark_")) or "benchmark" in name:
        return "existing_benchmark"
    if any(part in {"test", "tests"} for part in lowered_parts) or name.startswith(
        "test_"
    ):
        return "existing_test"
    if any(part in {"example", "examples"} for part in lowered_parts) or name.startswith(
        "example_"
    ):
        return "example"
    return None


def _module_name(relative: Path) -> str | None:
    parts = list(relative.with_suffix("").parts)
    if not all(part.isidentifier() for part in parts):
        return None
    return ".".join(parts)


def _candidate(repository: Path, path: Path, source: str) -> WorkloadCandidate | None:
    relative = path.relative_to(repository)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
    except (OSError, UnicodeError, SyntaxError):
        return None
    imports = _imports(tree)
    has_main = _has_main_guard(tree)
    test_functions = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
        for node in ast.walk(tree)
    )
    test_classes = sum(
        isinstance(node, ast.ClassDef)
        and (
            node.name.startswith("Test")
            or any(
                (isinstance(base, ast.Attribute) and base.attr == "TestCase")
                or (isinstance(base, ast.Name) and base.id == "TestCase")
                for base in node.bases
            )
        )
        for node in ast.walk(tree)
    )

    command: tuple[str, ...] | None = None
    directly_runnable = False
    requires_adaptation = True
    confidence = "low"
    reason = "Repository example that may demonstrate a meaningful entry path."
    if source == "existing_benchmark":
        confidence = "medium"
        reason = "Repository-owned benchmark; execution and representativeness still require validation."
        if has_main:
            command = ("{python}", relative.as_posix())
            directly_runnable = True
            requires_adaptation = False
    elif source == "existing_test":
        if test_functions == 0 and test_classes == 0:
            return None
        confidence = "medium"
        reason = "Repository-owned correctness test; usually needs scale and timing adaptation."
        if "pytest" in imports:
            command = ("{python}", "-m", "pytest", relative.as_posix())
            directly_runnable = True
        else:
            module = _module_name(relative)
            if module:
                command = ("{python}", "-m", "unittest", module)
                directly_runnable = True
    elif source == "example" and has_main:
        command = ("{python}", relative.as_posix())
        directly_runnable = True

    candidate_id = source + ":" + relative.as_posix()
    return WorkloadCandidate(
        candidate_id=candidate_id,
        source=source,
        path=relative.as_posix(),
        command=command,
        confidence=confidence,
        directly_runnable=directly_runnable,
        requires_adaptation=requires_adaptation,
        reason=reason,
        signals={
            "has_main_guard": has_main,
            "imports": sorted(imports),
            "test_function_count": int(test_functions),
            "test_class_count": int(test_classes),
        },
    )


def discover_workload_candidates(
    repository: Path, *, limit: int = 100
) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    repository = repository.resolve()
    candidates: list[WorkloadCandidate] = []
    for path in sorted(repository.rglob("*.py")):
        relative = path.relative_to(repository)
        if any(part in IGNORED_PARTS or part.startswith(".") for part in relative.parts):
            continue
        source = _source_type(relative)
        if source is None:
            continue
        candidate = _candidate(repository, path, source)
        if candidate is not None:
            candidates.append(candidate)

    priority = {"existing_benchmark": 0, "existing_test": 1, "example": 2}
    candidates.sort(
        key=lambda item: (
            priority[item.source],
            not item.directly_runnable,
            item.path,
        )
    )
    selected = candidates[:limit]
    counts = {
        source: sum(item.source == source for item in candidates)
        for source in ("existing_benchmark", "existing_test", "example")
    }
    return {
        "schema_version": 1,
        "repository": str(repository),
        "candidate_count": len(candidates),
        "returned_count": len(selected),
        "counts_by_source": counts,
        "selection_note": (
            "These are repository-evidenced candidates, not yet validated or frozen workloads."
        ),
        "candidates": [candidate.to_dict() for candidate in selected],
    }
