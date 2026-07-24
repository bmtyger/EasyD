"""CLI entrypoint for ai-deploy."""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import sys
from pathlib import Path

from ai_deploy.core.event_bus import EventBus
from ai_deploy.core.plugin_loader import PluginRegistry, load_plugins
from ai_deploy.core.types import AppSpec, DeployState

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
log = logging.getLogger("ai_deploy")


def _load_spec(path: Path) -> AppSpec:
    data = json.loads(path.read_text())
    return AppSpec(**data)


def _run_command(args) -> int:
    from ai_deploy.agents.architect import build as architect_build
    from ai_deploy.agents.cost import validate as cost_validate
    from ai_deploy.agents.requirements import analyze as analyze_requirements
    from ai_deploy.agents.security import scan as security_scan
    from ai_deploy.agents.terraform_security import scan as tf_scan
    from ai_deploy.core.rollback import write_manifest
    from ai_deploy.core.state import save_package, save_state
    from ai_deploy.plugins.aws_terraform import emit as aws_emit
    from ai_deploy.tracking.github import GitHubTracking

    bus = EventBus()
    try:
        from ai_deploy.notifier import NotifierBridge
        notifier = NotifierBridge()
        for event in ("spec.ready", "security.scan.done", "cost.validate.done", "terraform.scan.done", "deploy.done"):
            bus.subscribe(event, lambda payload, ev=event: notifier.publish(ev, payload))
    except Exception as exc:
        log.warning("notifier setup failed: %s", exc)

    registry = PluginRegistry(args.plugins)
    if registry.notifiers():
        log.info("plugin notifiers=%s", [m.name for m in registry.notifiers()])
    if registry.emitters(args.target):
        log.info("plugin emitters=%s", [m.name for m in registry.emitters(args.target)])
    if registry.detectors():
        log.info("plugin detectors=%s", [m.name for m in registry.detectors()])

    state = DeployState(app_id="local", environment=args.env, status="pending")
    output = args.output
    plugins = load_plugins(args.plugins)

    log.info("run target=%s env=%s plugins=%s", args.target, args.env, [p.name for p in plugins])

    if args.spec and args.spec.exists():
        spec = _load_spec(args.spec)
    else:
        spec = analyze_requirements(args.repo)
        spec.approved = True

    bus.publish("spec.ready", {"app_id": spec.app_id})
    package = architect_build(spec, target=args.target)

    bus.publish("security.scan.start", {"components": len(package.components)})
    package = security_scan(package)
    bus.publish("security.scan.done", {"approved": package.approved, "findings": len(package.security_findings)})

    bus.publish("cost.validate.start", {})
    package = cost_validate(spec, package)
    bus.publish("cost.validate.done", {"approved": package.approved})

    if args.target == "aws":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        aws_emit(package, args.output.parent)

        bus.publish("terraform.scan.start", {"directory": str(args.output.parent)})
        package = tf_scan(args.output.parent, package)
        bus.publish("terraform.scan.done", {"approved": package.approved, "findings": len(package.security_findings)})

    save_package(package, args.output)
    state.status = "live" if package.approved else "failed"
    state.artifacts.append({"type": "package.json", "ref": str(args.output)})
    if package.security_findings:
        state.artifacts.append({"type": "security_findings", "ref": str(args.output)})
    save_state(state, args.state_file)

    write_manifest(
        args.output.parent / "manifest.json",
        package=package,
        state=state,
        terraform_dir=args.output.parent if args.target == "aws" else None,
    )

    from ai_deploy.core.ops import write_summary as write_ops_summary
    write_ops_summary(
        args.output.parent / "ops-summary.json",
        spec=spec,
        package=package,
        state=state,
    )

    if getattr(args, "github_issue", None):
        tracker = GitHubTracking(repo=args.github_repo or __import__("os").environ.get("GITHUB_REPOSITORY", ""))
        if tracker.repo:
            tracker.post_deploy_summary(args.github_issue, spec, package, terraform_dir=args.output.parent)
        else:
            log.warning("github issue requested but no repo configured")

    epic_number = None
    if getattr(args, "create_github_epic", None) and not getattr(args, "github_issue", None):
        tracker = GitHubTracking(repo=args.github_repo or __import__("os").environ.get("GITHUB_REPOSITORY", ""))
        if tracker.repo:
            epic = tracker.ensure_epic(args.create_github_epic, f"Auto-created epic for {spec.app_id} deploy to {args.env}")
            if epic and epic.get("number"):
                epic_number = epic["number"]
                tracker.post_deploy_summary(epic_number, spec, package, terraform_dir=args.output.parent)
                state.tracking_ref = f"{tracker.repo}#{epic_number}"
        else:
            log.warning("github epic requested but no repo configured")

    log.info("deployment state=%s package=%s", state.status, args.output)
    print(json.dumps({"status": state.status, "package": str(args.output)}, indent=2))
    return 0 if package.approved else 1


def _plan_command(args) -> int:
    mod = importlib.import_module("ai_deploy.commands.plan")
    return mod.main([
        "--target", args.target,
        "--env", args.env,
        "--repo", str(args.repo),
        "--output", str(args.output),
    ])


def _validate_command(args) -> int:
    mod = importlib.import_module("ai_deploy.commands.validate")
    return mod.main([
        "--target", args.target,
        "--repo", str(args.repo),
        "--output", str(args.output),
    ])


def _rollback_command(args) -> int:
    mod = importlib.import_module("ai_deploy.commands.rollback")
    return mod.main([str(args.manifest), "--output", str(args.output)])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-deploy", description="AI deploy compiler")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run")
    run.add_argument("--target", default="aws")
    run.add_argument("--env", default="staging", choices=["staging", "prod"])
    run.add_argument("--spec", type=Path, default=None)
    run.add_argument("--state-file", type=Path, default=Path(".deploy/state.json"))
    run.add_argument("--output", type=Path, default=Path(".deploy/package.json"))
    run.add_argument("--repo", type=Path, default=Path("."))
    run.add_argument("--plugins", type=Path, default=Path("plugins"))
    run.add_argument("--github-issue", type=int, default=None)
    run.add_argument("--github-repo", type=str, default=None)
    run.add_argument("--create-github-epic", type=str, default=None)

    plan = sub.add_parser("plan")
    plan.add_argument("--target", default="aws")
    plan.add_argument("--env", default="staging", choices=["staging", "prod"])
    plan.add_argument("--repo", type=Path, default=Path("."))
    plan.add_argument("--output", type=Path, default=Path(".deploy/plan.json"))

    validate = sub.add_parser("validate")
    validate.add_argument("--target", default="aws")
    validate.add_argument("--repo", type=Path, default=Path("."))
    validate.add_argument("--output", type=Path, default=Path(".deploy/validation.json"))

    rollback = sub.add_parser("rollback")
    rollback.add_argument("manifest", type=Path)
    rollback.add_argument("--output", type=Path, default=Path(".deploy/rollback-restore.json"))

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    dispatch = {
        "run": _run_command,
        "plan": _plan_command,
        "validate": _validate_command,
        "rollback": _rollback_command,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
