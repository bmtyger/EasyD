"""Repo-local state persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ai_deploy.core.types import AppSpec, ComponentConfig, DeploymentPackage, DeployState, SecurityFinding

log = logging.getLogger(__name__)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def save_state(state: DeployState, dest: Path) -> None:
    write_json(dest, state.__dict__)


def load_state(dest: Path) -> DeployState | None:
    data = read_json(dest)
    if not data:
        return None
    return DeployState(**data)


def save_package(package: DeploymentPackage, dest: Path) -> None:
    components = []
    for component in package.components:
        components.append({"type": component.type, "config": component.config})

    payload = {
        "provider": package.provider,
        "components": components,
        "security_findings": [f.__dict__ for f in package.security_findings],
        "cost_estimate": package.cost_estimate,
        "approved": package.approved,
        "rollback_instructions": package.rollback_instructions,
    }
    write_json(dest, payload)


def load_package(dest: Path) -> DeploymentPackage | None:
    data = read_json(dest)
    if not data:
        return None
    components = [ComponentConfig(**c) for c in data.get("components", [])]
    findings = [SecurityFinding(**s) for s in data.get("security_findings", [])]
    pkg = DeploymentPackage(
        provider=data.get("provider", "aws"),
        components=components,
        security_findings=findings,
        cost_estimate=data.get("cost_estimate", {}),
        approved=data.get("approved", False),
        rollback_instructions=data.get("rollback_instructions", ""),
    )
    return pkg



