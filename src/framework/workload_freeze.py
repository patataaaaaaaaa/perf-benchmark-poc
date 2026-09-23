from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.framework.generated_benchmark import sha256_file


def _safe_artifact_path(root: Path, value: object) -> Path:
    relative = Path(str(value))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Workload script_path must stay inside the artifact directory")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Workload script_path escaped the artifact directory")
    return path


def freeze_workload_candidate(
    *,
    artifact_dir: Path,
    spec_path: Path,
    confirmed_sha256: str,
    reviewer: str,
    rationale: str,
) -> Path:
    """Create an immutable review artifact after explicit human confirmation.

    The candidate record is preserved. A separate frozen copy is created so
    later experiments can distinguish automated validation from human review.
    """

    artifact_dir = artifact_dir.resolve()
    spec_path = spec_path.resolve()
    if not spec_path.is_relative_to(artifact_dir):
        raise ValueError("spec_path must be inside artifact_dir")
    reviewer = reviewer.strip()
    rationale = rationale.strip()
    if not reviewer:
        raise ValueError("reviewer must not be empty")
    if not rationale:
        raise ValueError("rationale must not be empty")

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if not spec.get("automatic_validation_passed"):
        raise RuntimeError("Candidate did not pass automatic validation")
    if not spec.get("experiment_locked"):
        raise RuntimeError("Candidate was not hash-locked during its experiment")
    if spec.get("fidelity_status") != "PASS":
        raise RuntimeError("Candidate workload fidelity requires review or was rejected")
    if spec.get("human_confirmed") or spec.get("frozen"):
        raise RuntimeError("Candidate is already marked confirmed or frozen")

    script = _safe_artifact_path(artifact_dir, spec.get("script_path"))
    if not script.is_file():
        raise FileNotFoundError(f"Candidate workload script is missing: {script}")
    recorded_hash = str(spec.get("script_sha256", ""))
    actual_hash = sha256_file(script)
    if actual_hash != recorded_hash:
        raise RuntimeError("Candidate workload script no longer matches WorkloadSpec")
    if confirmed_sha256.strip() != actual_hash:
        raise RuntimeError("Explicitly confirmed SHA-256 does not match the candidate")

    frozen_dir = artifact_dir / "frozen_workload"
    if frozen_dir.exists():
        raise FileExistsError(f"Frozen workload already exists: {frozen_dir}")
    frozen_dir.mkdir()
    frozen_script = frozen_dir / "workload.py"
    shutil.copy2(script, frozen_script)

    frozen_spec: dict[str, Any] = dict(spec)
    frozen_spec.update(
        {
            "script_path": "frozen_workload/workload.py",
            "human_confirmed": True,
            "frozen": True,
            "script_sha256": actual_hash,
        }
    )
    confirmation = {
        "schema_version": 1,
        "status": "FROZEN",
        "reviewer": reviewer,
        "rationale": rationale,
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
        "source_spec": str(spec_path.relative_to(artifact_dir)),
        "source_script": str(script.relative_to(artifact_dir)),
        "confirmed_sha256": actual_hash,
        "automatic_validation_passed": True,
        "human_confirmed": True,
    }
    (frozen_dir / "workload_spec.json").write_text(
        json.dumps(frozen_spec, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (frozen_dir / "confirmation.json").write_text(
        json.dumps(confirmation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return frozen_dir
