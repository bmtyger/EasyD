"""Azure plugin scaffold."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ai_deploy.core.types import DeploymentPackage

log = logging.getLogger(__name__)


def emit(package: DeploymentPackage, dest: Path) -> None:  # pragma: no cover - scaffold
    dest.mkdir(parents=True, exist_ok=True)
    header = """\
resource "azurerm_resource_group" "rg" {
  name     = var.rg_name
  location = var.location
}
"""
    out = Path(dest) / "main.tf"
    out.write_text(header, encoding="utf-8")
    log.info("azure scaffold emitted -> %s", out)
