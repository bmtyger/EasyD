"""Plugin validation integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from ai_deploy.core.types import AppSpec
from ai_deploy.core.validation import validate_spec

log = logging.getLogger(__name__)


def validate_spec_issues(spec: AppSpec) -> List[str]:
    return list(validate_spec(spec))


def validate_deployment_package_issues(manifest: Path) -> List[str]:
    import json
    data = json.loads(manifest.read_text(encoding="utf-8"))
    issues: List[str] = []
    if not data.get("app_id"):
        issues.append("manifest missing app_id")
    if not data.get("status"):
        issues.append("manifest missing status")
    return issues
