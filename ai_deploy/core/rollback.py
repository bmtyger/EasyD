"""Rollback manifest writer."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Optional

from ai_deploy.core.types import DeployState, DeploymentPackage

log = logging.getLogger(__name__)


def write_manifest(
    dest: Path,
    *,
    package: DeploymentPackage,
    state: DeployState,
    terraform_dir: Optional[Path] = None,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "app_id": state.app_id,
        "environment": state.environment,
        "status": state.status,
        "provider": package.provider,
        "rollback_instructions": package.rollback_instructions,
        "artifacts": state.artifacts,
        "terraform_dir": str(terraform_dir) if terraform_dir else None,
        "last_deployed_at": state.last_deployed_at,
        "deployed_by": state.deployed_by,
        "tracking_ref": state.tracking_ref,
    }

    # preserve previous manifest before overwrite
    if dest.exists():
        backup = dest.with_suffix(".prev.json")
        try:
            shutil.copy2(dest, backup)
        except Exception:
            backup = None
        payload["previous_manifest"] = str(backup) if backup else None

    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log.info("wrote rollback manifest=%s", dest)
    return dest


def restore_previous(manifest: Path, output_dir: Path) -> Path:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    prev = data.get("previous_manifest")
    out = output_dir / "rollback-restore.json"

    if not prev:
        log.warning("No previous manifest recorded; writing empty restore artifact")
        out.write_text(json.dumps({"restored": False, "reason": "no_previous_manifest"}, indent=2) + "\n", encoding="utf-8")
        return out

    prev_path = Path(prev)
    if not prev_path.exists():
        log.warning("Previous manifest missing: %s; writing empty restore artifact", prev_path)
        out.write_text(json.dumps({"restored": False, "reason": "previous_manifest_missing", "path": str(prev_path)}, indent=2) + "\n", encoding="utf-8")
        return out

    restored = json.loads(prev_path.read_text(encoding="utf-8"))
    out.write_text(json.dumps(restored, indent=2) + "\n", encoding="utf-8")
    log.info("restored previous manifest -> %s", out)
    return out
