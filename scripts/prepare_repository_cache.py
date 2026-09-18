#!/usr/bin/env python3
"""Create an exact-content Git cache from downloaded source archives.

This is a fallback for environments where GitHub's Git endpoint is blocked but
the GitHub archive API is reachable. The experiment manifest still records the
official commit SHAs; the internal commits only make safe diff/rollback possible.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def extract(archive: Path, destination: Path) -> Path:
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        roots = {Path(member.name).parts[0] for member in members if member.name}
        if len(roots) != 1:
            raise ValueError(f"Expected one archive root, found: {sorted(roots)}")
        for member in members:
            resolved = (destination / member.name).resolve()
            if not resolved.is_relative_to(destination.resolve()):
                raise ValueError(f"Unsafe archive member: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(f"Archive links are not supported: {member.name}")
        bundle.extractall(destination)
    return destination / next(iter(roots))


def replace_worktree(repository: Path, source: Path) -> None:
    for child in repository.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in source.iterdir():
        destination = repository / child.name
        if child.is_dir() and not child.is_symlink():
            shutil.copytree(child, destination, symlinks=True)
        else:
            shutil.copy2(child, destination, follow_symlinks=False)


def commit_snapshot(repository: Path, message: str) -> str:
    git(repository, "add", "-A")
    git(
        repository,
        "-c",
        "user.name=Performance Framework",
        "-c",
        "user.email=framework@localhost",
        "commit",
        "-m",
        message,
    )
    return git(repository, "rev-parse", "HEAD")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-archive", type=Path, required=True)
    parser.add_argument("--human-archive", type=Path, required=True)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--human-ref", required=True)
    parser.add_argument(
        "--destination",
        type=Path,
        default=PROJECT_ROOT / ".cache" / "repositories" / "more_itertools_triplewise_889",
    )
    parser.add_argument(
        "--origin",
        default="https://github.com/more-itertools/more-itertools.git",
    )
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination == Path.home() or destination == Path("/"):
        raise ValueError("Refusing an unsafe cache destination")

    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        baseline = extract(args.baseline_archive, temporary_root / "baseline")
        human = extract(args.human_archive, temporary_root / "human")
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        git(destination, "init")
        git(destination, "remote", "add", "origin", args.origin)
        replace_worktree(destination, baseline)
        baseline_internal = commit_snapshot(destination, "baseline source snapshot")
        replace_worktree(destination, human)
        human_internal = commit_snapshot(destination, "human fix source snapshot")
        mapping = {
            args.baseline_ref: baseline_internal,
            args.human_ref: human_internal,
        }
        (destination / ".git" / "framework_refs.json").write_text(
            json.dumps(mapping, indent=2), encoding="utf-8"
        )
    print(f"Prepared repository cache: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
