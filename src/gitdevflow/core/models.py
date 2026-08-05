"""Pydantic models for GitHub API resources."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class User(BaseModel):
    """GitHub user model."""

    login: str
    id: int
    avatar_url: str | None = None
    html_url: str | None = None


class Label(BaseModel):
    """GitHub issue/PR label model."""

    name: str
    color: str = ""
    description: str | None = None


class Repository(BaseModel):
    """GitHub repository model."""

    id: int
    name: str
    full_name: str
    owner: User
    html_url: str
    default_branch: str = "main"
    description: str | None = None
    private: bool = False


class PullRequestRef(BaseModel):
    """Head or base reference in a pull request."""

    ref: str
    sha: str
    label: str | None = None


class PullRequest(BaseModel):
    """GitHub pull request model."""

    number: int
    title: str
    state: str
    html_url: str
    user: User
    body: str | None = None
    labels: list[Label] = Field(default_factory=list)
    head: PullRequestRef | None = None
    base: PullRequestRef | None = None
    draft: bool = False
    created_at: str | None = None
    merged_at: str | None = None


class CommitDetail(BaseModel):
    """Inner commit details."""

    message: str
    author: dict[str, Any] | None = None


class Commit(BaseModel):
    """GitHub commit model."""

    sha: str
    commit: CommitDetail | None = None
    html_url: str | None = None


class BranchComparison(BaseModel):
    """GitHub branch comparison model."""

    ahead_by: int = 0
    behind_by: int = 0
    status: str = ""
    total_commits: int = 0
    commits: list[Commit] = Field(default_factory=list)
