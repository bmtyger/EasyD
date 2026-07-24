"""Rollback CLI command."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from ai_deploy.core.rollback import restore_previous

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
log = logging.getLogger("ai_deploy")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-deploy-rollback", description="ai-deploy rollback")
    parser.add_argument("manifest", type=Path, help="Path to deploy manifest.json")
    parser.add_argument("--output", type=Path, default=Path(".deploy/rollback-restore.json"))
    args = parser.parse_args(argv)

    if not args.manifest.exists():
        log.error("manifest missing: %s", args.manifest)
        return 2

    restore_previous(args.manifest, args.output.parent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
