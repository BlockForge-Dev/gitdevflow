"""Typer CLI application entrypoint."""

from pathlib import Path

import typer

from gitdevflow import __app_name__, __version__
from gitdevflow.commands import changelog, config, pr
from gitdevflow.core.config import DEFAULT_CONFIG_PATH, AppConfig

app = typer.Typer(
    name=__app_name__,
    help="A CLI tool for streamlining Git-based development workflows.",
    add_completion=False,
    rich_markup_mode="rich",
)

# Register sub-command groups
app.add_typer(pr.app, name="pr", help="Pull request management commands.")
app.add_typer(changelog.app, name="changelog", help="Changelog generation commands.")
app.add_typer(config.app, name="config", help="Configuration commands.")


@app.command()
def version() -> None:
    """Print the version."""
    typer.echo(__version__)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
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
    cfg_path = config_path or DEFAULT_CONFIG_PATH
    loaded_config = AppConfig.load(cfg_path)
    ctx.ensure_object(dict)
    ctx.obj["config"] = loaded_config
