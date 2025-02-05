from __future__ import annotations

import argparse
from pathlib import Path

from gh_backdate.core.gh_cli import pr_view_json
from gh_backdate.core.merge_ops import merge_branch_backdated
from gh_backdate.utils import resolve_github_identity, resolve_github_login


def _resolve_branch_from_pr(pr_number: int, repo_dir: Path) -> str:
    data = pr_view_json(pr_number, ["headRefName"], cwd=repo_dir)
    head = data.get("headRefName")
    if not head:
        raise RuntimeError(f"Could not resolve head branch for PR #{pr_number}")
    return head


def handle(args: argparse.Namespace) -> None:
    repo_dir = Path(".").resolve()
    base = args.base
    branch = args.branch
    pr_number = args.pr

    if pr_number is not None and not branch:
        branch = _resolve_branch_from_pr(pr_number, repo_dir)

    name, email = resolve_github_identity()
    login = resolve_github_login()

    merge_branch_backdated(
        repo_dir=repo_dir,
        base=base,
        head=branch,
        merge_date=args.date,
        pr_number=pr_number,
        delete_branch=args.delete_branch,
        author_name=name,
        author_email=email,
        committer_name=login or name,
        committer_email=email,
    )


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "merge-pr",
        help="Merge a branch into base with a backdated merge commit and close the PR.",
    )
    p.add_argument("--base", default="main", help="Base branch (default: main).")
    p.add_argument("--branch", help="Branch to merge (head).")
    p.add_argument("--pr", type=int, help="PR number (optional if --branch is provided).")
    p.add_argument("--date", required=True, help="Merge commit date (e.g. '2025-03-01 17:00').")
    p.add_argument("--title", help="(unused) kept for compatibility.")
    p.add_argument("--delete-branch", action="store_true", help="Delete the remote branch after merge.")

    p.set_defaults(func=handle)
    return p
