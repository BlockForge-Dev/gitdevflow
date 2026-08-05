"""Pydantic settings loaded from YAML configuration and environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_PATH = Path.home() / ".gitdevflow.yaml"


class AppConfig(BaseSettings):
    """Application configuration with YAML and environment variable support."""

    github_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GITHUB_TOKEN", "github_token"),
    )
    default_repo: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DEFAULT_REPO", "default_repo"),
    )
    pr_label_prefix: str = Field(
        default="type:",
        validation_alias=AliasChoices("PR_LABEL_PREFIX", "pr_label_prefix"),
    )
    changelog_sections: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "Features": ["feat", "enhancement"],
            "Bug Fixes": ["fix", "bug"],
            "Documentation": ["docs", "documentation"],
        }
    )
    output_format: Literal["rich", "plain"] = Field(
        default="rich",
        validation_alias=AliasChoices("OUTPUT_FORMAT", "output_format"),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def load(cls, path: str | Path | None = None) -> AppConfig:
        """Load configuration from a YAML file overlaid with environment variables.

        Args:
            path: Optional custom path to YAML config file.

        Returns:
            Populated AppConfig instance.
        """
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        yaml_data: dict[str, Any] = {}

        if config_path.is_file():
            try:
                with open(config_path, encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    if isinstance(content, dict):
                        yaml_data = content
            except Exception as err:
                from gitdevflow.core.exceptions import ConfigError

                raise ConfigError(
                    f"Failed to parse config file {config_path}: {err}"
                ) from err

        # Environment variables override YAML values (12-factor app rule)
        for key in list(yaml_data.keys()):
            upper_key = key.upper()
            if upper_key in os.environ:
                yaml_data[key] = os.environ[upper_key]
            elif key in os.environ:
                yaml_data[key] = os.environ[key]

        return cls(**yaml_data)

    def masked_token(self) -> str:
        """Return masked version of the GitHub token for safe display."""
        if not self.github_token:
            return "[Not Set]"
        token = self.github_token.strip()
        if len(token) <= 8:
            return "****"
        return f"{token[:4]}...{token[-4:]}"

    def to_dict(self, mask_sensitive: bool = True) -> dict[str, Any]:
        """Convert config to dictionary format with optional token masking."""
        data = self.model_dump()
        if mask_sensitive:
            data["github_token"] = self.masked_token()
        return data


def load_config(path: str | Path | None = None) -> AppConfig:
    """Convenience wrapper around AppConfig.load."""
    return AppConfig.load(path)
