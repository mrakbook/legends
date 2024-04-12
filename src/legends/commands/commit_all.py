from __future__ import annotations

import argparse
from pathlib import Path

from gh_backdate.core import git
from gh_backdate.core.git_ops import add as git_add, commit as git_commit
from gh_backdate.core.gh_cli import pr_create, pr_comment, pr_review
from gh_backdate.core.merge_ops import merge_branch_backdated
from gh_backdate.utils import resolve_github_identity, resolve_github_login


def handle(args: argparse.Namespace) -> None:
    repo_dir = Path(".").resolve()
    base = args.base
    branch = args.branch

    try:
        git(["rev-parse", "--verify", branch], cwd=repo_dir)
        git(["checkout", branch], cwd=repo_dir)
    except Exception:
        git(["checkout", base], cwd=repo_dir)
        git(["checkout", "-b", branch], cwd=repo_dir)

    if args.touch:
        p = Path(args.touch)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write("")
        git_add(repo_dir, [args.touch])
    else:
        git(["add", "-A"], cwd=repo_dir)

    name, email = resolve_github_identity()
    login = resolve_github_login()

    git_commit(
        repo_dir,
        args.message,
        date=args.commit_date,
        allow_empty=args.allow_empty,
        author_name=name,
        author_email=email,
        committer_name=login or name,
        committer_email=email,
    )

    try:
        git(["push", "origin", branch], cwd=repo_dir)
    except Exception:
        git(["push", "-u", "origin", branch], cwd=repo_dir)

    pr_title = args.pr_title or args.message
    pr_number = pr_create(
        head=branch,
        base=base,
        title=pr_title,
        body=args.pr_body or "",
        draft=args.draft,
        cwd=repo_dir,
    )

    if args.review:
        pr_review(pr_number, body=args.review_body or "LGTM", approve=True, cwd=repo_dir)
    if args.comment:
        pr_comment(pr_number, body=args.comment, cwd=repo_dir)

    merge_branch_backdated(
        repo_dir=repo_dir,
        base=base,
        head=branch,
        merge_date=args.merge_date,
        pr_number=pr_number,
        delete_branch=args.delete_branch,
        author_name=name,
        author_email=email,
        committer_name=login or name,
        committer_email=email,
    )


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "commit-all",
        help="Commit (backdated) → open PR → (optional review/comment) → backdated merge (one shot).",
    )
    p.add_argument("--base", default="main", help="Base branch (default: main).")
    p.add_argument("--branch", required=True, help="Feature branch to work on.")
    p.add_argument("--commit-date", required=True, help="Commit date for the change.")
    p.add_argument("--message", required=True, help="Commit message.")
    p.add_argument("--touch", help="Create/modify this file before committing (ensures non-empty).")
    p.add_argument("--allow-empty", action="store_true", help="Allow empty commit if no changes.")
    p.add_argument("--pr-title", help="Pull request title (defaults to commit message).")
    p.add_argument("--pr-body", help="Pull request body.")
    p.add_argument("--draft", action="store_true", help="Open PR as draft.")
    p.add_argument("--merge-date", required=True, help="Merge commit date.")
    p.add_argument("--delete-branch", action="store_true", help="Delete remote branch after merge.")
    p.add_argument("--review", action="store_true", help="Approve the PR after opening (not backdated).")
    p.add_argument("--review-body", help="Body text for the approval review (default: 'LGTM').")
    p.add_argument("--comment", help="Post a top-level PR comment (not backdated).")

    p.set_defaults(func=handle)
    return p
