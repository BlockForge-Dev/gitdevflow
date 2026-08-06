"""Tests for interactive prompts and repository selection utility."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gitdevflow.core.models import Repository, User
from gitdevflow.utils.prompts import select_repo


class TestPrompts:
    """Test suite for interactive prompt helpers."""

    @pytest.mark.asyncio
    @patch("gitdevflow.utils.prompts.questionary.select")
    @patch(
        "gitdevflow.utils.prompts.GitHubClient.list_user_repos", new_callable=AsyncMock
    )
    async def test_select_repo_success(
        self, mock_list_repos: AsyncMock, mock_select: MagicMock
    ) -> None:
        """select_repo returns chosen repository string from questionary."""
        user = User(id=1, login="owner", avatar_url="https://github.com/owner.png")
        mock_list_repos.return_value = [
            Repository(
                id=1,
                name="repo1",
                full_name="owner/repo1",
                owner=user,
                html_url="https://github.com/owner/repo1",
            ),
            Repository(
                id=2,
                name="repo2",
                full_name="owner/repo2",
                owner=user,
                html_url="https://github.com/owner/repo2",
            ),
        ]
        mock_question = MagicMock()
        mock_question.ask.return_value = "owner/repo2"
        mock_select.return_value = mock_question

        result = await select_repo(token="ghp_test_token")
        assert result == "owner/repo2"
        mock_select.assert_called_once()

    @pytest.mark.asyncio
    @patch("gitdevflow.utils.prompts.questionary.select")
    @patch(
        "gitdevflow.utils.prompts.GitHubClient.list_user_repos", new_callable=AsyncMock
    )
    async def test_select_repo_cancelled(
        self, mock_list_repos: AsyncMock, mock_select: MagicMock
    ) -> None:
        """select_repo returns None if user cancels selection."""
        user = User(id=1, login="owner", avatar_url="https://github.com/owner.png")
        mock_list_repos.return_value = [
            Repository(
                id=1,
                name="repo1",
                full_name="owner/repo1",
                owner=user,
                html_url="https://github.com/owner/repo1",
            ),
        ]
        mock_question = MagicMock()
        mock_question.ask.return_value = None
        mock_select.return_value = mock_question

        result = await select_repo(token="ghp_test_token")
        assert result is None

    @pytest.mark.asyncio
    @patch(
        "gitdevflow.utils.prompts.GitHubClient.list_user_repos", new_callable=AsyncMock
    )
    async def test_select_repo_empty(self, mock_list_repos: AsyncMock) -> None:
        """select_repo returns None when no repositories are returned."""
        mock_list_repos.return_value = []
        result = await select_repo(token="ghp_test_token")
        assert result is None
