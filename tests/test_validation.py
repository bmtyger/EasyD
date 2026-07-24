import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_deploy.commands.validate import main as validate_main
from ai_deploy.commands.validation import validate_spec_issues, validate_deployment_package_issues
import tempfile


def test_validate_spec_clean():
    from ai_deploy.core.types import AppSpec
    spec = AppSpec(app_id="demo")
    assert validate_spec_issues(spec) == []


def test_validate_spec_invalid_app_id():
    from ai_deploy.core.types import AppSpec
    spec = AppSpec(app_id="")
    issues = validate_spec_issues(spec)
    assert any("app_id" in issue for issue in issues)


def test_validate_manifest_issues():
    d = Path(tempfile.mkdtemp()) / "manifest.json"
    d.write_text(json.dumps({"app_id": "x", "status": "live"}, indent=2), encoding="utf-8")
    assert validate_deployment_package_issues(d) == []


def test_validate_manifest_missing_fields():
    d = Path(tempfile.mkdtemp()) / "manifest.json"
    d.write_text("{}", encoding="utf-8")
    issues = validate_deployment_package_issues(d)
    assert "manifest missing app_id" in issues
    assert "manifest missing status" in issues
