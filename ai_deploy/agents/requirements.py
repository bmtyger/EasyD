"""Requirement analyzer agent."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from ai_deploy.core.types import AppSpec

log = logging.getLogger(__name__)


def _read_first(path: Path, limit: int = 200) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text[:limit]
    except Exception:
        return ""


def analyze(path: Path) -> AppSpec:
    log.info("analyzing path=%s", path)

    language = "unknown"
    framework = "unknown"
    detected_stack = "unknown"
    ports: list[int] = []
    env_vars: list[str] = []
    data_stores: list[dict] = []

    # Collect lightweight view of repo
    all_files = sorted([str(p).lower() for p in path.rglob("*") if p.is_file()])
    file_names = {p.name.lower() for p in path.rglob("*") if p.is_file()}
    root_files = {p.name.lower() for p in path.iterdir() if p.is_file()}

    # Language detection
    if "go.mod" in file_names:
        language = "go"
    elif "pom.xml" in file_names or "build.gradle" in file_names or "build.gradle.kts" in file_names:
        language = "java"
    elif "requirements.txt" in file_names or "pyproject.toml" in file_names or "setup.py" in file_names:
        language = "python"
    elif "package.json" in file_names:
        language = "javascript"

    # Framework detection
    if "manage.py" in file_names or "settings.py" in file_names:
        framework = "django"
    elif "app.py" in file_names or "main.py" in file_names:
        if language == "python":
            framework = "fastapi"
    elif "package.json" in file_names:
        pkg_text = _read_first(path / "package.json")
        if "express" in pkg_text:
            framework = "express"
        elif "next" in pkg_text:
            framework = "next.js"
        elif "react" in pkg_text:
            framework = "react"

    # Container presence
    if "dockerfile" in file_names or "docker-compose.yml" in file_names or "docker-compose.yaml" in file_names:
        detected_stack = "containerized"
    else:
        detected_stack = language if language != "unknown" else "unknown"

    # Port and env hints from Dockerfile/package.json/README
    docker_text = ""
    for candidate in ["dockerfile", "Dockerfile"]:
        if candidate in file_names:
            docker_text = _read_first(path / candidate)
            break

    exposed = re.findall(r"EXPOSE\s+(\d+)", docker_text, flags=re.IGNORECASE)
    ports = [int(p) for p in exposed]

    if not ports:
        if framework == "django":
            ports = [8000]
        elif framework == "fastapi":
            ports = [8000]
        elif framework == "express":
            ports = [3000]
        elif framework == "next.js":
            ports = [3000]

    # Env vars from common config files
    env_candidates: list[str] = []
    for rel in ["config.py", "settings.py", ".env.example", "package.json", "docker-compose.yml"]:
        p = path / rel
        if p.exists():
            env_candidates.append(_read_first(p, limit=400))

    env_text = "\n".join(env_candidates)
    found_envs = sorted(
        set(
            re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", env_text)
        )
    )
    # Filter likely noise
    env_vars = [e for e in found_envs if e not in {"DEBUG", "TRUE", "FALSE", "None", "AWS", "API", "URL"}][:20]

    # Data stores from docker-compose / requirements / imports
    data_stores = []
    lower = " ".join(all_files)
    if "postgres" in lower or "psycopg" in lower or "pg" in lower:
        data_stores.append({"type": "postgres", "version": "15"})
    if "mysql" in lower or "pymysql" in lower:
        data_stores.append({"type": "mysql", "version": "8"})
    if "redis" in lower:
        data_stores.append({"type": "redis", "version": "7"})
    if "mongodb" in lower or "pymongo" in lower:
        data_stores.append({"type": "mongodb", "version": "7"})
    if "s3" in lower or "boto" in lower:
        data_stores.append({"type": "s3", "version": "latest"})

    spec = AppSpec(
        app_id=path.name or "app",
        detected_stack=detected_stack,
        language=language,
        framework=framework,
        ports=ports,
        env_vars=env_vars,
        data_stores=data_stores,
    )
    log.info("spec=%s", spec.__dict__)
    return spec


def emit_spec(spec: AppSpec, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(spec.to_json() + "\n", encoding="utf-8")
