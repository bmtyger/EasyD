import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_deploy.core.types import DeploymentPackage
from ai_deploy.agents.terraform_security import scan as tf_scan
import tempfile


def _write_tf(text: str) -> Path:
    d = Path(tempfile.mkdtemp())
    (d / "main.tf").write_text(text, encoding="utf-8")
    return d


def test_tf_public_ingress():
    pkg = DeploymentPackage(components=[])
    d = _write_tf('''
resource "aws_security_group" "app" {
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
''')
    pkg = tf_scan(d, pkg)
    assert any(f.severity == "high" for f in pkg.security_findings)
    assert pkg.approved is False


def test_tf_clean_passes():
    pkg = DeploymentPackage(components=[])
    d = _write_tf('''
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
''')
    pkg = tf_scan(d, pkg)
    assert not pkg.security_findings
    assert pkg.approved is True
