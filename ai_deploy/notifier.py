"""Notifier bridge for deploy events."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from ai_deploy.core.types import AppSpec, DeploymentPackage, DeployState

log = logging.getLogger(__name__)


class NotifierBridge:
    def __init__(self) -> None:
        self.jira: Optional[Any] = None
        self._load_jira()

    def _load_jira(self) -> None:
        base_url = os.environ.get("JIRA_BASE_URL")
        email = os.environ.get("JIRA_EMAIL")
        api_token = os.environ.get("JIRA_API_TOKEN")
        if base_url and email and api_token:
            try:
                from ai_deploy.plugins.jira.notifier import JiraNotifier
                self.jira = JiraNotifier(base_url=base_url, email=email, api_token=api_token)
                log.info("jira notifier loaded")
            except Exception as exc:
                log.warning("jira notifier load failed: %s", exc)

    def publish(self, event: str, payload: dict[str, Any]) -> None:
        routes = {
            "spec.ready": self._on_spec_ready,
            "security.scan.done": self._on_security_done,
            "cost.validate.done": self._on_cost_done,
            "terraform.scan.done": self._on_terraform_done,
            "deploy.done": self._on_deploy_done,
        }
        handler = routes.get(event)
        if handler:
            try:
                handler(payload)
            except Exception as exc:
                log.exception("notify handler failed for %s", event)

    def _on_spec_ready(self, payload: dict[str, Any]) -> None:
        if self.jira:
            try:
                self.jira.create_issue(
                    project="AI",
                    title=f"Deploy request: {payload.get('app_id', 'app')}",
                    description=f"AppSpec ready: {json.dumps(payload)}",
                )
            except Exception as exc:
                log.error("jira spec.ready failed: %s", exc)

    def _on_security_done(self, payload: dict[str, Any]) -> None:
        if self.jira and not payload.get("approved", True):
            try:
                self.jira.create_issue(
                    project="AI",
                    title="Security scan blocked deploy",
                    description=f"Findings: {payload.get('findings', 0)}",
                    issue_type="Bug",
                )
            except Exception as exc:
                log.error("jira security.scan.done failed: %s", exc)

    def _on_cost_done(self, payload: dict[str, Any]) -> None:
        if self.jira and not payload.get("approved", True):
            try:
                issue = self.jira.create_issue(
                    project="AI",
                    title="Cost validation failed",
                    description="Budget cap exceeded or estimate invalid.",
                    issue_type="Task",
                )
                if issue and issue.get("key"):
                    self.jira.transition(issue["key"], "Blocked")
            except Exception as exc:
                log.error("jira cost.validate.done failed: %s", exc)

    def _on_terraform_done(self, payload: dict[str, Any]) -> None:
        if self.jira and not payload.get("approved", True):
            try:
                issue = self.jira.create_issue(
                    project="AI",
                    title="IaC validation failed",
                    description=f"Findings: {payload.get('findings', 0)}",
                    issue_type="Bug",
                )
                if issue and issue.get("key"):
                    self.jira.transition(issue["key"], "Blocked")
            except Exception as exc:
                log.error("jira terraform.scan.done failed: %s", exc)

    def _on_deploy_done(self, payload: dict[str, Any]) -> None:
        if self.jira:
            try:
                issue = self.jira.create_issue(
                    project="AI",
                    title=f"Deploy summary: {payload.get('app_id', 'app')}",
                    description=json.dumps(payload, indent=2),
                    issue_type="Task",
                )
                if issue and issue.get("key"):
                    state = (payload.get("state") or {}).get("status")
                    if state == "live":
                        self.jira.transition(issue["key"], "Done")
            except Exception as exc:
                log.error("jira deploy.done failed: %s", exc)
