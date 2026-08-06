"""Changelog generation and validation commands."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.markdown import Markdown
from rich.progress import BarColumn, Progress, TextColumn

from gitdevflow.commands.pr import _resolve_client_and_repo
from gitdevflow.core.config import AppConfig
from gitdevflow.core.exceptions import NotFoundError, RateLimitedError
from gitdevflow.core.models import PullRequest
from gitdevflow.utils.console import console, error_console

app = typer.Typer()


@app.command()
def generate(
    ctx: typer.Context,
    repo: str | None = typer.Option(
        None, "--repo", "-r", help="Repository in 'owner/name' format."
    ),
    from_ref: str = typer.Option(
        "v0.1.0", "--from-ref", help="Start tag or commit SHA."
    ),
    to_ref: str = typer.Option("HEAD", "--to-ref", help="End tag or commit SHA."),
    output: str = typer.Option(
        "CHANGELOG.md",
        "--output",
        "-o",
        help="Output file path or '-' for stdout.",
    ),
    format: str = typer.Option(
        "markdown", "--format", "-f", help="Output format: markdown or json."
    ),
) -> None:
    """Generate a changelog from merged PRs between two git refs."""
    client, owner, repo_name = _resolve_client_and_repo(ctx, repo)
    cfg: AppConfig = (
        ctx.obj.get("config") if ctx.obj and "config" in ctx.obj else AppConfig.load()
    )

    async def _fetch_changelog_prs() -> tuple[list[PullRequest], str]:
        async with client:
            try:
                comparison = await client.compare_branches(
                    owner, repo_name, from_ref, to_ref
                )
            except NotFoundError as err:
                error_console.print(
                    f"[bold red]Error:[/] Git ref '{from_ref}' or '{to_ref}' "
                    f"not found in {owner}/{repo_name}."
                )
                raise typer.Exit(code=1) from err
            except RateLimitedError as err:
                error_console.print(f"[bold red]Rate limited by GitHub API:[/] {err}")
                raise typer.Exit(code=1) from err

            prs_map: dict[int, PullRequest] = {}

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=error_console,
                disable=(output == "-"),
            ) as progress:
                commits = comparison.commits
                task = progress.add_task(
                    "Analyzing commits...", total=max(len(commits), 1)
                )

                for commit in commits:
                    try:
                        commit_prs = await client.get_commit_pull_requests(
                            owner, repo_name, commit.sha
                        )
                        for pr in commit_prs:
                            if pr.number not in prs_map:
                                prs_map[pr.number] = pr
                    except Exception:
                        pass
                    progress.advance(task)

            # Fallback if no PRs were associated directly with commits
            if not prs_map:
                all_closed = await client.get_pull_requests(
                    owner, repo_name, state="closed"
                )
                for pr in all_closed:
                    if pr.merged_at:
                        prs_map[pr.number] = pr

            today_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            return list(prs_map.values()), today_date

    try:
        prs, today_str = asyncio.run(_fetch_changelog_prs())
    except typer.Exit:
        raise
    except Exception as err:
        error_console.print(f"[bold red]Failed to generate changelog:[/] {err}")
        raise typer.Exit(code=1) from err

    # Categorize PRs based on config rules
    sections = cfg.changelog_sections
    categorized: dict[str, list[PullRequest]] = {
        sec_title: [] for sec_title in sections
    }
    categorized["Other Changes"] = []

    for pr in prs:
        assigned = False
        pr_label_names = {lbl.name.lower() for lbl in pr.labels}
        for sec_title, labels in sections.items():
            labels_lower = {lbl.lower() for lbl in labels}
            if pr_label_names.intersection(labels_lower):
                categorized[sec_title].append(pr)
                assigned = True
                break

        # Also check title prefix if not matched by label
        if not assigned:
            title_prefix = pr.title.split(":")[0].lower().strip()
            for sec_title, labels in sections.items():
                labels_lower = {lbl.lower() for lbl in labels}
                if title_prefix in labels_lower:
                    categorized[sec_title].append(pr)
                    assigned = True
                    break

        if not assigned:
            categorized["Other Changes"].append(pr)

    fmt_lower = format.lower()
    if fmt_lower == "json":
        json_output = {
            "from_ref": from_ref,
            "to_ref": to_ref,
            "date": today_str,
            "repository": f"{owner}/{repo_name}",
            "categories": {
                title: [pr.model_dump() for pr in items]
                for title, items in categorized.items()
                if items
            },
        }
        content = json.dumps(json_output, indent=2)
    else:
        lines: list[str] = [
            f"## [{to_ref}] - {today_str}",
            "",
        ]
        has_entries = False
        for sec_title, items in categorized.items():
            if not items:
                continue
            has_entries = True
            lines.append(f"### {sec_title}")
            for pr in items:
                lines.append(
                    f"- {pr.title} ([#{pr.number}]({pr.html_url})) by @{pr.user.login}"
                )
            lines.append("")

        if not has_entries:
            lines.append("*No pull requests included in this release.*")
            lines.append("")

        content = "\n".join(lines)

    if output == "-":
        typer.echo(content)
        return

    out_path = Path(output)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and fmt_lower in ("markdown", "md"):
            existing = out_path.read_text(encoding="utf-8")
            if not existing.startswith("# Changelog"):
                full_content = f"# Changelog\n\n{content}\n" + existing
            else:
                parts = existing.split("\n\n", 1)
                if len(parts) == 2:
                    full_content = f"{parts[0]}\n\n{content}\n{parts[1]}"
                else:
                    full_content = f"# Changelog\n\n{content}\n" + existing
            out_path.write_text(full_content, encoding="utf-8")
        else:
            out_path.write_text(content, encoding="utf-8")
    except PermissionError as err:
        error_console.print(
            f"[bold red]Permission Error:[/] Cannot write to '{out_path}'.\n"
            "[dim]Pass '--output -' to print to terminal, "
            "or specify a writable directory path.[/]"
        )
        raise typer.Exit(code=1) from err
    console.print(f"[bold green]✓ Changelog generated -> {out_path}[/]")
    console.print("\n[bold]Preview:[/]")
    console.print(Markdown(content))


@app.command()
def validate(
    path: Path = typer.Option(
        Path("CHANGELOG.md"),
        "--path",
        "-p",
        help="Path to CHANGELOG file.",
    ),
) -> None:
    """Validate the format of an existing CHANGELOG.md file."""
    if not path.exists():
        error_console.print(
            f"[bold red]Error:[/] Changelog file '{path}' does not exist."
        )
        raise typer.Exit(code=1)

    text = path.read_text(encoding="utf-8")
    issues: list[str] = []

    if "# Changelog" not in text:
        issues.append("Missing main heading '# Changelog'")
    if "## [" not in text and "## Unreleased" not in text:
        issues.append("Missing version section heading (e.g. '## [v1.0.0]')")

    if issues:
        error_console.print(f"[bold red]Validation failed for {path}:[/]")
        for issue in issues:
            error_console.print(f"  • {issue}")
        raise typer.Exit(code=1)

    console.print(f"[bold green]✓ Changelog '{path}' format is valid![/]")
