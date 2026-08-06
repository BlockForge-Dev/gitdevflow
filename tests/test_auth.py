"""Tests for gitdevflow auth login, auth status, and auth logout commands."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from gitdevflow.cli import app
from gitdevflow.core.config import AppConfig
from gitdevflow.core.exceptions import AuthenticationError
from gitdevflow.core.models import User

runner = CliRunner()


class TestAuthCLI:
    """Test suite for `gitdevflow auth` subcommands."""

    @patch("gitdevflow.commands.auth.GitHubClient.get_user", new_callable=AsyncMock)
    def test_auth_login_success(self, mock_get_user: AsyncMock, tmp_path: Path) -> None:
        """`auth login` validates token against GitHub API and saves it to config."""
        mock_get_user.return_value = User(
            id=1, login="octocat", avatar_url="https://github.com/octocat.png"
        )
        cfg_file = tmp_path / "config.yaml"

        result = runner.invoke(
            app,
            ["--config", str(cfg_file), "auth", "login"],
            input="ghp_valid_token_12345\n",
        )

        assert result.exit_code == 0
        assert "Successfully authenticated as @octocat" in result.output
        assert cfg_file.exists()

        saved_cfg = AppConfig.load(cfg_file)
        assert saved_cfg.github_token == "ghp_valid_token_12345"

    @patch("gitdevflow.commands.auth.GitHubClient.get_user", new_callable=AsyncMock)
    def test_auth_login_invalid_token(
        self, mock_get_user: AsyncMock, tmp_path: Path
    ) -> None:
        """`auth login` fails if token is invalid or expired."""
        mock_get_user.side_effect = AuthenticationError("Bad credentials")
        cfg_file = tmp_path / "config.yaml"

        result = runner.invoke(
            app,
            ["--config", str(cfg_file), "auth", "login"],
            input="ghp_invalid_token\n",
        )

        assert result.exit_code == 1
        assert "Authentication Failed" in result.output

    @patch("gitdevflow.commands.auth.GitHubClient.get_user", new_callable=AsyncMock)
    def test_auth_status_logged_in(
        self, mock_get_user: AsyncMock, tmp_path: Path
    ) -> None:
        """`auth status` displays authenticated user when token is valid."""
        mock_get_user.return_value = User(
            id=1, login="octocat", avatar_url="https://github.com/octocat.png"
        )
        cfg_file = tmp_path / "config.yaml"
        AppConfig(github_token="ghp_valid_token_12345").save(cfg_file)

        result = runner.invoke(app, ["--config", str(cfg_file), "auth", "status"])

        assert result.exit_code == 0
        assert "Logged in" in result.output
        assert "@octocat" in result.output

    def test_auth_status_not_logged_in(self, tmp_path: Path) -> None:
        """`auth status` informs user when no token is present."""
        cfg_file = tmp_path / "empty_config.yaml"
        AppConfig(github_token=None).save(cfg_file)

        result = runner.invoke(app, ["--config", str(cfg_file), "auth", "status"])

        assert result.exit_code == 0
        assert "Not logged in" in result.output

    def test_auth_logout(self, tmp_path: Path) -> None:
        """`auth logout` removes stored token from config file."""
        cfg_file = tmp_path / "config.yaml"
        AppConfig(github_token="ghp_token_to_remove").save(cfg_file)

        result = runner.invoke(app, ["--config", str(cfg_file), "auth", "logout"])

        assert result.exit_code == 0
        assert "Successfully logged out" in result.output

        saved_cfg = AppConfig.load(cfg_file)
        assert saved_cfg.github_token is None
