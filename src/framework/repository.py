from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from src.framework.config import FrameworkConfig


def _git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


class RepositoryManager:
    def __init__(self, config: FrameworkConfig) -> None:
        self.config = config

    @staticmethod
    def _ref_map(repository: Path) -> dict[str, str]:
        path = repository / ".git" / "framework_refs.json"
        if not path.is_file():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {str(key): str(value) for key, value in payload.items()}

    def prepare(self) -> Path:
        if self.config.repository is not None:
            return self.config.repository

        assert self.config.repository_url is not None
        cache = self.config.repository_cache / self.config.task_id
        if not (cache / ".git").is_dir():
            cache.parent.mkdir(parents=True, exist_ok=True)
            _git(["clone", "--no-checkout", self.config.repository_url, str(cache)])
        elif _git(["remote", "get-url", "origin"], cache) != self.config.repository_url:
            raise RuntimeError(f"Repository cache has the wrong origin: {cache}")

        refs = [self.config.baseline_commit, self.config.human_fix_commit]
        mapped = self._ref_map(cache)
        for ref in (value for value in refs if value):
            if ref in mapped:
                continue
            exists = subprocess.run(
                ["git", "cat-file", "-e", f"{ref}^{{commit}}"],
                cwd=cache,
                capture_output=True,
                check=False,
            )
            if exists.returncode != 0:
                _git(["fetch", "--depth", "1", "origin", ref], cache)
        return cache

    def resolve(self, repository: Path, ref: str | None) -> str:
        if ref is None:
            return _git(["rev-parse", "HEAD"], repository)
        if ref in self._ref_map(repository):
            return ref
        return _git(["rev-parse", f"{ref}^{{commit}}"], repository)

    def checkout(self, destination: Path, ref: str | None) -> str:
        source = self.prepare()
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if (source / ".git").is_dir():
            _git(["clone", "--shared", "--no-checkout", str(source), str(destination)])
            resolved = self.resolve(source, ref)
            internal_ref = self._ref_map(source).get(ref or "", resolved)
            _git(["checkout", "--detach", internal_ref], destination)
            return resolved

        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
        )
        _git(["init"], destination)
        _git(["add", "-A"], destination)
        _git(
            [
                "-c",
                "user.name=Performance Framework",
                "-c",
                "user.email=framework@localhost",
                "commit",
                "-m",
                "baseline snapshot",
            ],
            destination,
        )
        return self.resolve(destination, None)
