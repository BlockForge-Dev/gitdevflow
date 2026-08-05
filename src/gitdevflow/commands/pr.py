"""Pull Request management commands — list, check, label, create, merge."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from typing import Any

import typer
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from gitdevflow.core.config import AppConfig
from gitdevflow.core.github_client import GitHubClient
from gitdevflow.core.models import PullRequest
from gitdevflow.utils.console import console, error_console

app = typer.Typer()

CONVENTIONAL_COMMIT_REGEX = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\([a-zA-Z0-9_.-]+\))?!?: .+"
)

BRANCH_PREFIX_LABEL_MAP = {
    "feat": "enhancement",
    "feature": "enhancement",
    "fix": "bug",
    "bugfix": "bug",
    "docs": "documentation",
    "doc": "documentation",
    "test": "testing",
    "chore": "chore",
    "refactor": "refactor",
}


def parse_repo_string(repo_str: str) -> tuple[str, str]:
    """Validate and split 'owner/repo' format string into (owner, repo)."""
    parts = repo_str.strip().split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Invalid repository format '{repo_str}'. Expected 'owner/repository'."
        )
    return parts[0], parts[1]


def _resolve_client_and_repo(
    ctx: typer.Context, repo_arg: str | None
) -> tuple[GitHubClient, str, str]:
    """Extract client and repository info from Typer context or CLI options."""
    cfg: AppConfig = (
        ctx.obj.get("config") if ctx.obj and "config" in ctx.obj else AppConfig.load()
    )

    if not cfg.github_token:
        error_console.print(
            "[bold red]Error:[/] GITHUB_TOKEN is not set in environment or config."
        )
        raise typer.Exit(code=1)

    raw_repo = repo_arg or cfg.default_repo
    if not raw_repo:
        error_console.print(
            "[bold red]Error:[/] No repository specified. "
            "Provide --repo or set default_repo in config."
        )
        raise typer.Exit(code=1)

    try:
        owner, repo = parse_repo_string(raw_repo)
    except ValueError as err:
        error_console.print(f"[bold red]Error:[/] {err}")
        raise typer.Exit(code=1) from err

    client = GitHubClient(token=cfg.github_token, owner=owner, repo=repo)
    return client, owner, repo


def _get_current_git_branch() -> str | None:
    """Return the current local Git branch name if inside a git repository."""
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
        branch = res.stdout.strip()
        return branch if branch else None
    except Exception:
        return None


@app.command("list")
def list_prs(
    ctx: typer.Context,
    repo: str | None = typer.Option(
        None, "--repo", "-r", help="Repository in 'owner/name' format."
    ),
    state: str = typer.Option(
        "open", "--state", "-s", help="PR state: open, closed, or all."
    ),
    label: str | None = typer.Option(None, "--label", "-l", help="Filter by label."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON array."),
) -> None:
    """List pull requests for a repository."""
    client, owner, repo_name = _resolve_client_and_repo(ctx, repo)

    async def _fetch() -> list[PullRequest]:
        async with client:
            return await client.get_pull_requests(owner, repo_name, state=state)

    try:
        prs = asyncio.run(_fetch())
    except Exception as err:
        error_console.print(f"[bold red]Failed to fetch PRs:[/] {err}")
        raise typer.Exit(code=1) from err

    if label:
        label_lower = label.lower()
        prs = [
            pr
            for pr in prs
            if any(lbl.name.lower() == label_lower for lbl in pr.labels)
        ]

    if as_json:
        json_data = [pr.model_dump() for pr in prs]
        typer.echo(json.dumps(json_data, indent=2))
        return

    if not prs:
        console.print(
            f"[yellow]No {state} pull requests found for {owner}/{repo_name}.[/]"
        )
        return

    table = Table(
        title=f"Pull Requests for {owner}/{repo_name} ({state})",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("PR #", style="bold yellow", justify="right")
    table.add_column("Title", style="white")
    table.add_column("Author", style="green")
    table.add_column("Labels", style="magenta")
    table.add_column("Created At", style="dim")

    for pr in prs:
        labels_str = ", ".join(lbl.name for lbl in pr.labels) if pr.labels else "-"
        created = (pr.created_at or "")[:10]
        table.add_row(f"#{pr.number}", pr.title, pr.user.login, labels_str, created)

    console.print(table)


@app.command()
def check(
    ctx: typer.Context,
    repo: str | None = typer.Option(
        None, "--repo", "-r", help="Repository in 'owner/name' format."
    ),
    pr_number: int | None = typer.Option(
        None, "--pr", "-p", help="Specific PR number to check."
    ),
) -> None:
    """Check PR title and body compliance against Conventional Commits."""
    client, owner, repo_name = _resolve_client_and_repo(ctx, repo)

    async def _fetch() -> list[PullRequest]:
        async with client:
            if pr_number is not None:
                all_prs = await client.get_pull_requests(owner, repo_name, state="all")
                matching = [p for p in all_prs if p.number == pr_number]
                if not matching:
                    error_console.print(f"[bold red]PR #{pr_number} not found.[/]")
                    raise typer.Exit(code=1)
                return matching
            return await client.get_pull_requests(owner, repo_name, state="open")

    try:
        prs = asyncio.run(_fetch())
    except typer.Exit:
        raise
    except Exception as err:
        error_console.print(f"[bold red]Failed to check PRs:[/] {err}")
        raise typer.Exit(code=1) from err

    if not prs:
        console.print("[yellow]No pull requests to check.[/]")
        return

    has_violations = False
    results_text: list[str] = []

    for pr in prs:
        pr_issues: list[str] = []

        if not CONVENTIONAL_COMMIT_REGEX.match(pr.title):
            pr_issues.append(
                f"Title '{pr.title}' does not follow Conventional Commits "
                "format (e.g. 'feat: description')."
            )

        if not pr.body or len(pr.body.strip()) < 10:
            pr_issues.append(
                "PR description body is empty or too short "
                "(minimum 10 characters required)."
            )

        if pr.head and pr.head.ref:
            branch = pr.head.ref
            valid_prefix = any(
                branch.startswith(f"{p}/") for p in BRANCH_PREFIX_LABEL_MAP
            )
            if not valid_prefix and branch not in ("main", "develop"):
                prefixes = ", ".join(BRANCH_PREFIX_LABEL_MAP.keys())
                pr_issues.append(
                    f"Branch name '{branch}' does not start with a recognized "
                    f"prefix ({prefixes}/)."
                )

        if pr_issues:
            has_violations = True
            results_text.append(f"[bold red]❌ PR #{pr.number}: {pr.title}[/]")
            for issue in pr_issues:
                results_text.append(f"   • {issue}")
        else:
            results_text.append(
                f"[bold green]✓ PR #{pr.number}: {pr.title} (Passed)[/]"
            )

    panel_style = "bold red" if has_violations else "bold green"
    panel_title = (
        "PR Compliance Validation Failed"
        if has_violations
        else "PR Compliance Validation Passed"
    )
    console.print(
        Panel("\n".join(results_text), title=panel_title, border_style=panel_style)
    )

    if has_violations:
        raise typer.Exit(code=1)


@app.command()
def label(
    ctx: typer.Context,
    repo: str | None = typer.Option(
        None, "--repo", "-r", help="Repository in 'owner/name' format."
    ),
    pr_number: int | None = typer.Option(
        None, "--pr", "-p", help="Specific PR number to auto-label."
    ),
) -> None:
    """Auto-label pull requests based on branch prefix or title rules."""
    client, owner, repo_name = _resolve_client_and_repo(ctx, repo)

    async def _process_labels() -> list[tuple[int, list[str]]]:
        async with client:
            if pr_number is not None:
                prs = await client.get_pull_requests(owner, repo_name, state="all")
                prs = [p for p in prs if p.number == pr_number]
            else:
                prs = await client.get_pull_requests(owner, repo_name, state="open")

            results: list[tuple[int, list[str]]] = []
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Labeling PRs...", total=len(prs))

                for pr in prs:
                    new_labels: set[str] = {lbl.name for lbl in pr.labels}

                    if pr.head and pr.head.ref:
                        branch_prefix = pr.head.ref.split("/")[0].lower()
                        if branch_prefix in BRANCH_PREFIX_LABEL_MAP:
                            new_labels.add(BRANCH_PREFIX_LABEL_MAP[branch_prefix])

                    title_prefix = pr.title.split(":")[0].lower().strip()
                    if title_prefix in BRANCH_PREFIX_LABEL_MAP:
                        new_labels.add(BRANCH_PREFIX_LABEL_MAP[title_prefix])

                    updated_list = sorted(new_labels)
                    if set(updated_list) != {lbl.name for lbl in pr.labels}:
                        await client.set_labels(
                            owner, repo_name, pr.number, updated_list
                        )
                        results.append((pr.number, updated_list))

                    progress.advance(task)

            return results

    try:
        updated = asyncio.run(_process_labels())
    except Exception as err:
        error_console.print(f"[bold red]Failed to label PRs:[/] {err}")
        raise typer.Exit(code=1) from err

    if not updated:
        console.print("[yellow]No PRs required label updates.[/]")
        return

    console.print(f"[bold green]✓ Auto-labeled {len(updated)} pull request(s):[/]")
    for pr_num, labels_set in updated:
        console.print(f"  • PR #{pr_num} → {', '.join(labels_set)}")


@app.command()
def create(
    ctx: typer.Context,
    title: str | None = typer.Option(None, "--title", "-t", help="Pull request title."),
    head: str | None = typer.Option(
        None, "--head", "-h", help="Head branch containing your changes."
    ),
    base: str = typer.Option("main", "--base", "-b", help="Base branch to merge into."),
    body: str | None = typer.Option(None, "--body", help="Pull request description."),
    draft: bool = typer.Option(
        False, "--draft", "-d", help="Create as a draft pull request."
    ),
    repo: str | None = typer.Option(
        None, "--repo", "-r", help="Repository in 'owner/name' format."
    ),
) -> None:
    """Create a new pull request with interactive prompts and validation."""
    client, owner, repo_name = _resolve_client_and_repo(ctx, repo)

    head_branch = head or _get_current_git_branch()
    if not head_branch:
        head_branch = typer.prompt("Head branch (branch to merge)")

    pr_title = title
    if not pr_title:
        pr_title = typer.prompt("Pull request title")

    if not head_branch or not pr_title:
        error_console.print("[bold red]Error:[/] Head branch and title are required.")
        raise typer.Exit(code=1)

    pr_body = body
    if pr_body is None:
        pr_body = typer.prompt(
            "Pull request description (optional)", default="", show_default=False
        )

    target_head: str = head_branch
    target_title: str = pr_title

    async def _create() -> PullRequest:
        async with client:
            return await client.create_pull_request(
                owner=owner,
                repo=repo_name,
                title=target_title,
                head=target_head,
                base=base,
                body=pr_body if pr_body else None,
                draft=draft,
            )

    try:
        new_pr = asyncio.run(_create())
    except Exception as err:
        error_console.print(f"[bold red]Failed to create PR:[/] {err}")
        raise typer.Exit(code=1) from err

    draft_badge = " [yellow](Draft)[/]" if draft else ""
    console.print(
        f"[bold green]✓ Created Pull Request #{new_pr.number}{draft_badge}:[/] "
        f"{new_pr.title}"
    )
    console.print(f"  Link: [cyan]{new_pr.html_url}[/]")


@app.command()
def merge(
    ctx: typer.Context,
    pr_number: int = typer.Argument(..., help="PR number to merge."),
    repo: str | None = typer.Option(
        None, "--repo", "-r", help="Repository in 'owner/name' format."
    ),
    strategy: str = typer.Option(
        "squash", "--strategy", help="Merge strategy: squash, merge, or rebase."
    ),
) -> None:
    """Merge a pull request."""
    client, owner, repo_name = _resolve_client_and_repo(ctx, repo)

    async def _merge() -> dict[str, Any]:
        async with client:
            return await client.merge_pull_request(
                owner, repo_name, pr_number, merge_method=strategy
            )

    try:
        res = asyncio.run(_merge())
    except Exception as err:
        error_console.print(f"[bold red]Failed to merge PR #{pr_number}:[/] {err}")
        raise typer.Exit(code=1) from err

    msg = res.get("message", "Merged successfully.")
    console.print(f"[bold green]✓ PR #{pr_number} merged:[/] {msg}")
