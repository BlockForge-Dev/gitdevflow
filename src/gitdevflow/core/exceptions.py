"""Custom exceptions for gitdevflow."""


class GitDevFlowError(Exception):
    """Base exception for all gitdevflow errors."""


class ConfigError(GitDevFlowError):
    """Raised when configuration is invalid or missing."""


class GitHubAPIError(GitDevFlowError):
    """Raised when a GitHub API call fails."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"GitHub API error ({status_code}): {message}")


class AuthenticationError(GitHubAPIError):
    """Raised when authentication with GitHub fails."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(status_code=401, message=message)
