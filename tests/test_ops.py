import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_deploy.core.ops import write_summary
from ai_deploy.core.types import AppSpec, DeployState, DeploymentPackage
import tempfile


def test_write_summary_without_actual_cost():
    d = Path(tempfile.mkdtemp()) / "ops-summary.json"
    spec = AppSpec(app_id="demo")
    pkg = DeploymentPackage(provider="aws")
    state = DeployState(app_id="demo", environment="staging", status="live")
    out = write_summary(d, spec=spec, package=pkg, state=state)
    data = json.loads(out.read_text())
    assert data["app_id"] == "demo"
    assert data["cost"]["actual_usd"] is None
    assert data["security_findings_count"] == 0


def test_write_summary_with_actual_cost_and_variance_alert():
    d = Path(tempfile.mkdtemp()) / "ops-summary.json"
    spec = AppSpec(app_id="demo")
    pkg = DeploymentPackage(provider="aws", cost_estimate={"monthly_estimate_usd": 50.0})
    state = DeployState(app_id="demo", environment="staging", status="live")
    out = write_summary(d, spec=spec, package=pkg, state=state, actual_cost_usd=65.0)
    data = json.loads(out.read_text())
    assert data["cost"]["variance_usd"] == 15.0
    assert data["cost"]["alert"] is True
