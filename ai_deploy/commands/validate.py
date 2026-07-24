"""Validate command: schema + Terraform checks without apply."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ai_deploy.agents.architect import build as architect_build
from ai_deploy.agents.requirements import analyze as analyze_requirements
from ai_deploy.agents.terraform_security import scan as tf_scan
from ai_deploy.plugins.aws_terraform import emit as aws_emit

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
log = logging.getLogger("ai_deploy")


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="ai-deploy-validate")
    parser.add_argument("--target", default="aws")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path(".deploy/validation.json"))
    args = parser.parse_args(argv)

    spec = analyze_requirements(args.repo)
    package = architect_build(spec, target=args.target)

    tf_dir = Path(".deploy/tf-validate")
    aws_emit(package, tf_dir)
    package = tf_scan(tf_dir, package)

    report = {
        "app_id": spec.app_id,
        "provider": package.provider,
        "approved": package.approved,
        "findings": [f.__dict__ for f in package.security_findings],
        "issues": [f.finding for f in package.security_findings if f.severity == "high"],
        "warnings": [f.finding for f in package.security_findings if f.severity != "high"],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    log.info("validation results written to %s", args.output)
    return 0 if package.approved else 2


if __name__ == "__main__":
    raise SystemExit(main())
