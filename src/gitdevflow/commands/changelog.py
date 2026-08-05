"""Changelog generation commands."""

import typer

from gitdevflow.utils.console import console

app = typer.Typer()


@app.command()
def generate(
    since: str | None = typer.Option(None, "--since", help="Start tag or commit"),
    output: str = typer.Option("CHANGELOG.md", "--output", "-o", help="Output file"),
    format: str = typer.Option("md", "--format", "-f", help="Output format (md, json)"),
    group_by: bool = typer.Option(True, "--group-by", help="Group by labels"),
) -> None:
    """Generate a changelog from merged PRs."""
    console.print(f"[bold green]Generating changelog → {output}[/]")
    # TODO: Implement changelog generation


@app.command()
def validate() -> None:
    """Validate the existing changelog format."""
    console.print("[bold]Validating CHANGELOG.md...[/]")
    # TODO: Implement changelog validation
