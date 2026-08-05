"""Async GitHub API client wrapper using httpx."""

from __future__ import annotations

from typing import Any, cast

import httpx


class GitHubClient:
    """Async wrapper around the GitHub REST API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str, owner: str, repo: str) -> None:
        self.owner = owner
        self.repo = repo
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    @property
    def _repo_url(self) -> str:
        return f"/repos/{self.owner}/{self.repo}"

    async def list_pull_requests(
        self, state: str = "open", per_page: int = 30
    ) -> list[dict[str, Any]]:
        """List pull requests for the repository."""
        response = await self._client.get(
            f"{self._repo_url}/pulls",
            params={"state": state, "per_page": per_page},
        )
        response.raise_for_status()
        return cast(list[dict[str, Any]], response.json())

    async def create_pull_request(
        self,
        title: str,
        head: str,
        base: str = "main",
        body: str | None = None,
        draft: bool = False,
    ) -> dict[str, Any]:
        """Create a new pull request."""
        payload: dict[str, Any] = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
        }
        if body:
            payload["body"] = body

        response = await self._client.post(f"{self._repo_url}/pulls", json=payload)
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def merge_pull_request(
        self, pr_number: int, merge_method: str = "squash"
    ) -> dict[str, Any]:
        """Merge a pull request."""
        response = await self._client.put(
            f"{self._repo_url}/pulls/{pr_number}/merge",
            json={"merge_method": merge_method},
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> GitHubClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
