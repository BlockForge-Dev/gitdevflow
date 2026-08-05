"""Configuration display and validation commands."""

import typer

from gitdevflow.utils.console import console

app = typer.Typer()


@app.command()
def show() -> None:
    """Display the current configuration."""
    console.print("[bold]Current configuration:[/]")
    # TODO: Load and display config


@app.command()
def validate() -> None:
    """Validate the configuration file."""
    console.print("[bold]Validating configuration...[/]")
    # TODO: Implement config validation


@app.command()
def init() -> None:
    """Initialize a new configuration file."""
    console.print("[bold green]Creating .gitdevflow.yml...[/]")
    # TODO: Implement config initialization
