"""Cost guardrail agent."""

from __future__ import annotations

import logging
from typing import Any

from ai_deploy.core.types import AppSpec, DeploymentPackage

log = logging.getLogger(__name__)


def validate(spec: AppSpec, package: DeploymentPackage) -> DeploymentPackage:
    estimate = float((package.cost_estimate or {}).get("monthly_estimate_usd") or 0)
    if spec.budget_cap_usd > 0 and estimate > spec.budget_cap_usd:
        package.approved = False
        package.rollback_instructions = (
            f"Cost estimate {estimate:.2f} exceeds budget cap {spec.budget_cap_usd:.2f}. "
            "Resize or remove components before deploying."
        )
        log.warning("budget cap exceeded: estimate=%f cap=%f", estimate, spec.budget_cap_usd)
    else:
        package.approved = True
    return package
