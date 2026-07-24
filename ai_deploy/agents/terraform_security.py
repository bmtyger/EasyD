"""Terraform-aware security scanner."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from ai_deploy.core.types import DeploymentPackage, SecurityFinding

log = logging.getLogger(__name__)


def scan(terraform_dir: Path, package: DeploymentPackage) -> DeploymentPackage:
    findings: list[SecurityFinding] = []
    main = terraform_dir / "main.tf"
    if not main.exists():
        return package

    text = main.read_text(encoding="utf-8", errors="ignore")

    # public ingress candidate
    if re.search(r"cidr_blocks\s*=\s*\[[^\]]*0\.0\.0\.0/0[^\]]*\]", text) and re.search(r"ingress\s*\{", text):
        findings.append(
            SecurityFinding(
                finding="Ingress rule contains public CIDR 0.0.0.0/0 in Terraform",
                severity="high",
                action="Restrict source CIDR to known IP ranges",
            )
        )

    # unencrypted storage candidates
    if re.search(r'resource\s+"aws_s3_bucket"', text):
        findings.append(
            SecurityFinding(
                finding="S3 bucket without explicit server-side encryption block detected",
                severity="medium",
                action="Add server_side_encryption_configuration block",
            )
        )

    # missing encryption on EBS blocks
    if re.search(r'resource\s+"aws_ebs_volume"', text):
        findings.append(
            SecurityFinding(
                finding="EBS volume without explicit encryption/block_public_access policy",
                severity="medium",
                action="Enable encryption and public access exclusion",
            )
        )

    # IAM wildcard Action
    if re.search(r"\"Action\"\\s*:\\s*\"\\*\"", text) or re.search(r"'Action'\\s*:\\s*'\\*'", text):
        findings.append(
            SecurityFinding(
                finding="IAM policy uses wildcard Action in Terraform",
                severity="high",
                action="Scope actions to specific resources",
            )
        )

    # overly permissive SG from_port=0 to_port=65535 with 0.0.0.0/0-like egress
    if re.search(r"ingress\\s*\\{[^}]*from_port\\s*=\\s*0", text) and "0.0.0.0/0" in text:
        findings.append(
            SecurityFinding(
                finding="Ingress allows full port range from public CIDR",
                severity="high",
                action="Limit ports and source CIDRs",
            )
        )

    # egress everywhere
    if re.search(r"egress\\s*\\{[^}]*protocol\\s*=\\s*\"-1\"", text) and "0.0.0.0/0" in text:
        findings.append(
            SecurityFinding(
                finding="Egress allows unrestricted outbound traffic",
                severity="low",
                action="Limit egress to required destinations",
            )
        )

    package.security_findings.extend(findings)
    package.approved = not any(f.severity == "high" for f in package.security_findings)
    if not package.approved:
        log.warning("terraform scan blocked deploy: %s", [f.finding for f in findings if f.severity == "high"])
    return package


try:
    import re as _re
except Exception:
    pass
