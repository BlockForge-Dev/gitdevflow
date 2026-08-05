"""Tests for the async GitHub API client, error mapping, retries, and pagination."""

from typing import Any

import httpx
import pytest
import respx

from gitdevflow.core.exceptions import (
    AuthenticationError,
    GitHubAPIError,
    NotFoundError,
    RateLimitedError,
)
from gitdevflow.core.github_client import GitHubClient
from gitdevflow.core.models import BranchComparison, Label, PullRequest, Repository


class TestGitHubClient:
    """Test suite for GitHubClient REST API methods."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_repo(
        self, github_client: GitHubClient, mock_repo_data: dict[str, Any]
    ) -> None:
        """`get_repo` fetches repository info and parses Repository model."""
        respx.get("https://api.github.com/repos/octocat/Hello-World").mock(
            return_value=httpx.Response(200, json=mock_repo_data)
        )

        repo = await github_client.get_repo("octocat", "Hello-World")
        assert isinstance(repo, Repository)
        assert repo.name == "Hello-World"
        assert repo.full_name == "octocat/Hello-World"
        assert repo.owner.login == "octocat"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_pull_requests(
        self, github_client: GitHubClient, mock_pr_response: dict[str, Any]
    ) -> None:
        """`get_pull_requests` retrieves PR list."""
        respx.get("https://api.github.com/repos/octocat/Hello-World/pulls").mock(
            return_value=httpx.Response(200, json=[mock_pr_response])
        )

        prs = await github_client.get_pull_requests("octocat", "Hello-World")
        assert len(prs) == 1
        assert isinstance(prs[0], PullRequest)
        assert prs[0].number == 42
        assert prs[0].title == "Add feature X"

    @pytest.mark.asyncio
    @respx.mock
    async def test_pagination(
        self, github_client: GitHubClient, mock_pr_response: dict[str, Any]
    ) -> None:
        """`paginate` follows Link header rel="next" to fetch all pages."""
        base_url = "https://api.github.com/repos/octocat/Hello-World/pulls"
        page1_url = f"{base_url}?state=open&per_page=1"
        page2_url = f"{base_url}?page=2"

        pr1 = {**mock_pr_response, "number": 1, "title": "PR 1"}
        pr2 = {**mock_pr_response, "number": 2, "title": "PR 2"}

        link_header = f'<{page2_url}>; rel="next", <{page2_url}>; rel="last"'

        respx.get(page1_url).mock(
            return_value=httpx.Response(200, json=[pr1], headers={"Link": link_header})
        )
        respx.get(page2_url).mock(return_value=httpx.Response(200, json=[pr2]))

        items = []
        async for item in github_client.paginate(
            "/repos/octocat/Hello-World/pulls",
            params={"state": "open"},
            per_page=1,
        ):
            items.append(item)

        assert len(items) == 2
        assert items[0]["number"] == 1
        assert items[1]["number"] == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_pull_request(
        self, github_client: GitHubClient, mock_pr_response: dict[str, Any]
    ) -> None:
        """`create_pull_request` posts PR payload and parses response."""
        respx.post("https://api.github.com/repos/octocat/Hello-World/pulls").mock(
            return_value=httpx.Response(201, json=mock_pr_response)
        )

        pr = await github_client.create_pull_request(
            owner="octocat",
            repo="Hello-World",
            title="Add feature X",
            head="feature-branch",
            base="main",
        )
        assert isinstance(pr, PullRequest)
        assert pr.number == 42

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_and_set_labels(
        self, github_client: GitHubClient, mock_label_data: dict[str, Any]
    ) -> None:
        """Test `get_labels` and `set_labels`."""
        respx.get("https://api.github.com/repos/octocat/Hello-World/labels").mock(
            return_value=httpx.Response(200, json=[mock_label_data])
        )
        respx.post(
            "https://api.github.com/repos/octocat/Hello-World/issues/42/labels"
        ).mock(return_value=httpx.Response(200, json=[mock_label_data]))

        labels = await github_client.get_labels("octocat", "Hello-World")
        assert len(labels) == 1
        assert isinstance(labels[0], Label)
        assert labels[0].name == "enhancement"

        set_result = await github_client.set_labels(
            "octocat", "Hello-World", 42, ["enhancement"]
        )
        assert len(set_result) == 1
        assert set_result[0].name == "enhancement"

    @pytest.mark.asyncio
    @respx.mock
    async def test_compare_branches(
        self, github_client: GitHubClient, mock_compare_data: dict[str, Any]
    ) -> None:
        """`compare_branches` parses BranchComparison response."""
        url = "https://api.github.com/repos/octocat/Hello-World/compare/main...feature"
        respx.get(url).mock(return_value=httpx.Response(200, json=mock_compare_data))

        comparison = await github_client.compare_branches(
            "octocat", "Hello-World", "main", "feature"
        )
        assert isinstance(comparison, BranchComparison)
        assert comparison.ahead_by == 2
        assert len(comparison.commits) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_authentication_error_401(self, github_client: GitHubClient) -> None:
        """HTTP 401 raises AuthenticationError."""
        respx.get("https://api.github.com/repos/octocat/Hello-World").mock(
            return_value=httpx.Response(401, json={"message": "Bad credentials"})
        )

        with pytest.raises(AuthenticationError):
            await github_client.get_repo("octocat", "Hello-World")

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limited_error_429(self, github_client: GitHubClient) -> None:
        """HTTP 429 raises RateLimitedError after retries."""
        respx.get("https://api.github.com/repos/octocat/Hello-World").mock(
            return_value=httpx.Response(
                429, json={"message": "API rate limit exceeded"}
            )
        )

        with pytest.raises(RateLimitedError):
            await github_client.get_repo("octocat", "Hello-World")

    @pytest.mark.asyncio
    @respx.mock
    async def test_not_found_error_404(self, github_client: GitHubClient) -> None:
        """HTTP 404 raises NotFoundError."""
        respx.get("https://api.github.com/repos/octocat/Hello-World").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )

        with pytest.raises(NotFoundError):
            await github_client.get_repo("octocat", "Hello-World")

    @pytest.mark.asyncio
    @respx.mock
    async def test_generic_api_error_500(self, github_client: GitHubClient) -> None:
        """HTTP 500 raises GitHubAPIError after retries exhaust."""
        respx.get("https://api.github.com/repos/octocat/Hello-World").mock(
            return_value=httpx.Response(500, json={"message": "Internal Server Error"})
        )

        with pytest.raises(GitHubAPIError):
            await github_client.get_repo("octocat", "Hello-World")
