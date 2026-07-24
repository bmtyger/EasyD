"""Security scanner agent v0."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ai_deploy.core.types import DeploymentPackage, SecurityFinding

log = logging.getLogger(__name__)


def scan(package: DeploymentPackage) -> DeploymentPackage:
    findings: list[SecurityFinding] = []

    for component in package.components:
        cfg = component.config or {}
        raw = json.dumps(cfg)

        # public ingress
        if re.search(r'"0\.0\.0\.0/0"', raw) or re.search(r"/0", raw):
            findings.append(
                SecurityFinding(
                    finding="Public network exposure detected in component",
                    severity="high",
                    action="Restrict source CIDR to known IP ranges",
                )
            )

        # IAM wildcard
        if '"Action": "*"' in raw or '"Action":["*"]' in raw:
            findings.append(
                SecurityFinding(
                    finding="Overprivileged IAM wildcard",
                    severity="high",
                    action="Scope IAM action to specific resources",
                )
            )

    package.security_findings = findings
    package.approved = not any(f.severity == "high" for f in findings)
    if not package.approved:
        log.warning("security scan blocked deploy: %s", [f.finding for f in findings])
    return package
