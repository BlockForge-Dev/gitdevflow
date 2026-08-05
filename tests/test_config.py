"""Tests for configuration loading and validation."""

from pathlib import Path

from gitdevflow.core.config import AppConfig, load_config


class TestAppConfig:
    """Test the AppConfig model."""

    def test_default_config(self) -> None:
        """Default config should have sensible defaults."""
        config = AppConfig()
        assert config.github.owner == ""
        assert config.pr.default_base == "main"
        assert config.changelog.output == "CHANGELOG.md"

    def test_load_config_returns_app_config(self, tmp_config: Path) -> None:
        """load_config should return an AppConfig instance."""
        config = load_config(tmp_config)
        assert isinstance(config, AppConfig)
