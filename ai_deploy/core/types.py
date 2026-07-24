"""Core types and protocols."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class AppSpec:
    app_id: str
    detected_stack: str = "unknown"
    language: str = "unknown"
    framework: str = "unknown"
    ports: List[int] = field(default_factory=list)
    env_vars: List[str] = field(default_factory=list)
    secrets_refs: List[str] = field(default_factory=list)
    data_stores: List[dict] = field(default_factory=list)
    traffic_hint: str = "low"
    regions: List[str] = field(default_factory=lambda: ["us-east-1"])
    budget_cap_usd: float = 0.0
    compliance: List[str] = field(default_factory=list)
    approved: bool = False

    def to_json(self) -> str:
        import json
        return json.dumps(self.__dict__, indent=2)


@dataclass
class ComponentConfig:
    type: str
    config: dict = field(default_factory=dict)


@dataclass
class SecurityFinding:
    finding: str
    severity: str
    action: str


@dataclass
class DeploymentPackage:
    provider: str = "aws"
    components: List[ComponentConfig] = field(default_factory=list)
    security_findings: List[SecurityFinding] = field(default_factory=list)
    cost_estimate: dict = field(default_factory=dict)
    rollback_instructions: str = ""
    approved: bool = False


@dataclass
class DeployState:
    app_id: str
    environment: str = "staging"
    status: str = "pending"
    artifacts: List[dict] = field(default_factory=list)
    last_deployed_at: Optional[str] = None
    deployed_by: str = "cli"
    tracking_ref: str = ""
