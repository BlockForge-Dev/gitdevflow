"""Interactive prompt utilities using questionary and Rich."""

from __future__ import annotations

import questionary

from gitdevflow.core.github_client import GitHubClient
from gitdevflow.utils.console import error_console


async def select_repo(token: str, default: str | None = None) -> str | None:
    """Interactively search and select a repository from accessible user repos.

    Args:
        token: GitHub Personal Access Token.
        default: Optional default repository full_name ('owner/repo') to preselect.

    Returns:
        Selected repository full_name string (e.g. 'owner/repo') or None if cancelled.
    """
    async with GitHubClient(token=token) as client:
        try:
            repos = await client.list_user_repos()
        except Exception as err:
            error_console.print(f"[bold red]Failed to fetch repositories:[/] {err}")
            return None

    if not repos:
        error_console.print(
            "[yellow]No accessible repositories found for your account.[/]"
        )
        return None

    repo_names = [repo.full_name for repo in repos]

    # Pre-select default if present in list
    default_choice = (
        default if default in repo_names else (repo_names[0] if repo_names else None)
    )

    try:
        selection: str | None = questionary.select(
            "Choose a repository:",
            choices=repo_names,
            default=default_choice,
        ).ask()
        return selection
    except Exception:
        return None
