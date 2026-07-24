import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_deploy.core.promote import promote
from ai_deploy.core.rollback import restore_previous, write_manifest
from ai_deploy.core.types import AppSpec, DeployState, DeploymentPackage
import tempfile


def test_promote_staging_to_prod():
    spec = AppSpec(app_id="demo")
    pkg = DeploymentPackage()
    state = DeployState(app_id="demo", environment="staging", status="live")
    new_state, _ = promote(pkg, state, "prod")
    assert new_state.environment == "prod"
    assert new_state.status == "pending"


def test_write_manifest_creates_backup():
    spec = AppSpec(app_id="demo")
    pkg = DeploymentPackage()
    state = DeployState(app_id="demo", environment="staging", status="live")
    d = Path(tempfile.mkdtemp()) / "manifest.json"
    write_manifest(d, package=pkg, state=state)
    assert d.exists()
    assert not d.with_suffix(".prev.json").exists()


def test_rollback_without_previous_manifest():
    import tempfile
    from pathlib import Path
    manifest = Path(tempfile.mkdtemp()) / "manifest.json"
    manifest.write_text(json.dumps({}, indent=2), encoding="utf-8")
    out = Path(tempfile.mkdtemp())
    result = restore_previous(manifest, out)
    assert result.exists()
    assert json.loads(result.read_text())["restored"] is False
