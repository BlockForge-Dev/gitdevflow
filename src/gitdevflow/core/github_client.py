"""Async GitHub REST API client with resilience, retries, and pagination."""

from __future__ import annotations

import re
from collections.abc import AsyncGenerator
from typing import Any, cast

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from gitdevflow.core.exceptions import (
    AuthenticationError,
    GitHubAPIError,
    NotFoundError,
    RateLimitedError,
)
from gitdevflow.core.models import BranchComparison, Label, PullRequest, Repository


class _TransientHTTPError(Exception):
    """Internal exception to trigger tenacity retry on 5xx and 429."""


class GitHubClient:
    """Async wrapper around the GitHub REST API with retries and pagination."""

    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        token: str,
        owner: str = "",
        repo: str = "",
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.owner = owner
        self.repo = repo
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Map HTTP error status codes to custom gitdevflow exceptions."""
        if response.is_success:
            return

        status = response.status_code
        try:
            payload = response.json()
            message = payload.get("message", response.text)
        except Exception:
            message = response.text or f"HTTP status {status}"

        if status == 401:
            raise AuthenticationError(message)
        if status in (429, 403) and ("rate limit" in message.lower() or status == 429):
            retry_after = response.headers.get("Retry-After")
            seconds = (
                int(retry_after) if retry_after and retry_after.isdigit() else None
            )
            raise RateLimitedError(message, retry_after=seconds)
        if status == 404:
            raise NotFoundError(message)

        raise GitHubAPIError(status, message)

    @retry(
        retry=retry_if_exception_type((_TransientHTTPError, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
        reraise=True,
    )
    async def _send_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send HTTP request with automatic retries for transient errors."""
        response = await self._client.request(method, url, params=params, json=json)
        if response.status_code in (429, 500, 502, 503, 504):
            raise _TransientHTTPError(f"Transient HTTP error: {response.status_code}")
        return response

    async def _request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute request with retries and error mapping."""
        try:
            response = await self._send_request(method, url, params=params, json=json)
        except _TransientHTTPError as err:
            last_code = int(str(err).split(":")[-1].strip())
            if last_code == 429:
                raise RateLimitedError("GitHub API rate limit exceeded") from err
            raise GitHubAPIError(
                last_code, f"Server error after retries: {last_code}"
            ) from err

        self._handle_error_response(response)
        return response

    async def paginate(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        per_page: int = 30,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Yield items across paginated GitHub endpoints using RFC 5988 Link headers."""
        next_url: str | None = url
        query_params = dict(params or {})
        query_params["per_page"] = per_page

        while next_url:
            response = await self._request("GET", next_url, params=query_params)
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    yield cast(dict[str, Any], item)
            else:
                yield cast(dict[str, Any], data)

            link_header = response.headers.get("Link")
            next_url = None
            query_params = {}

            if link_header:
                matches = re.findall(r'<([^>]+)>;\s*rel="([^"]+)"', link_header)
                for link, rel in matches:
                    if rel == "next":
                        next_url = link
                        break

    async def get_repo(self, owner: str, repo: str) -> Repository:
        """Get repository details."""
        response = await self._request("GET", f"/repos/{owner}/{repo}")
        return Repository.model_validate(response.json())

    async def get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> list[PullRequest]:
        """Get pull requests for a repository with pagination."""
        prs: list[PullRequest] = []
        async for item in self.paginate(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state},
            per_page=per_page,
        ):
            prs.append(PullRequest.model_validate(item))
        return prs

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: str | None = None,
        draft: bool = False,
    ) -> PullRequest:
        """Create a new pull request."""
        payload: dict[str, Any] = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
        }
        if body:
            payload["body"] = body

        response = await self._request(
            "POST", f"/repos/{owner}/{repo}/pulls", json=payload
        )
        return PullRequest.model_validate(response.json())

    async def get_labels(self, owner: str, repo: str) -> list[Label]:
        """Get repository labels."""
        labels: list[Label] = []
        async for item in self.paginate(f"/repos/{owner}/{repo}/labels"):
            labels.append(Label.model_validate(item))
        return labels

    async def set_labels(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        labels: list[str],
    ) -> list[Label]:
        """Set labels on a PR or issue."""
        response = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels",
            json={"labels": labels},
        )
        data = response.json()
        return [Label.model_validate(item) for item in data]

    async def compare_branches(
        self,
        owner: str,
        repo: str,
        base: str,
        head: str,
    ) -> BranchComparison:
        """Compare two branches or commits."""
        response = await self._request(
            "GET", f"/repos/{owner}/{repo}/compare/{base}...{head}"
        )
        return BranchComparison.model_validate(response.json())

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> GitHubClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
