"""Configuration display and validation commands."""

from pathlib import Path

import typer
from rich.table import Table

from gitdevflow.core.config import DEFAULT_CONFIG_PATH, AppConfig
from gitdevflow.utils.console import console, error_console

app = typer.Typer()


def _get_config(ctx: typer.Context) -> AppConfig:
    """Retrieve AppConfig from Typer context or load default."""
    if ctx.obj and "config" in ctx.obj and isinstance(ctx.obj["config"], AppConfig):
        return ctx.obj["config"]
    return AppConfig.load()


@app.command()
def show(ctx: typer.Context) -> None:
    """Display the current configuration (with token masked)."""
    cfg = _get_config(ctx)
    data = cfg.to_dict(mask_sensitive=True)

    if cfg.output_format == "plain":
        typer.echo("Configuration:")
        for key, val in data.items():
            typer.echo(f"  {key}: {val}")
        return

    table = Table(
        title="gitdevflow Configuration",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    for key, val in data.items():
        table.add_row(key, str(val))

    console.print(table)


@app.command()
def validate(ctx: typer.Context) -> None:
    """Check if required configuration fields are present and valid."""
    cfg = _get_config(ctx)
    issues: list[str] = []

    if not cfg.github_token:
        issues.append(
            "`github_token` is missing. Set GITHUB_TOKEN environment "
            "variable or add to config."
        )

    if issues:
        error_console.print("[bold red]Configuration validation failed:[/]")
        for issue in issues:
            error_console.print(f"  • {issue}")
        raise typer.Exit(code=1)

    console.print("[bold green]✓ Configuration is valid![/]")
    console.print(f"  GitHub Token: [dim]{cfg.masked_token()}[/]")
    if cfg.default_repo:
        console.print(f"  Default Repo: [dim]{cfg.default_repo}[/]")


@app.command()
def init(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Custom path for initial config file.",
    ),
) -> None:
    """Initialize a default configuration file."""
    target_path = path or DEFAULT_CONFIG_PATH
    if target_path.exists():
        error_console.print(
            f"[bold red]Configuration file already exists at {target_path}[/]"
        )
        raise typer.Exit(code=1)

    sample_content = """# gitdevflow configuration file
github_token: ""
default_repo: ""
pr_label_prefix: "type:"
changelog_sections:
  Features:
    - feat
    - enhancement
  Bug Fixes:
    - fix
    - bug
  Documentation:
    - docs
    - documentation
output_format: "rich"
"""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(sample_content, encoding="utf-8")
    console.print(f"[bold green]✓ Created configuration file at {target_path}[/]")
