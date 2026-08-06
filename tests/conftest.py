"""Shared test fixtures: mock GitHub responses, temporary config files, CLI runner."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
import respx
from typer.testing import CliRunner

from gitdevflow.core.github_client import GitHubClient

runner_instance = CliRunner()


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture providing Typer CliRunner."""
    return runner_instance


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Fixture creating a temporary valid .gitdevflow.yaml config file."""
    cfg_file = tmp_path / ".gitdevflow.yaml"
    content = """github_token: "ghp_fixture_token_12345"
default_repo: "octocat/Hello-World"
pr_label_prefix: "type:"
changelog_sections:
  Features:
    - feat
    - enhancement
  Bug Fixes:
    - fix
    - bug
output_format: "rich"
"""
    cfg_file.write_text(content, encoding="utf-8")
    return cfg_file


@pytest.fixture
def mock_github() -> Generator[respx.Router, None, None]:
    """Fixture using respx to mock GitHub HTTP requests."""
    with respx.mock(
        base_url="https://api.github.com", assert_all_called=False
    ) as respx_mock:
        yield respx_mock


@pytest.fixture
def mock_user_data() -> dict[str, Any]:
    """Return a mock GitHub User dict."""
    return {
        "login": "octocat",
        "id": 1,
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "html_url": "https://github.com/octocat",
    }


@pytest.fixture
def mock_label_data() -> dict[str, Any]:
    """Return a mock GitHub Label dict."""
    return {
        "name": "enhancement",
        "color": "a2eeef",
        "description": "New feature or request",
    }


@pytest.fixture
def mock_repo_data(mock_user_data: dict[str, Any]) -> dict[str, Any]:
    """Return a mock GitHub Repository dict."""
    return {
        "id": 129432,
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "owner": mock_user_data,
        "html_url": "https://github.com/octocat/Hello-World",
        "default_branch": "main",
        "private": False,
    }


@pytest.fixture
def mock_pr_response(
    mock_user_data: dict[str, Any], mock_label_data: dict[str, Any]
) -> dict[str, Any]:
    """Return a mock GitHub PR API response."""
    return {
        "number": 42,
        "title": "Add feature X",
        "state": "open",
        "html_url": "https://github.com/octocat/Hello-World/pull/42",
        "user": mock_user_data,
        "labels": [mock_label_data],
        "head": {
            "ref": "feature-branch",
            "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
        },
        "base": {
            "ref": "main",
            "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
        },
        "draft": False,
        "created_at": "2026-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_compare_data() -> dict[str, Any]:
    """Return a mock GitHub branch comparison dict."""
    return {
        "ahead_by": 2,
        "behind_by": 0,
        "status": "ahead",
        "total_commits": 2,
        "commits": [
            {
                "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
                "commit": {"message": "feat: add feature X"},
                "html_url": (
                    "https://github.com/octocat/Hello-World/commit/"
                    "6dcb09b5b57875f334f61aebed695e2e4193db5e"
                ),
            }
        ],
    }


@pytest_asyncio.fixture
async def github_client() -> AsyncGenerator[GitHubClient, None]:
    """Provide a GitHubClient instance for tests."""
    async with GitHubClient(
        token="test-token", owner="octocat", repo="Hello-World"
    ) as client:
        yield client
