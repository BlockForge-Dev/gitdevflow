"""Tests for configuration loading, YAML parsing, env overrides, and CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from gitdevflow.cli import app
from gitdevflow.core.config import AppConfig, load_config
from gitdevflow.core.exceptions import ConfigError

runner = CliRunner()


class TestAppConfig:
    """Test the AppConfig model and loader."""

    def test_default_config(self) -> None:
        """Default config should have sensible defaults."""
        config = AppConfig()
        assert config.github_token is None
        assert config.default_repo is None
        assert config.pr_label_prefix == "type:"
        assert config.output_format == "rich"
        assert "Features" in config.changelog_sections

    def test_load_yaml_config(self, tmp_path: Path) -> None:
        """Load settings from a YAML file."""
        yaml_content = """
github_token: "ghp_yaml_token_123456789"
default_repo: "owner/myrepo"
pr_label_prefix: "label:"
output_format: "plain"
changelog_sections:
  Features:
    - feat
"""
        cfg_file = tmp_path / ".gitdevflow.yaml"
        cfg_file.write_text(yaml_content, encoding="utf-8")

        config = AppConfig.load(cfg_file)
        assert config.github_token == "ghp_yaml_token_123456789"
        assert config.default_repo == "owner/myrepo"
        assert config.pr_label_prefix == "label:"
        assert config.output_format == "plain"
        assert config.changelog_sections == {"Features": ["feat"]}

    def test_env_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables should override YAML settings."""
        yaml_content = """
github_token: "ghp_yaml_token"
default_repo: "yaml-owner/yaml-repo"
"""
        cfg_file = tmp_path / ".gitdevflow.yaml"
        cfg_file.write_text(yaml_content, encoding="utf-8")

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_env_token_override")

        config = AppConfig.load(cfg_file)
        assert config.github_token == "ghp_env_token_override"
        assert config.default_repo == "yaml-owner/yaml-repo"

    def test_missing_file_fallback(self, tmp_path: Path) -> None:
        """Non-existent config file should fall back to defaults gracefully."""
        non_existent = tmp_path / "does_not_exist.yaml"
        config = load_config(non_existent)
        assert isinstance(config, AppConfig)
        assert config.pr_label_prefix == "type:"

    def test_invalid_yaml_raises_config_error(self, tmp_path: Path) -> None:
        """Invalid YAML syntax should raise ConfigError."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("invalid: : : yaml", encoding="utf-8")

        with pytest.raises(ConfigError):
            AppConfig.load(bad_yaml)

    def test_masked_token(self) -> None:
        """Test token masking for display."""
        cfg_no_token = AppConfig(github_token=None)
        assert cfg_no_token.masked_token() == "[Not Set]"

        cfg_short_token = AppConfig(github_token="1234")
        assert cfg_short_token.masked_token() == "****"

        cfg_long_token = AppConfig(github_token="ghp_1234567890abcdef")
        assert cfg_long_token.masked_token() == "ghp_...cdef"


class TestConfigCLI:
    """Test `gitdevflow config` CLI commands."""

    def test_config_show(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """`config show` displays configuration with token masked."""
        cfg_file = tmp_path / "config.yaml"
        cfg_content = "default_repo: 'org/repo'\noutput_format: 'plain'"
        cfg_file.write_text(cfg_content, encoding="utf-8")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret_token_12345")

        result = runner.invoke(app, ["--config", str(cfg_file), "config", "show"])
        assert result.exit_code == 0
        assert "org/repo" in result.output
        assert "ghp_...2345" in result.output
        assert "ghp_secret_token_12345" not in result.output

    def test_config_validate_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`config validate` succeeds when token is present."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        result = runner.invoke(app, ["config", "validate"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_config_validate_missing_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`config validate` fails when required token is missing."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        result = runner.invoke(
            app, ["--config", "non_existent.yaml", "config", "validate"]
        )
        assert result.exit_code == 1
        assert "missing" in result.output.lower()

    def test_config_init(self, tmp_path: Path) -> None:
        """`config init` creates a new config file."""
        target_path = tmp_path / "new_config.yaml"
        result = runner.invoke(
            app, ["config", "init", "--path", str(target_path), "--non-interactive"]
        )
        assert result.exit_code == 0
        assert target_path.exists()
        assert "github_token" in target_path.read_text(encoding="utf-8")

    def test_config_init_already_exists(self, tmp_path: Path) -> None:
        """`config init` fails if target config file already exists."""
        target_path = tmp_path / "existing.yaml"
        target_path.write_text("github_token: foo", encoding="utf-8")
        result = runner.invoke(
            app, ["config", "init", "--path", str(target_path), "--non-interactive"]
        )
        assert result.exit_code == 1
        assert "already exists" in result.output.lower()

    def test_config_show_rich(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`config show` renders Rich table when output_format is rich."""
        cfg_file = tmp_path / "config.yaml"
        cfg_content = "default_repo: 'org/repo'\noutput_format: 'rich'"
        cfg_file.write_text(cfg_content, encoding="utf-8")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret_token_12345")

        result = runner.invoke(app, ["--config", str(cfg_file), "config", "show"])
        assert result.exit_code == 0
        assert "org/repo" in result.output
        assert "ghp_...2345" in result.output
