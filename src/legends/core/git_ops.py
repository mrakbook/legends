from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from . import RunResult, git
from .dates import build_commit_env


def init_repo(path: Path, *, base_branch: str = "main") -> None:
    """Initialize a repo and set default branch (created on first commit)."""
    path.mkdir(parents=True, exist_ok=True)
    git(["init"], cwd=path)
    git(["config", "init.defaultBranch", base_branch], cwd=path)


def add(path: Path, items: Iterable[str] = (".",)) -> None:
    args = ["add", *list(items)]
    git(args, cwd=path)


def commit(
    path: Path,
    message: str,
    *,
    date: Optional[str] = None,
    allow_empty: bool = False,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None,
    committer_name: Optional[str] = None,
    committer_email: Optional[str] = None,
) -> RunResult:
    """Create a commit with optional backdated author/committer dates."""
    env = build_commit_env(
        date,
        author_name=author_name,
        author_email=author_email,
        committer_name=committer_name,
        committer_email=committer_email,
    )
    args = ["commit", "-m", message]
    if allow_empty:
        args.insert(1, "--allow-empty")
    return git(args, cwd=path, env=env)


def checkout(path: Path, ref: str) -> None:
    git(["checkout", ref], cwd=path)


def create_branch(path: Path, branch: str, *, base: str = "main") -> None:
    """Create a new branch from base."""
    try:
        git(["rev-parse", "--verify", base], cwd=path)
    except Exception:
        git(["fetch", "origin", f"{base}:{base}"], cwd=path)
    git(["checkout", base], cwd=path)
    git(["checkout", "-b", branch], cwd=path)


def merge_noff_no_commit(path: Path, base: str, branch: str) -> None:
    """Perform a no-ff merge into base, but leave the commit to the caller."""
    git(["checkout", base], cwd=path)
    git(["merge", "--no-ff", "--no-commit", branch], cwd=path)


def merge_commit(
    path: Path,
    message: str,
    *,
    date: Optional[str] = None,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None,
    committer_name: Optional[str] = None,
    committer_email: Optional[str] = None,
) -> RunResult:
    """Finalize a pending merge by creating the merge commit (with optional backdate)."""
    env = build_commit_env(
        date,
        author_name=author_name,
        author_email=author_email,
        committer_name=committer_name,
        committer_email=committer_email,
    )
    return git(["commit", "-m", message], cwd=path, env=env)


def push(path: Path, remote: str, refspec: str, *, set_upstream: bool = False) -> None:
    args = ["push", remote, refspec]
    if set_upstream:
        args.insert(1, "-u")
    git(args, cwd=path)


def pull(path: Path, remote: str, ref: str) -> None:
    git(["pull", remote, ref], cwd=path)
