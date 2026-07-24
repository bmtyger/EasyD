"""Architect agent."""

from __future__ import annotations

import logging
from typing import Any

from ai_deploy.core.types import AppSpec, ComponentConfig, DeploymentPackage

log = logging.getLogger(__name__)


def build(spec: AppSpec, target: str = "aws") -> DeploymentPackage:
    pkg = DeploymentPackage(provider=target)

    if target == "aws":
        pkg.components.append(ComponentConfig(type="vpc", config={"cidr": "10.0.0.0/16"}))
        pkg.components.append(ComponentConfig(type="iam", config={}))

        if spec.data_stores:
            ds = spec.data_stores[0]
            pkg.components.append(ComponentConfig(type="rds", config={"engine": ds["type"], "version": ds["version"]}))

        if spec.language != "unknown":
            if spec.framework in {"fastapi", "django", "express", "next.js"}:
                pkg.components.append(ComponentConfig(type="ecs", config={"port": spec.ports[0] if spec.ports else 8000}))
            else:
                pkg.components.append(ComponentConfig(type="ecs", config={"port": spec.ports[0] if spec.ports else 8000}))

        if spec.ports:
            pkg.components.append(ComponentConfig(type="cloudfront", config={"port": spec.ports[0]}))
            pkg.components.append(ComponentConfig(type="acm", config={"domain": "example.com"}))

        pkg.components.append(ComponentConfig(type="github_actions", config={"deploy_path": ".github/workflows/deploy.yml"}))
    else:
        pkg.components.append(ComponentConfig(type="vpc", config={"cidr": "10.0.0.0/16"}))

    pkg.cost_estimate = {"monthly_estimate_usd": 50.0, "components": len(pkg.components)}
    pkg.rollback_instructions = "Rollback to previous Terraform state and redeploy prior version."
    log.info("deployment package components=%s", [c.type for c in pkg.components])
    return pkg
