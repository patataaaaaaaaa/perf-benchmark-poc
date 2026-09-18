from __future__ import annotations

import ast
import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


DIFF_FENCE = re.compile(r"```(?:diff|patch)?\s*\n(.*?)```", re.I | re.S)
HUNK_HEADER = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$"
)


def extract_unified_diff(response: str) -> str:
    match = DIFF_FENCE.search(response)
    patch = (match.group(1) if match else response).strip()
    if not patch or not (
        patch.startswith("diff --git ")
        or (patch.startswith("--- ") and "\n+++ " in patch)
    ):
        raise ValueError("Patch Generator did not return a unified diff")
    return patch + "\n"


def patch_paths(patch: str) -> set[Path]:
    paths: set[Path] = set()
    for line in patch.splitlines():
        if not line.startswith("diff --git "):
            continue
        parts = line.split()
        if len(parts) != 4 or not parts[2].startswith("a/") or not parts[3].startswith("b/"):
            raise ValueError(f"Unsupported diff header: {line}")
        old = Path(parts[2][2:])
        new = Path(parts[3][2:])
        if old != new:
            raise ValueError("Renames are not allowed")
        paths.add(new)
    if not paths:
        for line in patch.splitlines():
            if line.startswith("+++ b/"):
                paths.add(Path(line[6:]))
    if not paths:
        raise ValueError("Patch does not identify a changed file")
    for path in paths:
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe patch path: {path}")
    return paths


def canonicalize_hunk_locations(
    repository: Path,
    patch: str,
    editable_files: tuple[Path, ...] | None = None,
) -> str:
    """Recompute hunk locations from exact old-source context.

    Models often emit a semantically correct hunk with line numbers copied from
    a shortened prompt. This changes only hunk metadata; every context, removed,
    and added line remains byte-for-byte the model's proposal.
    """

    paths = patch_paths(patch)
    if editable_files is not None:
        unexpected = paths - set(editable_files)
        if unexpected:
            raise ValueError(
                "Patch changes non-editable files: "
                + ", ".join(sorted(str(path) for path in unexpected))
            )
    lines = patch.splitlines()
    result: list[str] = []
    current_path: Path | None = None
    index = 0
    cumulative_delta: dict[Path, int] = {}
    while index < len(lines):
        line = lines[index]
        if line.startswith("+++ b/"):
            current_path = Path(line[6:])
            result.append(line)
            index += 1
            continue
        match = HUNK_HEADER.match(line)
        if match is None:
            result.append(line)
            index += 1
            continue
        if current_path is None:
            raise ValueError("Hunk appeared before a target file header")

        hunk: list[str] = []
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            if HUNK_HEADER.match(candidate) or candidate.startswith("diff --git "):
                break
            if candidate.startswith("--- ") and hunk:
                break
            hunk.append(candidate)
            cursor += 1

        old_lines = [
            value[1:]
            for value in hunk
            if value.startswith((" ", "-")) and value != "\\ No newline at end of file"
        ]
        if not old_lines:
            raise ValueError("New-file and context-free patches are not allowed")
        source_lines = (repository / current_path).read_text(encoding="utf-8").splitlines()
        matches = [
            position
            for position in range(0, len(source_lines) - len(old_lines) + 1)
            if source_lines[position : position + len(old_lines)] == old_lines
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Unable to locate a unique old-source hunk in {current_path}; "
                f"found {len(matches)} matches"
            )
        old_start = matches[0] + 1
        old_count = sum(value.startswith((" ", "-")) for value in hunk)
        new_count = sum(value.startswith((" ", "+")) for value in hunk)
        delta = cumulative_delta.get(current_path, 0)
        new_start = old_start + delta
        suffix = match.group(5)
        result.append(
            f"@@ -{old_start},{old_count} +{new_start},{new_count} @@{suffix}"
        )
        result.extend(hunk)
        cumulative_delta[current_path] = delta + new_count - old_count
        index = cursor
    return "\n".join(result) + "\n"


def apply_safe_patch(
    repository: Path, patch: str, editable_files: tuple[Path, ...]
) -> set[Path]:
    paths = patch_paths(patch)
    allowed = set(editable_files)
    unexpected = paths - allowed
    if unexpected:
        raise ValueError(
            "Patch changes non-editable files: "
            + ", ".join(sorted(str(path) for path in unexpected))
        )
    patch = canonicalize_hunk_locations(repository, patch, editable_files)
    check = subprocess.run(
        [
            "git",
            "apply",
            "--check",
            "--unidiff-zero",
            "--whitespace=error",
            "-",
        ],
        cwd=repository,
        input=patch,
        text=True,
        capture_output=True,
        check=False,
    )
    if check.returncode != 0:
        raise ValueError(f"git apply --check failed: {check.stderr.strip()}")
    applied = subprocess.run(
        ["git", "apply", "--unidiff-zero", "--whitespace=error", "-"],
        cwd=repository,
        input=patch,
        text=True,
        capture_output=True,
        check=False,
    )
    if applied.returncode != 0:
        raise ValueError(f"git apply failed: {applied.stderr.strip()}")
    changed = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    )
    changed_paths = {Path(value) for value in changed.stdout.splitlines() if value}
    if not changed_paths or changed_paths - allowed:
        raise ValueError("Applied changes escaped the editable file allowlist")
    return changed_paths


def repository_diff(repository: Path) -> str:
    result = subprocess.run(
        ["git", "diff", "--binary", "--no-ext-diff"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout


def restore_patch(repository: Path, patch: str) -> None:
    subprocess.run(
        ["git", "reset", "--hard", "HEAD"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    )
    if patch:
        subprocess.run(
            ["git", "apply", "-"],
            cwd=repository,
            input=patch,
            text=True,
            capture_output=True,
            check=True,
        )


def file_hashes(repository: Path, paths: tuple[Path, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in paths:
        path = repository / relative
        result[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def assert_hashes_unchanged(
    repository: Path, expected: dict[str, str]
) -> None:
    actual = file_hashes(repository, tuple(Path(path) for path in expected))
    if actual != expected:
        changed = sorted(path for path in expected if expected[path] != actual.get(path))
        raise ValueError("Protected files changed: " + ", ".join(changed))


def extract_symbol_context(source: str, qualified_symbol: str) -> str:
    tree = ast.parse(source)
    symbol = qualified_symbol.rsplit(".", 1)[-1]
    imports = [
        ast.get_source_segment(source, node)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    target = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == symbol
        ),
        None,
    )
    if target is None:
        raise ValueError(f"Unable to find target function {qualified_symbol}")
    function_source = ast.get_source_segment(source, target)
    return "\n".join(value for value in [*imports, function_source] if value)


def extract_matching_context(source: str, needle: str, radius: int = 12) -> str:
    lines = source.splitlines()
    selected: set[int] = set()
    for index, line in enumerate(lines):
        if needle in line:
            selected.update(range(max(0, index - radius), min(len(lines), index + radius + 1)))
    if not selected:
        return ""
    chunks: list[str] = []
    previous: int | None = None
    for index in sorted(selected):
        if previous is not None and index != previous + 1:
            chunks.append("# ...")
        chunks.append(lines[index])
        previous = index
    return "\n".join(chunks)


@dataclass(frozen=True)
class PatchStats:
    files_changed: int
    lines_added: int
    lines_deleted: int

    def to_dict(self) -> dict[str, int]:
        return {
            "files_changed": self.files_changed,
            "lines_added": self.lines_added,
            "lines_deleted": self.lines_deleted,
        }


def patch_stats(patch: str) -> PatchStats:
    additions = 0
    deletions = 0
    for line in patch.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return PatchStats(len(patch_paths(patch)), additions, deletions)
