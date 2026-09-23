#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "1bb68ba6d9de6bb7f00aee11d135123163f15887"
HUMAN_FIX_COMMIT = "2e279e85fece187b6058718ac7e82d1692461e26"
BASELINE_SHA256 = "a7e6c9d8184d286dc5f4c0888bb6aeafab30590317fbac56bcb55960d686cfce"
HUMAN_FIX_SHA256 = "1002a50162a3d4e5660962db52dc36bc70c8bc347eb2fe9c6897e975f7c2912e"


SITE_CUSTOMIZE = '''from __future__ import annotations

import sys
from pathlib import Path


candidate_lib = Path(__file__).resolve().parent / "Lib"
if str(candidate_lib) not in sys.path:
    sys.path.insert(0, str(candidate_lib))
'''


TEST_INIT = '"""Controlled behavioral tests for the urllib memory task."""\n'
URLLIB_INIT = '"""Pinned urllib package for the controlled performance task."""\n'


BEHAVIOR_TESTS = '''from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "Lib"))
for module_name in ("urllib.parse", "urllib"):
    sys.modules.pop(module_name, None)

from urllib.parse import unquote, unquote_to_bytes  # noqa: E402


class UnquoteToBytesTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(unquote_to_bytes(""), b"")
        self.assertEqual(unquote_to_bytes(b""), b"")

    def test_str_and_bytes(self) -> None:
        self.assertEqual(unquote_to_bytes("abc%20def"), b"abc def")
        self.assertEqual(unquote_to_bytes(b"abc%2Fdef"), b"abc/def")

    def test_non_ascii_and_invalid_escapes(self) -> None:
        self.assertEqual(unquote_to_bytes("Ł%20"), "Ł ".encode())
        self.assertEqual(unquote_to_bytes("%zz%"), b"%zz%")
        self.assertEqual(unquote_to_bytes("%01"), b"\\x01")

    def test_large_repeated_input(self) -> None:
        text = "Ł%01š%20" * 2_000
        result = unquote_to_bytes(text)
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 12_000)
        self.assertEqual(result[:6], "Ł\\x01š ".encode())

    def test_dynamic_target_hit_and_source(self) -> None:
        hit = False
        target_code = unquote_to_bytes.__code__

        def profiler(frame, event, arg):  # type: ignore[no-untyped-def]
            nonlocal hit
            if event == "call" and frame.f_code is target_code:
                hit = True
            return profiler

        sys.setprofile(profiler)
        try:
            self.assertEqual(unquote_to_bytes("a%20b"), b"a b")
        finally:
            sys.setprofile(None)
        self.assertTrue(hit)
        source = Path(inspect.getsourcefile(unquote_to_bytes) or "").resolve()
        self.assertTrue(source.is_relative_to(REPOSITORY), source)


class UnquoteCompatibilityTests(unittest.TestCase):
    def test_unquote_behavior_is_preserved(self) -> None:
        self.assertEqual(unquote("abc%20def"), "abc def")
        self.assertEqual(unquote("Ł%20š"), "Ł š")
        self.assertEqual(unquote("%zz"), "%zz")


if __name__ == "__main__":
    unittest.main()
'''


README = '''# Controlled CPython urllib task slice

This local Git repository contains the exact `Lib/urllib/parse.py` files from
two pinned upstream CPython commits plus controlled behavioral tests. It exists
only to make the offline performance experiment reproducible. The official
commit IDs are mapped to the two local commits in `.git/framework_refs.json`.
'''


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repository, text=True, capture_output=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def read_checked(path: Path, expected_sha256: str) -> bytes:
    payload = path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != expected_sha256:
        raise RuntimeError(
            f"Unexpected source hash for {path}: {actual}; expected {expected_sha256}"
        )
    compile(payload, str(path), "exec")
    return payload


def write_file(path: Path, payload: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_text(payload, encoding="utf-8")


def verify_existing(repository: Path) -> bool:
    mapping_path = repository / ".git" / "framework_refs.json"
    if not mapping_path.is_file():
        return False
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    expected = {BASELINE_COMMIT, HUMAN_FIX_COMMIT}
    if not expected.issubset(mapping):
        return False
    checks = (
        (mapping[BASELINE_COMMIT], BASELINE_SHA256),
        (mapping[HUMAN_FIX_COMMIT], HUMAN_FIX_SHA256),
    )
    for local_commit, expected_hash in checks:
        result = subprocess.run(
            ["git", "show", f"{local_commit}:Lib/urllib/parse.py"],
            cwd=repository,
            capture_output=True,
        )
        if result.returncode != 0 or sha256_bytes(result.stdout) != expected_hash:
            return False
        package = subprocess.run(
            ["git", "cat-file", "-e", f"{local_commit}:Lib/urllib/__init__.py"],
            cwd=repository,
            capture_output=True,
        )
        if package.returncode != 0:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the offline two-commit repository for the urllib memory task."
    )
    parser.add_argument(
        "--baseline-source",
        type=Path,
        default=PROJECT_ROOT
        / ".cache"
        / "task_inputs"
        / "cpython_urllib"
        / "baseline_parse.py",
    )
    parser.add_argument(
        "--human-source",
        type=Path,
        default=PROJECT_ROOT
        / ".cache"
        / "task_inputs"
        / "cpython_urllib"
        / "human_fix_parse.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / ".cache" / "task_repositories" / "cpython_urllib",
    )
    args = parser.parse_args()

    if args.output.exists():
        if verify_existing(args.output):
            print(f"Repository already prepared: {args.output}")
            return 0
        raise RuntimeError(
            f"Refusing to replace an existing unverified directory: {args.output}"
        )

    baseline = read_checked(args.baseline_source, BASELINE_SHA256)
    human = read_checked(args.human_source, HUMAN_FIX_SHA256)
    args.output.mkdir(parents=True)
    git(args.output, "init")
    git(args.output, "config", "user.name", "Performance Framework")
    git(args.output, "config", "user.email", "framework@localhost")

    write_file(args.output / "Lib" / "urllib" / "parse.py", baseline)
    write_file(args.output / "Lib" / "urllib" / "__init__.py", URLLIB_INIT)
    write_file(args.output / "sitecustomize.py", SITE_CUSTOMIZE)
    write_file(args.output / "task_tests" / "__init__.py", TEST_INIT)
    write_file(args.output / "task_tests" / "test_parse.py", BEHAVIOR_TESTS)
    write_file(args.output / "README.md", README)
    git(args.output, "add", "-A")
    git(args.output, "commit", "-m", "Pinned CPython urllib baseline task slice")
    baseline_local = git(args.output, "rev-parse", "HEAD")

    write_file(args.output / "Lib" / "urllib" / "parse.py", human)
    git(args.output, "add", "Lib/urllib/parse.py")
    git(args.output, "commit", "-m", "Apply pinned upstream urllib human fix")
    human_local = git(args.output, "rev-parse", "HEAD")

    mapping = {BASELINE_COMMIT: baseline_local, HUMAN_FIX_COMMIT: human_local}
    write_file(
        args.output / ".git" / "framework_refs.json",
        json.dumps(mapping, indent=2, sort_keys=True) + "\n",
    )
    write_file(
        args.output / ".git" / "source_manifest.json",
        json.dumps(
            {
                "upstream_repository": "https://github.com/python/cpython.git",
                "upstream_path": "Lib/urllib/parse.py",
                "baseline_commit": BASELINE_COMMIT,
                "human_fix_commit": HUMAN_FIX_COMMIT,
                "baseline_sha256": BASELINE_SHA256,
                "human_fix_sha256": HUMAN_FIX_SHA256,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    print(f"Prepared: {args.output}")
    print(f"Baseline local commit: {baseline_local}")
    print(f"Human-fix local commit: {human_local}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
