"""Pydantic settings loaded from YAML config and environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

DEFAULT_CONFIG_PATH = Path(".gitdevflow.yml")


class GitHubSettings(BaseSettings):
    """GitHub-related configuration."""

    owner: str = ""
    repo: str = ""
    token: str = Field(default="", alias="GITHUB_TOKEN")


class PRSettings(BaseSettings):
    """Pull request defaults."""

    default_base: str = "main"
    template: str | None = None
    labels: list[str] = Field(default_factory=list)


class ChangelogSettings(BaseSettings):
    """Changelog generation settings."""

    output: str = "CHANGELOG.md"
    group_by_labels: bool = True


class AppConfig(BaseSettings):
    """Root application configuration."""

    github: GitHubSettings = Field(default_factory=GitHubSettings)
    pr: PRSettings = Field(default_factory=PRSettings)
    changelog: ChangelogSettings = Field(default_factory=ChangelogSettings)


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load configuration from YAML file with env overrides.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Parsed AppConfig instance.
    """
    # TODO: Implement YAML loading + merge with env vars
    return AppConfig()
