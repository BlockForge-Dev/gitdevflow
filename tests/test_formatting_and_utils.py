"""Tests for formatting utilities, git branch helper, and CLI error paths."""

from datetime import datetime, timezone

import pytest
from typer.testing import CliRunner

from gitdevflow.cli import app
from gitdevflow.commands.pr import _get_current_git_branch, parse_repo_string
from gitdevflow.utils.formatting import format_date, slugify, truncate, utc_now

runner = CliRunner()


def test_format_date() -> None:
    """Test date formatting function."""
    dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    assert format_date(dt) == "2026-01-15"
    assert format_date(dt, "%Y/%m/%d") == "2026/01/15"


def test_utc_now() -> None:
    """Test utc_now returns a datetime with UTC tzinfo."""
    now = utc_now()
    assert isinstance(now, datetime)
    assert now.tzinfo == timezone.utc


def test_slugify() -> None:
    """Test slugify string conversion."""
    assert slugify("Hello World!") == "hello-world"
    assert slugify("  Feat: Add new API endpoint!  ") == "feat-add-new-api-endpoint"


def test_truncate() -> None:
    """Test text truncation."""
    text = "A very long commit message description that exceeds max length"
    assert truncate(text, max_length=20) == "A very long commi..."
    assert truncate("Short text", max_length=20) == "Short text"


def test_parse_repo_string_invalid() -> None:
    """Test invalid repository format raises ValueError."""
    with pytest.raises(ValueError, match="Invalid repository format"):
        parse_repo_string("invalid_repo_format")

    with pytest.raises(ValueError, match="Invalid repository format"):
        parse_repo_string("owner/")


def test_get_current_git_branch() -> None:
    """Test git branch retrieval helper."""
    branch = _get_current_git_branch()
    assert branch is None or isinstance(branch, str)


def test_pr_command_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """PR commands fail with clear message when GITHUB_TOKEN is missing."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    result = runner.invoke(
        app, ["--config", "non_existent.yaml", "pr", "list", "--repo", "owner/repo"]
    )
    assert result.exit_code == 1
    assert "GITHUB_TOKEN" in result.output


def test_pr_command_no_repo_specified(monkeypatch: pytest.MonkeyPatch) -> None:
    """PR commands fail when no repository is specified."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
    result = runner.invoke(app, ["--config", "non_existent.yaml", "pr", "list"])
    assert result.exit_code == 1
    assert "No repository specified" in result.output


def test_main_module_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test __main__.main calls Typer app."""
    import gitdevflow.__main__

    called = False

    def dummy_app() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(gitdevflow.__main__, "app", dummy_app)
    gitdevflow.__main__.main()
    assert called
