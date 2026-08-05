"""Tests for changelog generation and validation commands."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from typer.testing import CliRunner

from gitdevflow.cli import app

runner = CliRunner()


class TestChangelogCommands:
    """Test suite for `gitdevflow changelog` subcommands."""

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

    @respx.mock
    def test_changelog_generate_markdown_stdout(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_compare_data: dict[str, Any],
        mock_pr_response: dict[str, Any],
    ) -> None:
        """`changelog generate` outputs formatted Markdown to stdout."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        compare_url = (
            "https://api.github.com/repos/octocat/Hello-World/compare/v0.1.0...HEAD"
        )
        respx.get(compare_url).mock(
            return_value=httpx.Response(200, json=mock_compare_data)
        )
        pr_commit_url = (
            "https://api.github.com/repos/octocat/Hello-World/commits/"
            "6dcb09b5b57875f334f61aebed695e2e4193db5e/pulls?per_page=30"
        )
        respx.get(pr_commit_url).mock(
            return_value=httpx.Response(200, json=[mock_pr_response])
        )

        result = runner.invoke(
            app,
            [
                "changelog",
                "generate",
                "--repo",
                "octocat/Hello-World",
                "--from-ref",
                "v0.1.0",
                "--output",
                "-",
            ],
        )
        assert result.exit_code == 0
        assert "## [HEAD]" in result.output
        assert "### Features" in result.output
        assert "Add feature X" in result.output
        assert "[#42]" in result.output

    @respx.mock
    def test_changelog_generate_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_compare_data: dict[str, Any],
        mock_pr_response: dict[str, Any],
    ) -> None:
        """`changelog generate --format json` outputs structured JSON."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        compare_url = (
            "https://api.github.com/repos/octocat/Hello-World/compare/v0.1.0...HEAD"
        )
        respx.get(compare_url).mock(
            return_value=httpx.Response(200, json=mock_compare_data)
        )
        pr_commit_url = (
            "https://api.github.com/repos/octocat/Hello-World/commits/"
            "6dcb09b5b57875f334f61aebed695e2e4193db5e/pulls?per_page=30"
        )
        respx.get(pr_commit_url).mock(
            return_value=httpx.Response(200, json=[mock_pr_response])
        )

        result = runner.invoke(
            app,
            [
                "changelog",
                "generate",
                "--repo",
                "octocat/Hello-World",
                "--output",
                "-",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["from_ref"] == "v0.1.0"
        assert "Features" in data["categories"]
        assert data["categories"]["Features"][0]["number"] == 42

    @respx.mock
    def test_changelog_generate_to_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_compare_data: dict[str, Any],
        mock_pr_response: dict[str, Any],
    ) -> None:
        """`changelog generate` writes output to a file."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        out_file = tmp_path / "CHANGELOG.md"
        compare_url = (
            "https://api.github.com/repos/octocat/Hello-World/compare/v0.1.0...HEAD"
        )
        respx.get(compare_url).mock(
            return_value=httpx.Response(200, json=mock_compare_data)
        )
        pr_commit_url = (
            "https://api.github.com/repos/octocat/Hello-World/commits/"
            "6dcb09b5b57875f334f61aebed695e2e4193db5e/pulls?per_page=30"
        )
        respx.get(pr_commit_url).mock(
            return_value=httpx.Response(200, json=[mock_pr_response])
        )

        result = runner.invoke(
            app,
            [
                "changelog",
                "generate",
                "--repo",
                "octocat/Hello-World",
                "--output",
                str(out_file),
            ],
        )
        assert result.exit_code == 0
        assert out_file.exists()
        text = out_file.read_text(encoding="utf-8")
        assert "Add feature X" in text

    @respx.mock
    def test_changelog_generate_not_found(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`changelog generate` handles 404 for non-existent refs gracefully."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_1234")
        compare_url = "https://api.github.com/repos/octocat/Hello-World/compare/invalid_tag...HEAD"
        respx.get(compare_url).mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )

        result = runner.invoke(
            app,
            [
                "changelog",
                "generate",
                "--repo",
                "octocat/Hello-World",
                "--from-ref",
                "invalid_tag",
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_changelog_validate_success(self, tmp_path: Path) -> None:
        """`changelog validate` passes for valid CHANGELOG file."""
        cl_file = tmp_path / "CHANGELOG.md"
        cl_file.write_text(
            "# Changelog\n\n## [v1.0.0] - 2026-01-01\n- Initial release\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["changelog", "validate", "--path", str(cl_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_changelog_validate_invalid(self, tmp_path: Path) -> None:
        """`changelog validate` fails when required headers are missing."""
        cl_file = tmp_path / "CHANGELOG.md"
        cl_file.write_text("No heading here", encoding="utf-8")
        result = runner.invoke(app, ["changelog", "validate", "--path", str(cl_file)])
        assert result.exit_code == 1
        assert "Missing" in result.output
