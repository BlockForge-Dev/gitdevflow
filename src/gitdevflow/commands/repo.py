"""Repository management commands — use, show, list."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.table import Table

from gitdevflow.commands.pr import parse_repo_string
from gitdevflow.core.config import DEFAULT_CONFIG_PATH, AppConfig
from gitdevflow.core.github_client import GitHubClient
from gitdevflow.utils.console import console, error_console
from gitdevflow.utils.prompts import select_repo

app = typer.Typer()


def _get_config(ctx: typer.Context) -> AppConfig:
    """Retrieve AppConfig from Typer context or load default."""
    if ctx.obj and "config" in ctx.obj and isinstance(ctx.obj["config"], AppConfig):
        return ctx.obj["config"]
    return AppConfig.load()


def _get_config_path(ctx: typer.Context) -> Path:
    """Retrieve config Path from Typer context or return default."""
    if (
        ctx.obj
        and "config_path" in ctx.obj
        and isinstance(ctx.obj["config_path"], Path)
    ):
        return ctx.obj["config_path"]
    return DEFAULT_CONFIG_PATH


@app.command()
def use(
    ctx: typer.Context,
    repository: str | None = typer.Argument(
        None, help="Repository in 'owner/name' format. Omit for interactive selection."
    ),
) -> None:
    """Set the default repository interactively or via argument."""
    cfg = _get_config(ctx)
    cfg_path = _get_config_path(ctx)

    if repository:
        try:
            owner, name = parse_repo_string(repository)
            chosen_repo = f"{owner}/{name}"
        except ValueError as err:
            error_console.print(f"[bold red]Error:[/] {err}")
            raise typer.Exit(code=1) from err
    else:
        if not cfg.github_token:
            error_console.print(
                "[bold red]Authentication Required:[/] Set GITHUB_TOKEN or run "
                "'gitdevflow auth login' to select repositories interactively."
            )
            raise typer.Exit(code=1)

        chosen = asyncio.run(select_repo(cfg.github_token, default=cfg.default_repo))
        if not chosen:
            console.print("[yellow]No repository selected.[/]")
            return
        chosen_repo = chosen

    cfg.default_repo = chosen_repo
    cfg.save(cfg_path)
    console.print(
        f"[bold green]✓ Default repository set to [bold white]{chosen_repo}[/]!"
    )


@app.command()
def show(ctx: typer.Context) -> None:
    """Display the currently configured default repository."""
    cfg = _get_config(ctx)
    if cfg.default_repo:
        console.print(f"Default repository: [bold cyan]{cfg.default_repo}[/]")
    else:
        console.print("[yellow]No default repository configured.[/]")
        console.print(
            "[dim]Run 'gitdevflow repo use' or 'gitdevflow config init' to set one.[/]"
        )


@app.command("list")
def list_repos(ctx: typer.Context) -> None:
    """List accessible user repositories with default star indicator."""
    cfg = _get_config(ctx)
    if not cfg.github_token:
        error_console.print(
            "[bold red]Authentication Required:[/] Set GITHUB_TOKEN or run "
            "'gitdevflow auth login' to list repositories."
        )
        raise typer.Exit(code=1)

    async def _fetch() -> list[tuple[str, bool, str, str]]:
        async with GitHubClient(token=cfg.github_token or "") as client:
            repos = await client.list_user_repos()
            return [
                (
                    repo.full_name,
                    repo.private,
                    repo.default_branch,
                    repo.html_url,
                )
                for repo in repos
            ]

    try:
        repos_data = asyncio.run(_fetch())
    except Exception as err:
        error_console.print(f"[bold red]Failed to fetch repositories:[/] {err}")
        raise typer.Exit(code=1) from err

    if not repos_data:
        console.print("[yellow]No accessible repositories found.[/]")
        return

    table = Table(
        title="Accessible GitHub Repositories",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("", justify="center", style="yellow")
    table.add_column("Repository", style="bold white")
    table.add_column("Visibility", style="dim")
    table.add_column("Branch", style="cyan")
    table.add_column("URL", style="dim")

    for full_name, private, branch, url in repos_data:
        is_default = full_name == cfg.default_repo
        star = "★" if is_default else ""
        visibility = "Private" if private else "Public"
        table.add_row(star, full_name, visibility, branch, url)

    console.print(table)
