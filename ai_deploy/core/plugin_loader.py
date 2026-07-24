"""Plugin manifest validation and loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PluginManifest:
    def __init__(self, path: Path) -> None:
        self.path = path
        data: dict[str, Any] = json.loads(path.read_text())
        self.name: str = data["name"]
        self.version: str = data.get("version", "0.0.0")
        self.interfaces: list[str] = data.get("interface", [])


def load_plugins(root: Path) -> list[PluginManifest]:
    manifests: list[PluginManifest] = []
    for path in root.glob("*/plugin.json"):
        if path.is_file():
            manifests.append(PluginManifest(path))
    return manifests
