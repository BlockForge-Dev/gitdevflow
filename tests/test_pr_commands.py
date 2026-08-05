"""Tests for PR management commands."""

from typer.testing import CliRunner

from gitdevflow.cli import app

runner = CliRunner()


class TestPRCommands:
    """Test PR CLI commands."""

    def test_pr_create_help(self) -> None:
        """PR create should display help text."""
        result = runner.invoke(app, ["pr", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new pull request" in result.output

    def test_pr_list_help(self) -> None:
        """PR list should display help text."""
        result = runner.invoke(app, ["pr", "list", "--help"])
        assert result.exit_code == 0
        assert "List pull requests" in result.output

    def test_pr_merge_help(self) -> None:
        """PR merge should display help text."""
        result = runner.invoke(app, ["pr", "merge", "--help"])
        assert result.exit_code == 0
        assert "Merge a pull request" in result.output
