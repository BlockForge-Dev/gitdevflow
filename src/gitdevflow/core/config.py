"""Pydantic settings loaded from YAML configuration and environment variables."""

from __future__ import annotations

import os
import stat
from contextlib import suppress
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "gitdevflow" / "config.yaml"
LEGACY_CONFIG_PATH = Path.home() / ".gitdevflow.yaml"


class AppConfig(BaseSettings):
    """Application configuration with YAML and environment variable support."""

    github_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "GITDEVFLOW_GITHUB_TOKEN", "GITHUB_TOKEN", "github_token"
        ),
    )

    @field_validator("github_token", mode="before")
    @classmethod
    def sanitize_token(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            cleaned = "".join(c for c in v if 32 <= ord(c) <= 126).strip()
            return cleaned if cleaned else None
        return v

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

    def save(self, path: str | Path | None = None) -> Path:
        """Save configuration to YAML file with strict file permissions (0o600).

        Args:
            path: Optional destination path.

        Returns:
            The Path object where configuration was written.
        """
        target_path = Path(path) if path else DEFAULT_CONFIG_PATH
        target_path.parent.mkdir(parents=True, exist_ok=True)

        data = self.model_dump()
        yaml_content = yaml.safe_dump(data, sort_keys=False)
        target_path.write_text(yaml_content, encoding="utf-8")

        with suppress(OSError, NotImplementedError):
            os.chmod(target_path, 0o600)

        return target_path

    @classmethod
    def load(cls, path: str | Path | None = None) -> AppConfig:
        """Load configuration from a YAML file overlaid with environment variables.

        Args:
            path: Optional custom path to YAML config file.

        Returns:
            Populated AppConfig instance.
        """
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        if not config_path.is_file() and not path and LEGACY_CONFIG_PATH.is_file():
            config_path = LEGACY_CONFIG_PATH

        yaml_data: dict[str, Any] = {}

        if config_path.is_file():
            # Check file permissions on POSIX systems
            try:
                if os.name == "posix":
                    st = config_path.stat()
                    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO) != 0:
                        from gitdevflow.utils.console import error_console

                        error_console.print(
                            f"[bold yellow]Warning:[/] Config file '{config_path}' "
                            "permissions are too open. Run 'chmod 600 "
                            f"{config_path}' to secure it."
                        )
            except Exception:
                pass

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
            elif f"GITDEVFLOW_{upper_key}" in os.environ:
                yaml_data[key] = os.environ[f"GITDEVFLOW_{upper_key}"]
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
