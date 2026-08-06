"""Tests for gitdevflow repo use, repo show, and repo list commands."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from gitdevflow.cli import app
from gitdevflow.core.config import AppConfig
from gitdevflow.core.models import Repository, User

runner = CliRunner()


class TestRepoCLI:
    """Test suite for `gitdevflow repo` subcommands."""

    def test_repo_show_configured(self, tmp_path: Path) -> None:
        """`repo show` displays configured default_repo."""
        cfg_file = tmp_path / "config.yaml"
        AppConfig(default_repo="owner/myrepo").save(cfg_file)

        result = runner.invoke(app, ["--config", str(cfg_file), "repo", "show"])
        assert result.exit_code == 0
        assert "owner/myrepo" in result.output

    def test_repo_show_unset(self, tmp_path: Path) -> None:
        """`repo show` displays warning message when default_repo is unset."""
        cfg_file = tmp_path / "config.yaml"
        AppConfig(default_repo=None).save(cfg_file)

        result = runner.invoke(app, ["--config", str(cfg_file), "repo", "show"])
        assert result.exit_code == 0
        assert "No default repository configured" in result.output

    def test_repo_use_direct_argument(self, tmp_path: Path) -> None:
        """`repo use owner/repo` sets default_repo directly."""
        cfg_file = tmp_path / "config.yaml"
        AppConfig(default_repo=None).save(cfg_file)

        result = runner.invoke(
            app, ["--config", str(cfg_file), "repo", "use", "owner/newrepo"]
        )
        assert result.exit_code == 0
        assert "Default repository set to owner/newrepo" in result.output

        saved_cfg = AppConfig.load(cfg_file)
        assert saved_cfg.default_repo == "owner/newrepo"

    @patch("gitdevflow.commands.repo.select_repo", new_callable=AsyncMock)
    def test_repo_use_interactive(
        self, mock_select: AsyncMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`repo use` launches select_repo picker when argument is omitted."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        mock_select.return_value = "owner/chosen_repo"
        cfg_file = tmp_path / "config.yaml"
        AppConfig(github_token="ghp_test_token", default_repo=None).save(cfg_file)

        result = runner.invoke(app, ["--config", str(cfg_file), "repo", "use"])
        assert result.exit_code == 0
        assert "Default repository set to owner/chosen_repo" in result.output

        saved_cfg = AppConfig.load(cfg_file)
        assert saved_cfg.default_repo == "owner/chosen_repo"

    @patch(
        "gitdevflow.commands.repo.GitHubClient.list_user_repos", new_callable=AsyncMock
    )
    def test_repo_list_subcommand(
        self,
        mock_list_repos: AsyncMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """`repo list` displays user repositories in a Rich table."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        user = User(id=1, login="owner", avatar_url="https://github.com/owner.png")
        mock_list_repos.return_value = [
            Repository(
                id=1,
                name="repo1",
                full_name="owner/repo1",
                owner=user,
                private=False,
                default_branch="main",
                html_url="https://github.com/owner/repo1",
            ),
            Repository(
                id=2,
                name="repo2",
                full_name="owner/repo2",
                owner=user,
                private=True,
                default_branch="main",
                html_url="https://github.com/owner/repo2",
            ),
        ]
        cfg_file = tmp_path / "config.yaml"
        AppConfig(github_token="ghp_test_token", default_repo="owner/repo1").save(
            cfg_file
        )

        result = runner.invoke(app, ["--config", str(cfg_file), "repo", "list"])
        assert result.exit_code == 0
        assert "Accessible GitHub Repositories" in result.output
        assert "owner/repo1" in result.output
        assert "owner/repo2" in result.output
        assert "★" in result.output
