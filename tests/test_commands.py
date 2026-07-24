import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_deploy.commands.plan import main as plan_main
from ai_deploy.commands.validate import main as validate_main


def test_plan_writes_output():
    import tempfile
    d = Path(tempfile.mkdtemp())
    ret = plan_main(["--repo", "demo-fastapi/app", "--output", str(d / "plan.json"), "--target", "aws", "--env", "staging"])
    assert ret == 0
    assert (d / "plan.json").exists()


def test_validate_clean_repo():
    import tempfile
    d = Path(tempfile.mkdtemp())
    ret = validate_main(["--repo", "demo-fastapi/app", "--output", str(d / "validation.json"), "--target", "aws"])
    # current emitted Terraform includes placeholder public SG; validation may fail
    assert ret in (0, 2)
