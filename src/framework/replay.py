from __future__ import annotations

import json
from pathlib import Path

from src.framework.config import FrameworkConfig
from src.framework.generated_benchmark import sha256_file
from src.framework.patching import apply_safe_patch
from src.framework.repository import RepositoryManager


def reconstruct_frozen_workspaces(
    *,
    artifact_dir: Path,
    config: FrameworkConfig,
    destination: Path,
    run_number: int,
) -> dict[str, Path]:
    """Rebuild baseline, human and accepted candidate from immutable evidence."""

    manifest = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))
    release_dir = artifact_dir / "release_candidate"
    patch_path = release_dir / "best.patch"
    release_manifest = release_dir / "manifest.json"
    if not patch_path.is_file():
        patch_path = artifact_dir / f"run_{run_number:02d}" / "final" / "best.patch"
    if not patch_path.is_file():
        raise FileNotFoundError("Unable to find the accepted best.patch")
    if release_manifest.is_file():
        release = json.loads(release_manifest.read_text(encoding="utf-8"))
        if sha256_file(patch_path) != release.get("patch_sha256"):
            raise RuntimeError("Release candidate patch hash mismatch during replay")

    target = manifest.get("target_discovery") or {}
    selection = target.get("selection") or {}
    target_file_value = selection.get("target_file") or manifest["config"].get(
        "target_file"
    )
    if not target_file_value:
        raise ValueError("Experiment manifest does not identify target_file")
    target_file = Path(str(target_file_value))

    manager = RepositoryManager(config)
    workspaces = {
        "baseline": destination / "baseline",
        "human_fix": destination / "human_fix",
        "deepseek_fix": destination / "deepseek_fix",
    }
    manager.checkout(workspaces["baseline"], config.baseline_commit)
    if config.human_fix_commit is None:
        raise ValueError("Replay requires human_fix_commit")
    manager.checkout(workspaces["human_fix"], config.human_fix_commit)
    manager.checkout(workspaces["deepseek_fix"], config.baseline_commit)
    patch = patch_path.read_text(encoding="utf-8")
    if patch.strip():
        apply_safe_patch(workspaces["deepseek_fix"], patch, (target_file,))
    return workspaces
