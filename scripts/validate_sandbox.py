#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.framework.sandbox import SandboxLimits, SandboxResult, run_in_docker  # noqa: E402


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _run(
    run_dir: Path,
    name: str,
    command: list[str],
    limits: SandboxLimits,
) -> SandboxResult:
    case_dir = run_dir / name
    workspace = case_dir / "workspace"
    output = case_dir / "output"
    workspace.mkdir(parents=True)
    result = run_in_docker(
        image="python:3.11-slim",
        workspace=workspace,
        harness=PROJECT_ROOT / "subjects" / "sandbox_checks",
        output=output,
        inner_command=command,
        limits=limits,
    )
    _write_json(case_dir / "result.json", result.to_dict())
    (case_dir / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (case_dir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    return result


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = PROJECT_ROOT / "artifacts" / "sandbox_validation" / stamp
    run_dir.mkdir(parents=True)

    print("[Sandbox] verify non-root, no secrets, read-only workspace and no network")
    restrictions = _run(
        run_dir,
        "restrictions",
        ["python", "/harness/check_restrictions.py"],
        SandboxLimits(memory="128m", timeout_seconds=30),
    )
    restrictions_passed = restrictions.return_code == 0 and not restrictions.timed_out

    print("[Sandbox] verify host timeout removes a sleeping container")
    timeout = _run(
        run_dir,
        "timeout",
        ["python", "-c", "import time; time.sleep(30)"],
        SandboxLimits(memory="128m", timeout_seconds=1),
    )
    timeout_passed = timeout.timed_out and timeout.return_code == 124

    print("[Sandbox] verify memory limit terminates an allocating process")
    memory = _run(
        run_dir,
        "memory",
        ["python", "/harness/exhaust_memory.py"],
        SandboxLimits(memory="64m", timeout_seconds=20),
    )
    memory_passed = not memory.timed_out and memory.return_code != 0

    summary = {
        "image": "python:3.11-slim",
        "passed": restrictions_passed and timeout_passed and memory_passed,
        "checks": {
            "restrictions": {
                "passed": restrictions_passed,
                "return_code": restrictions.return_code,
                "stdout": restrictions.stdout.strip(),
            },
            "timeout": {
                "passed": timeout_passed,
                "return_code": timeout.return_code,
                "timed_out": timeout.timed_out,
            },
            "memory": {
                "passed": memory_passed,
                "return_code": memory.return_code,
                "timed_out": memory.timed_out,
                "stderr": memory.stderr.strip(),
            },
        },
    }
    _write_json(run_dir / "summary.json", summary)
    lines = [
        "# 基础沙箱负向验证",
        "",
        "| 检查项 | 结果 |",
        "|---|---|",
        f"| 非 root、密钥隔离、仓库只读、禁止网络 | {'通过' if restrictions_passed else '失败'} |",
        f"| 超时后终止并删除容器 | {'通过' if timeout_passed else '失败'} |",
        f"| 超过内存限制后进程失败 | {'通过' if memory_passed else '失败'} |",
        "",
        "详细原始结果见同目录下的 `summary.json` 和各检查子目录。",
    ]
    (run_dir / "REPORT_ZH.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[Complete] passed={summary['passed']} artifacts={run_dir}")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
