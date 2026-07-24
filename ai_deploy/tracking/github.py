"""GitHub tracking writer."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

from ai_deploy.core.types import AppSpec, DeploymentPackage

log = logging.getLogger(__name__)


class GitHubTracking:
    def __init__(self, repo: str, token: Optional[str] = None) -> None:
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    def _gh(self, method: str, path: str, data: Optional[dict] = None) -> dict:
        url = f"https://api.github.com/repos/{urllib.parse.quote(self.repo, safe='')}{path}"
        body = json.dumps(data or {}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="ignore")
            log.error("github api error %s %s body=%s", exc.code, path, text[:500])
            raise

    def _gh_cli(self, args: list[str], stdin: Optional[str] = None, check: bool = False) -> str:
        cmd = ["gh"] + args
        log.info("gh command: %s", " ".join(cmd))
        out = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
        if out.returncode != 0:
            log.error("gh error: %s", out.stderr[-1000:])
            if check:
                raise RuntimeError(f"gh failed: {out.stderr[-500:]}")
        return out.stdout

    def create_issue(self, title: str, body: str) -> dict:
        if self._gh_cli(["issue", "create", "--title", title, "--body", body, "--repo", self.repo], check=False).strip():
            return {}
        return self._gh("POST", "/issues", {"title": title, "body": body})

    def comment(self, issue_number: int, body: str) -> dict:
        if self._gh_cli(["issue", "comment", str(issue_number), "--body", body, "--repo", self.repo], check=False).strip():
            return {}
        return self._gh("POST", f"/issues/{issue_number}/comments", {"body": body})

    def transition(self, issue_number: int, state: str) -> dict:
        if state.lower() in {"closed", "close"}:
            if self._gh_cli(["issue", "close", str(issue_number), "--repo", self.repo], check=False).strip():
                return {}
            return self._gh("POST", f"/issues/{issue_number}/comments", {"body": f"Transitioned to `closed` by ai-deploy.\n"})
        if self._gh_cli(["issue", "reopen", str(issue_number), "--repo", self.repo], check=False).strip():
            return {}
        return self._gh("POST", f"/issues/{issue_number}/comments", {"body": f"Transitioned to `reopened` by ai-deploy.\n"})

    def post_deploy_summary(
        self,
        issue_number: int,
        spec: AppSpec,
        package: DeploymentPackage,
        terraform_dir: Optional[Path] = None,
    ) -> dict:
        lines = [
            "## ai-deploy summary",
            "",
            "### AppSpec",
            "| Field | Value |",
            "| --- | --- |",
            f"| app_id | {spec.app_id} |",
            f"| language | {spec.language} |",
            f"| framework | {spec.framework} |",
            f"| ports | {', '.join(map(str, spec.ports))} |",
            f"| detected_stack | {spec.detected_stack} |",
            "",
            "### DeploymentPackage",
            "| Field | Value |",
            "| --- | --- |",
            f"| provider | {package.provider} |",
            f"| components | {', '.join(c.type for c in package.components)} |",
            f"| approved | {package.approved} |",
            f"| rollback | {package.rollback_instructions or 'n/a'} |",
            "",
        ]

        if package.security_findings:
            lines.append("### Security findings")
            lines.append("| Severity | Finding | Action |")
            lines.append("| --- | --- | --- |")
            for f in package.security_findings:
                lines.append(f"| {f.severity} | {f.finding} | {f.action} |")
            lines.append("")

        if terraform_dir and (terraform_dir / "main.tf").exists():
            lines.append("### Terraform")
            lines.append(f"Path: `{terraform_dir / 'main.tf'}`")
            lines.append("")
            lines.append("```hcl")
            lines.append((terraform_dir / "main.tf").read_text(encoding="utf-8", errors="ignore")[:4000])
            lines.append("```")
            lines.append("")

        body = "\n".join(lines)
        return self.comment(issue_number, body)

    def ensure_epic(self, title: str, body: str) -> dict:
        issue = self.create_issue(title, body)
        if issue.get("number"):
            return issue
        # fallback search exact title
        q = urllib.parse.quote(f"repo:{self.repo} {title} in:title")
        found = self._gh("GET", f"/search/issues?q={q}")
        items = found.get("items", [])
        if items:
            return self._gh("GET", f"/issues/{items[0]['number']}")
        return {"number": None}
