"""PR management commands."""

import typer

from gitdevflow.utils.console import console

app = typer.Typer()


@app.command()
def create(
    title: str = typer.Option(..., "--title", "-t", help="PR title"),
    base: str = typer.Option("main", "--base", "-b", help="Base branch"),
    draft: bool = typer.Option(False, "--draft", "-d", help="Create as draft PR"),
    body: str | None = typer.Option(None, "--body", help="PR description"),
) -> None:
    """Create a new pull request."""
    console.print(f"[bold green]Creating PR:[/] {title}")
    # TODO: Implement PR creation via GitHub client


@app.command("list")
def list_prs(
    state: str = typer.Option("open", "--state", "-s", help="PR state filter"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
) -> None:
    """List pull requests."""
    console.print(f"[bold]Listing {state} PRs (limit: {limit})[/]")
    # TODO: Implement PR listing via GitHub client


@app.command()
def merge(
    pr_number: int = typer.Argument(..., help="PR number to merge"),
    strategy: str = typer.Option("squash", "--strategy", help="Merge strategy"),
) -> None:
    """Merge a pull request."""
    console.print(f"[bold yellow]Merging PR #{pr_number} with {strategy} strategy[/]")
    # TODO: Implement PR merge via GitHub client
