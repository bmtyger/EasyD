import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_deploy.tracking.github import GitHubTracking


def test_github_tracker_defaults():
    tracker = GitHubTracking(repo="o/u")
    assert tracker.token is None


def test_github_tracker_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "abc")
    tracker = GitHubTracking(repo="o/u")
    assert tracker.token == "abc"
