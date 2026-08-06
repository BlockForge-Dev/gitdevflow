"""Tests for CLI UX, verbose logging, error panels, and interactive wizard."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from gitdevflow.cli import app, render_error_panel
from gitdevflow.core.exceptions import (
    AuthenticationError,
    ConfigError,
    GitHubAPIError,
    NotFoundError,
    RateLimitedError,
)

runner = CliRunner()


class TestCLIUX:
    """Test suite for UX polish, Rich formatting, and error panels."""

    def test_version_command(self) -> None:
        """`gitdevflow version` prints styled version."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "gitdevflow" in result.output
        assert "0.1.0" in result.output

    def test_version_flag(self) -> None:
        """`gitdevflow --version` prints styled version and exits."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "gitdevflow" in result.output
        assert "0.1.0" in result.output

    def test_verbose_flag(self) -> None:
        """`gitdevflow --verbose` enables debug logging."""
        result = runner.invoke(app, ["--verbose", "version"])
        assert result.exit_code == 0

    def test_config_init_interactive(self, tmp_path: Path) -> None:
        """`config init` interactive wizard prompts user and writes YAML file."""
        target_path = tmp_path / ".gitdevflow.yaml"
        user_inputs = "\nghp_my_wizard_token\nmyorg/myrepo\ntype:\nrich\n"

        result = runner.invoke(
            app,
            ["config", "init", "--path", str(target_path)],
            input=user_inputs,
        )
        assert result.exit_code == 0
        assert target_path.exists()
        content = target_path.read_text(encoding="utf-8")
        assert "ghp_my_wizard_token" in content
        assert "myorg/myrepo" in content

    def test_error_panel_rendering(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify error panel renderer formats different exceptions."""
        render_error_panel(AuthenticationError("Bad credentials"))
        captured = capsys.readouterr()
        combined = captured.err + captured.out
        assert "Authentication Failed" in combined

        render_error_panel(RateLimitedError("Limit reached", retry_after=60))
        captured = capsys.readouterr()
        combined = captured.err + captured.out
        assert "Rate Limited" in combined

        render_error_panel(NotFoundError("PR #999 not found"))
        captured = capsys.readouterr()
        combined = captured.err + captured.out
        assert "Not Found" in combined

        render_error_panel(ConfigError("Invalid syntax"))
        captured = capsys.readouterr()
        combined = captured.err + captured.out
        assert "Config Error" in combined

        render_error_panel(GitHubAPIError(500, "Internal Server Error"))
        captured = capsys.readouterr()
        combined = captured.err + captured.out
        assert "API Error" in combined
