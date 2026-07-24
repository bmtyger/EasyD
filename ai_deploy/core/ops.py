"""Continuous ops summary writer."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ai_deploy.core.types import AppSpec, DeploymentPackage, DeployState

log = logging.getLogger(__name__)


def write_summary(
    dest: Path,
    *,
    spec: AppSpec,
    package: DeploymentPackage,
    state: DeployState,
    actual_cost_usd: Optional[float] = None,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)

    estimate = float((package.cost_estimate or {}).get("monthly_estimate_usd") or 0)
    variance = None
    if actual_cost_usd is not None and estimate > 0:
        variance = actual_cost_usd - estimate

    payload: dict[str, Any] = {
        "app_id": spec.app_id,
        "environment": state.environment,
        "status": state.status,
        "provider": package.provider,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z"),
        "cost": {
            "estimate_usd": estimate,
            "actual_usd": actual_cost_usd,
            "variance_usd": variance,
            "alert": bool(variance is not None and abs(variance / estimate) > 0.2),
        },
        "security_findings_count": len(package.security_findings),
        "security_approved": package.approved,
        "deployed_by": state.deployed_by,
        "tracking_ref": state.tracking_ref,
    }

    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log.info("wrote ops summary=%s", dest)
    return dest
