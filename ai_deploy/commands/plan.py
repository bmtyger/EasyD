"""Plan command: IaC summary, components, cost estimate."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ai_deploy.agents.architect import build as architect_build
from ai_deploy.agents.cost import validate as cost_validate
from ai_deploy.agents.requirements import analyze as analyze_requirements
from ai_deploy.core.types import AppSpec
from ai_deploy.plugins.aws_terraform import emit as aws_emit

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
log = logging.getLogger("ai_deploy")


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="ai-deploy-plan")
    parser.add_argument("--target", default="aws")
    parser.add_argument("--env", default="staging", choices=["staging", "prod"])
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path(".deploy/plan.json"))
    args = parser.parse_args(argv)

    spec = analyze_requirements(args.repo)
    spec.approved = True
    package = architect_build(spec, target=args.target)
    package = cost_validate(spec, package)

    plan = {
        "environment": args.env,
        "provider": package.provider,
        "app_id": spec.app_id,
        "stack": {
            "language": spec.language,
            "framework": spec.framework,
            "detected_stack": spec.detected_stack,
            "ports": spec.ports,
        },
        "components": [c.type for c in package.components],
        "cost_estimate": package.cost_estimate,
        "approved": package.approved,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    log.info("wrote plan to %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
