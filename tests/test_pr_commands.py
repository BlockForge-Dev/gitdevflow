"""Tests for PR management commands (list, check, label, create, merge)."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from typer.testing import CliRunner

from gitdevflow.cli import app

runner = CliRunner()


class TestPRCommands:
    """Test suite for `gitdevflow pr` subcommands."""

    @respx.mock
    def test_pr_list_table(
        self, monkeypatch: pytest.MonkeyPatch, mock_pr_response: dict[str, Any]
    ) -> None:
        """`pr list` displays pull requests in a formatted table."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        url = "https://api.github.com/repos/octocat/Hello-World/pulls?state=open&per_page=30"
        respx.get(url).mock(return_value=httpx.Response(200, json=[mock_pr_response]))

        result = runner.invoke(app, ["pr", "list", "--repo", "octocat/Hello-World"])
        assert result.exit_code == 0
        assert "#42" in result.output
        assert "Add feature X" in result.output
        assert "octocat" in result.output

    @respx.mock
    def test_pr_list_default_repo_fallback(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_pr_response: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """`pr list` uses config.default_repo when --repo is omitted."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        cfg_file = tmp_path / "config.yaml"
        from gitdevflow.core.config import AppConfig

        AppConfig(
            github_token="ghp_test_token_1234", default_repo="octocat/Hello-World"
        ).save(cfg_file)

        url = "https://api.github.com/repos/octocat/Hello-World/pulls?state=open&per_page=30"
        respx.get(url).mock(return_value=httpx.Response(200, json=[mock_pr_response]))

        result = runner.invoke(app, ["--config", str(cfg_file), "pr", "list"])
        assert result.exit_code == 0
        assert "#42" in result.output

    @respx.mock
    def test_pr_list_json(
        self, monkeypatch: pytest.MonkeyPatch, mock_pr_response: dict[str, Any]
    ) -> None:
        """`pr list --json` outputs raw JSON array."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        url = "https://api.github.com/repos/octocat/Hello-World/pulls?state=open&per_page=30"
        respx.get(url).mock(return_value=httpx.Response(200, json=[mock_pr_response]))

        result = runner.invoke(
            app, ["pr", "list", "--repo", "octocat/Hello-World", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["number"] == 42

    @respx.mock
    def test_pr_check_valid(
        self, monkeypatch: pytest.MonkeyPatch, mock_pr_response: dict[str, Any]
    ) -> None:
        """`pr check` succeeds when PR title and body comply with conventions."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        valid_pr = {
            **mock_pr_response,
            "title": "feat: add user authentication",
            "body": "Detailed description of user authentication feature.",
            "head": {"ref": "feat/user-auth", "sha": "123456"},
        }
        url = "https://api.github.com/repos/octocat/Hello-World/pulls?state=open&per_page=30"
        respx.get(url).mock(return_value=httpx.Response(200, json=[valid_pr]))

        result = runner.invoke(app, ["pr", "check", "--repo", "octocat/Hello-World"])
        assert result.exit_code == 0
        assert "Passed" in result.output

    @respx.mock
    def test_pr_check_violations(
        self, monkeypatch: pytest.MonkeyPatch, mock_pr_response: dict[str, Any]
    ) -> None:
        """`pr check` fails (exit code 1) when PR title or body violates rules."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        invalid_pr = {
            **mock_pr_response,
            "title": "bad title without conventional commit prefix",
            "body": "short",
        }
        url = "https://api.github.com/repos/octocat/Hello-World/pulls?state=open&per_page=30"
        respx.get(url).mock(return_value=httpx.Response(200, json=[invalid_pr]))

        result = runner.invoke(app, ["pr", "check", "--repo", "octocat/Hello-World"])
        assert result.exit_code == 1
        assert "Conventional Commits" in result.output
        assert "short" in result.output or "minimum 10 characters" in result.output

    @respx.mock
    def test_pr_label(
        self, monkeypatch: pytest.MonkeyPatch, mock_pr_response: dict[str, Any]
    ) -> None:
        """`pr label` auto-labels PR based on branch and title rules."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        pr_unlabeled = {
            **mock_pr_response,
            "title": "fix: resolve memory leak",
            "labels": [],
            "head": {"ref": "fix/memory-leak", "sha": "123456"},
        }
        url = "https://api.github.com/repos/octocat/Hello-World/pulls?state=open&per_page=30"
        respx.get(url).mock(return_value=httpx.Response(200, json=[pr_unlabeled]))
        label_url = "https://api.github.com/repos/octocat/Hello-World/issues/42/labels"
        respx.post(label_url).mock(
            return_value=httpx.Response(200, json=[{"name": "bug"}])
        )

        result = runner.invoke(app, ["pr", "label", "--repo", "octocat/Hello-World"])
        assert result.exit_code == 0
        assert "Auto-labeled" in result.output
        assert "bug" in result.output

    @respx.mock
    def test_pr_create(
        self, monkeypatch: pytest.MonkeyPatch, mock_pr_response: dict[str, Any]
    ) -> None:
        """`pr create` sends creation request to GitHub."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        respx.post("https://api.github.com/repos/octocat/Hello-World/pulls").mock(
            return_value=httpx.Response(201, json=mock_pr_response)
        )

        result = runner.invoke(
            app,
            [
                "pr",
                "create",
                "--repo",
                "octocat/Hello-World",
                "--title",
                "Add feature X",
                "--head",
                "feature-branch",
                "--base",
                "main",
                "--body",
                "Implementation details for feature X",
            ],
        )
        assert result.exit_code == 0
        assert "Created Pull Request #42" in result.output

    def test_pr_create_invalid_repo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`pr create` fails when owner/repo format is invalid."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        result = runner.invoke(
            app,
            ["pr", "create", "--repo", "invalidrepoformat", "--title", "Test"],
        )
        assert result.exit_code == 1
        assert "Invalid repository format" in result.output

    @respx.mock
    def test_pr_merge(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`pr merge` calls GitHub API to merge pull request."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        merge_url = "https://api.github.com/repos/octocat/Hello-World/pulls/42/merge"
        respx.put(merge_url).mock(
            return_value=httpx.Response(
                200,
                json={
                    "sha": "6dcb09b",
                    "merged": True,
                    "message": "Pull Request successfully merged",
                },
            )
        )

        result = runner.invoke(
            app, ["pr", "merge", "42", "--repo", "octocat/Hello-World"]
        )
        assert result.exit_code == 0
        assert "PR #42 merged" in result.output

    @respx.mock
    def test_pr_check_specific_pr_not_found(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`pr check --pr 999` displays error when PR is not found."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        url = "https://api.github.com/repos/octocat/Hello-World/pulls?state=all&per_page=30"
        respx.get(url).mock(return_value=httpx.Response(200, json=[]))

        result = runner.invoke(
            app, ["pr", "check", "--repo", "octocat/Hello-World", "--pr", "999"]
        )
        assert result.exit_code == 1
        assert "PR #999 not found" in result.output

    @respx.mock
    def test_pr_check_no_prs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`pr check` displays warning when no PRs are present."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        url = "https://api.github.com/repos/octocat/Hello-World/pulls?state=open&per_page=30"
        respx.get(url).mock(return_value=httpx.Response(200, json=[]))

        result = runner.invoke(app, ["pr", "check", "--repo", "octocat/Hello-World"])
        assert result.exit_code == 0
        assert "No pull requests to check" in result.output

    @respx.mock
    def test_pr_label_no_updates(
        self, monkeypatch: pytest.MonkeyPatch, mock_pr_response: dict[str, Any]
    ) -> None:
        """`pr label` outputs message when no PRs need label updates."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        pr_already_labeled = {
            **mock_pr_response,
            "title": "fix: resolve memory leak",
            "labels": [{"name": "bug"}],
            "head": {"ref": "fix/memory-leak", "sha": "123456"},
        }
        url = "https://api.github.com/repos/octocat/Hello-World/pulls?state=open&per_page=30"
        respx.get(url).mock(return_value=httpx.Response(200, json=[pr_already_labeled]))

        result = runner.invoke(app, ["pr", "label", "--repo", "octocat/Hello-World"])
        assert result.exit_code == 0
        assert "No PRs required label updates" in result.output

    @respx.mock
    def test_pr_merge_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`pr merge` displays error when GitHub API fails."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        merge_url = "https://api.github.com/repos/octocat/Hello-World/pulls/42/merge"
        respx.put(merge_url).mock(
            return_value=httpx.Response(
                405, json={"message": "Pull Request is not mergeable"}
            )
        )

        result = runner.invoke(
            app, ["pr", "merge", "42", "--repo", "octocat/Hello-World"]
        )
        assert result.exit_code == 1
        assert "Failed to merge PR" in result.output
