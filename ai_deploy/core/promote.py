"""Environment promotion workflow."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ai_deploy.core.types import AppSpec, DeploymentPackage, DeployState

log = logging.getLogger(__name__)


def promote(
    package: DeploymentPackage,
    state: DeployState,
    target_env: str,
    *,
    rollback_manifest: Optional[Path] = None,
) -> tuple[DeployState, Optional[Path]]:
    if target_env not in {"staging", "prod"}:
        raise ValueError("target_env must be staging or prod")

    if state.environment == target_env:
        log.info("already in target environment=%s", target_env)
        return state, rollback_manifest

    previous_env = state.environment
    state.environment = target_env
    state.status = "pending"
    state.tracking_ref = state.tracking_ref or ""

    log.info("promote %s -> %s", previous_env, target_env)
    manifest = rollback_manifest
    return state, manifest
