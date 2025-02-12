from __future__ import annotations

from pathlib import Path
from typing import Optional

from .git_ops import merge_noff_no_commit, merge_commit, pull, push, checkout
from .gh_cli import pr_close
from .templates import TEMPLATES, render


def merge_branch_backdated(
    *,
    repo_dir: Path,
    base: str,
    head: str,
    merge_date: str,
    pr_number: Optional[int] = None,
    delete_branch: bool = True,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None,
    committer_name: Optional[str] = None,
    committer_email: Optional[str] = None,
) -> None:
    """
    Perform a no-ff merge of `head` into `base` using a backdated merge commit, push, and (optionally) close PR.
    """
    checkout(repo_dir, base)
    pull(repo_dir, "origin", base)
    merge_noff_no_commit(repo_dir, base, head)

    if pr_number is not None:
        msg = render(
            TEMPLATES.merge_message_with_pr,
            {"pr_number": pr_number, "branch": head, "base": base, "title": f"Merge {head}"},
        )
    else:
        msg = render(
            TEMPLATES.merge_message_plain,
            {"branch": head, "base": base, "title": f"Merge {head}"},
        )

    merge_commit(
        repo_dir,
        msg,
        date=merge_date,
        author_name=author_name,
        author_email=author_email,
        committer_name=committer_name,
        committer_email=committer_email,
    )
    push(repo_dir, "origin", base)

    if pr_number is not None and delete_branch:
        pr_close(pr_number, delete_branch=True, cwd=repo_dir)
    elif delete_branch:
        push(repo_dir, "origin", f":{head}")
