"""Authentication commands for login, status display, and logout."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from gitdevflow.core.config import DEFAULT_CONFIG_PATH, AppConfig
from gitdevflow.core.exceptions import AuthenticationError
from gitdevflow.core.github_client import GitHubClient
from gitdevflow.utils.console import console, error_console

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
def login(ctx: typer.Context) -> None:
    """Authenticate with GitHub using a Personal Access Token."""
    console.print("[bold cyan]gitdevflow Authentication Login[/]")
    token = typer.prompt("Enter GitHub personal access token", hide_input=True)

    if not token or not token.strip():
        error_console.print("[bold red]Error:[/] Token cannot be empty.")
        raise typer.Exit(code=1)

    clean_token = token.strip()

    async def _validate() -> str:
        async with GitHubClient(token=clean_token) as client:
            user = await client.get_user()
            return user.login

    try:
        username = asyncio.run(_validate())
    except AuthenticationError as err:
        error_console.print(
            "[bold red]Authentication Failed:[/] Invalid or expired token.\n"
            f"[dim]{err.message}[/]"
        )
        raise typer.Exit(code=1) from err
    except Exception as err:
        error_console.print(f"[bold red]Failed to validate token:[/] {err}")
        raise typer.Exit(code=1) from err

    cfg = _get_config(ctx)
    cfg.github_token = clean_token
    saved_path = cfg.save(_get_config_path(ctx))

    console.print(
        f"[bold green]✓ Successfully authenticated as [bold white]@{username}[/]!"
    )
    console.print(f"  Token saved securely to [dim]{saved_path}[/]")


@app.command()
def status(ctx: typer.Context) -> None:
    """Check current authentication status and logged-in user."""
    cfg = _get_config(ctx)
    cfg_path = _get_config_path(ctx)

    if not cfg.github_token:
        console.print("[yellow]Not logged in.[/]")
        console.print("[dim]Run 'gitdevflow auth login' to authenticate.[/]")
        return

    async def _check_status() -> str:
        async with GitHubClient(token=cfg.github_token or "") as client:
            user = await client.get_user()
            return user.login

    try:
        username = asyncio.run(_check_status())
        console.print("[bold green]Logged in[/]")
        console.print(f"  User: [bold cyan]@{username}[/]")
        console.print(f"  Token: [dim]{cfg.masked_token()}[/]")
        console.print(f"  Config: [dim]{cfg_path}[/]")
    except Exception as err:
        error_console.print(
            "[bold red]Authentication Status Error:[/] "
            f"Token in config is invalid ({err})."
        )
        console.print("[dim]Run 'gitdevflow auth login' to re-authenticate.[/]")
        raise typer.Exit(code=1) from err


@app.command()
def logout(ctx: typer.Context) -> None:
    """Remove stored GitHub authentication token."""
    cfg = _get_config(ctx)
    cfg.github_token = None
    saved_path = cfg.save(_get_config_path(ctx))

    console.print("[bold green]✓ Successfully logged out.[/]")
    console.print(f"  Removed token from [dim]{saved_path}[/]")
