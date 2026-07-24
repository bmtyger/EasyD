"""Jira notifier plugin."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

log = logging.getLogger(__name__)


class JiraNotifier:
    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token

    def _request(self, method: str, path: str, data: Optional[dict] = None) -> dict:
        url = f"{self.base_url}/rest/api/3{path}"
        body = json.dumps(data or {}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        # basic auth with email:api_token
        import base64
        token = base64.b64encode(f"{self.email}:{self.api_token}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="ignore")
            log.error("jira api error %s %s body=%s", exc.code, path, text[:500])
            raise

    def create_issue(self, project: str, title: str, description: str, issue_type: str = "Task") -> dict:
        data = {
            "fields": {
                "project": {"key": project},
                "summary": title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
                },
                "issuetype": {"name": issue_type},
            }
        }
        return self._request("POST", "/issue", data)

    def comment(self, issue_key: str, body: str) -> dict:
        data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": body}]}],
            }
        }
        return self._request("POST", f"/issue/{issue_key}/comment", data)

    def transition(self, issue_key: str, transition_name: str) -> dict:
        data = {"transition": {"name": transition_name}}
        return self._request("POST", f"/issue/{issue_key}/transitions", data)
