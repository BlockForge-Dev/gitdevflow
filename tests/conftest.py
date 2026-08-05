"""Shared test fixtures: mock GitHub responses, temporary config files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    """Create a temporary .gitdevflow.yml config file."""
    config_content = """\
github:
  owner: test-owner
  repo: test-repo
  token: ghp_test_token_123

pr:
  default_base: main
  labels:
    - auto-merge

changelog:
  output: CHANGELOG.md
  group_by_labels: true
"""
    config_file = tmp_path / ".gitdevflow.yml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_pr_response() -> dict[str, Any]:
    """Return a mock GitHub PR API response."""
    return {
        "number": 42,
        "title": "Add feature X",
        "state": "open",
        "html_url": "https://github.com/test-owner/test-repo/pull/42",
        "user": {"login": "testuser"},
        "labels": [{"name": "enhancement"}],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
    }


@pytest.fixture
def mock_pr_list(mock_pr_response: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a list of mock PR responses."""
    return [
        mock_pr_response,
        {
            **mock_pr_response,
            "number": 43,
            "title": "Fix bug Y",
            "labels": [{"name": "bug"}],
        },
    ]
