"""Typer CLI application entrypoint."""

from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.logging import RichHandler
from rich.panel import Panel

from gitdevflow import __app_name__, __version__
from gitdevflow.commands import changelog, config, pr
from gitdevflow.core.config import DEFAULT_CONFIG_PATH, AppConfig
from gitdevflow.core.exceptions import (
    AuthenticationError,
    ConfigError,
    GitHubAPIError,
    NotFoundError,
    RateLimitedError,
)
from gitdevflow.utils.console import console, error_console

app = typer.Typer(
    name=__app_name__,
    help="A CLI tool for streamlining Git-based development workflows.",
    add_completion=True,
    rich_markup_mode="rich",
)

# Register sub-command groups
app.add_typer(pr.app, name="pr", help="Pull request management commands.")
app.add_typer(changelog.app, name="changelog", help="Changelog generation commands.")
app.add_typer(config.app, name="config", help="Configuration commands.")


def render_error_panel(err: Exception) -> None:
    """Render a styled Rich error panel for exceptions."""
    if isinstance(err, AuthenticationError):
        panel = Panel(
            "[bold red]Authentication Error:[/]\n"
            f"{err.message}\n\n"
            "[dim]Check your GITHUB_TOKEN environment variable or config file.[/]",
            title="Authentication Failed",
            border_style="red",
        )
    elif isinstance(err, RateLimitedError):
        retry_msg = (
            f"Retry after {err.retry_after} seconds."
            if err.retry_after
            else "Please wait before sending more requests."
        )
        panel = Panel(
            f"[bold yellow]Rate Limit Exceeded:[/]\n{err.message}\n\n"
            f"[dim]{retry_msg}[/]",
            title="Rate Limited",
            border_style="yellow",
        )
    elif isinstance(err, NotFoundError):
        panel = Panel(
            f"[bold red]Resource Not Found:[/]\n{err.message}",
            title="Not Found",
            border_style="red",
        )
    elif isinstance(err, ConfigError):
        panel = Panel(
            f"[bold red]Configuration Error:[/]\n{err}\n\n"
            "[dim]Run 'gitdevflow config init' to create a valid config.[/]",
            title="Config Error",
            border_style="red",
        )
    elif isinstance(err, GitHubAPIError):
        panel = Panel(
            f"[bold red]GitHub API Error [{err.status_code}]:[/]\n{err.message}",
            title="API Error",
            border_style="red",
        )
    else:
        panel = Panel(
            f"[bold red]Unhandled Error:[/]\n{err}",
            title="Error",
            border_style="red",
        )
    error_console.print(panel)


@app.command()
def version() -> None:
    """Print the version."""
    console.print(f"[bold cyan]{__app_name__}[/] v[bold green]{__version__}[/]")


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]{__app_name__}[/] v[bold green]{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    config_path: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration YAML file.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable detailed verbose logging output.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging output.",
    ),
    show_version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """gitdevflow — streamline your Git development workflow."""
    if verbose or debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=error_console, rich_tracebacks=True)],
        )
        logging.debug("Debug logging enabled.")

    cfg_path = config_path or DEFAULT_CONFIG_PATH
    try:
        loaded_config = AppConfig.load(cfg_path)
    except ConfigError as err:
        render_error_panel(err)
        raise typer.Exit(code=1) from err

    ctx.ensure_object(dict)
    ctx.obj["config"] = loaded_config
