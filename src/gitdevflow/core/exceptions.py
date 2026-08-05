"""Custom exception hierarchy for gitdevflow."""

from __future__ import annotations


class GitDevFlowError(Exception):
    """Base exception for all gitdevflow errors."""


class ConfigError(GitDevFlowError):
    """Raised when configuration is invalid or missing."""


class GitHubAPIError(GitDevFlowError):
    """Base exception for GitHub REST API errors."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API Error [{status_code}]: {message}")


class AuthenticationError(GitHubAPIError):
    """Raised when GitHub API authentication fails (HTTP 401)."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(status_code=401, message=message)


class RateLimitedError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded (HTTP 429 / 403)."""

    def __init__(
        self,
        message: str = "GitHub API rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(status_code=429, message=message)


class NotFoundError(GitHubAPIError):
    """Raised when a requested GitHub resource is not found (HTTP 404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(status_code=404, message=message)
