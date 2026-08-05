"""Shared test fixtures: mock GitHub responses, temporary config files."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio

from gitdevflow.core.github_client import GitHubClient


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
