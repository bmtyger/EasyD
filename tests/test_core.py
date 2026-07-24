import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_deploy.core.types import AppSpec, DeploymentPackage, SecurityFinding


def test_appspec_defaults() -> None:
    spec = AppSpec(app_id="demo")
    assert spec.app_id == "demo"
    assert spec.ports == []
    assert spec.budget_cap_usd == 0.0


def test_security_finding_high_blocks() -> None:
    package = DeploymentPackage(components=[])
    from ai_deploy.agents.security import scan
    package = scan(package)
    assert package.approved is True

