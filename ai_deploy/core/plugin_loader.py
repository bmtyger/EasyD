"""Plugin manifest validation, loader, and registry."""

from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_deploy.core.types import AppSpec, DeploymentPackage


log = logging.getLogger(__name__)


class PluginManifest:
    def __init__(self, path: Path) -> None:
        self.path = path
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        self.name: str = data["name"]
        self.version: str = data.get("version", "0.0.0")
        self.interfaces: list[str] = data.get("interface", []) or []


def load_plugins(root: Path) -> list[PluginManifest]:
    manifests: list[PluginManifest] = []
    for path in root.glob("*/plugin.json"):
        if path.is_file():
            try:
                manifests.append(PluginManifest(path))
            except Exception as exc:
                log.warning("skip invalid manifest %s: %s", path, exc)
    return manifests


class PluginRegistry:
    def __init__(self, plugins_root: Path) -> None:
        self.root = plugins_root
        self.manifests = load_plugins(plugins_root)
        self.logger = log

    def emitters(self, provider: str) -> list[PluginManifest]:
        return [m for m in self.manifests if "emit" in m.interfaces]

    def scanners(self) -> list[PluginManifest]:
        return [m for m in self.manifests if "scan" in m.interfaces]

    def notifiers(self) -> list[PluginManifest]:
        return [m for m in self.manifests if "notify" in m.interfaces]

    def detectors(self) -> list[PluginManifest]:
        return [m for m in self.manifests if "detect" in m.interfaces]

    def call_emit(self, plugin: PluginManifest, package: DeploymentPackage, dest: Path) -> None:
        mod = _load_plugin_module(plugin, "emitter.py")
        emit = getattr(mod, "emit", None)
        if not callable(emit):
            raise RuntimeError(f"Plugin {plugin.path.parent} missing emit(package, dest)")
        emit(package, dest)

    def call_scan(self, plugin: PluginManifest, package: DeploymentPackage) -> DeploymentPackage:
        mod = _load_plugin_module(plugin, "scanner.py")
        scan = getattr(mod, "scan", None)
        if not callable(scan):
            raise RuntimeError(f"Plugin {plugin.path.parent} missing scan(package)")
        return scan(package)

    def call_notify(self, plugin: PluginManifest, event: str, payload: dict[str, Any]) -> None:
        mod = _load_plugin_module(plugin, "notifier.py")
        publish = getattr(mod, "publish", None)
        if not callable(publish):
            raise RuntimeError(f"Plugin {plugin.path.parent} missing publish(event, payload)")
        publish(event, payload)

    def call_detect(self, plugin: PluginManifest, repo: Path) -> AppSpec:
        mod = _load_plugin_module(plugin, "detector.py")
        detect = getattr(mod, "detect", None)
        if not callable(detect):
            raise RuntimeError(f"Plugin {plugin.path.parent} missing detect(repo)")
        return detect(repo)


def _load_plugin_module(plugin: PluginManifest, filename: str):
    target = plugin.path.parent / filename
    if not target.exists():
        raise FileNotFoundError(f"Plugin file missing: {target}")

    spec = importlib.util.spec_from_file_location("plugin_module", target)
    if spec is None or spec.origin is None or spec.loader is None:
        raise RuntimeError(f"Cannot load plugin module from {target}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["plugin_module"] = mod
    spec.loader.exec_module(mod)
    return mod
