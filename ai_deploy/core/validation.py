"""Strict AppSpec validation."""

from __future__ import annotations

import logging
import re
from typing import Optional

from ai_deploy.core.types import AppSpec

log = logging.getLogger(__name__)


def validate_spec(spec: AppSpec) -> list[str]:
    issues: list[str] = []

    if not spec.app_id or not re.match(r"^[A-Za-z0-9_-]+$", spec.app_id):
        issues.append("app_id must be non-empty and alphanumeric/underscore/hyphen only")

    if spec.budget_cap_usd < 0:
        issues.append("budget_cap_usd must be >= 0")

    for port in spec.ports:
        if not (0 < port < 65536):
            issues.append(f"port {port} is out of valid range")
            break

    for store in spec.data_stores:
        if "type" not in store:
            issues.append("data_stores entries require a 'type'")
            break

    return issues


def enforce_spec(spec: AppSpec) -> AppSpec:
    issues = validate_spec(spec)
    if issues:
        raise ValueError(f"Invalid AppSpec: {issues}")
    return spec
