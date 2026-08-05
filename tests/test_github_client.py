"""Tests for the GitHub API client."""

import pytest

from gitdevflow.core.github_client import GitHubClient


class TestGitHubClient:
    """Test the GitHubClient wrapper."""

    def test_client_initialization(self) -> None:
        """Client should initialize with correct attributes."""
        client = GitHubClient(token="test-token", owner="owner", repo="repo")
        assert client.owner == "owner"
        assert client.repo == "repo"

    def test_repo_url(self) -> None:
        """Repo URL should be correctly constructed."""
        client = GitHubClient(token="test-token", owner="owner", repo="repo")
        assert client._repo_url == "/repos/owner/repo"

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Client should support async context manager."""
        async with GitHubClient(
            token="test-token", owner="owner", repo="repo"
        ) as client:
            assert client.owner == "owner"
