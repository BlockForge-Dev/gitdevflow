"""Tests for changelog generation."""

from typer.testing import CliRunner

from gitdevflow.cli import app

runner = CliRunner()


class TestChangelogCommands:
    """Test changelog CLI commands."""

    def test_changelog_generate_help(self) -> None:
        """Changelog generate should display help text."""
        result = runner.invoke(app, ["changelog", "generate", "--help"])
        assert result.exit_code == 0
        assert "Generate a changelog" in result.output

    def test_changelog_validate_help(self) -> None:
        """Changelog validate should display help text."""
        result = runner.invoke(app, ["changelog", "validate", "--help"])
        assert result.exit_code == 0
        assert "Validate" in result.output
