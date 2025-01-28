from __future__ import annotations

import argparse
from pathlib import Path

from gh_backdate.core.git_ops import create_branch as _create_branch, commit
from gh_backdate.utils import resolve_github_identity, resolve_github_login


def handle(args: argparse.Namespace) -> None:
    repo_dir = Path(".").resolve()
    _create_branch(repo_dir, args.branch, base=args.base)

    name, email = resolve_github_identity()
    login = resolve_github_login()

    message = args.message or f"chore({args.branch}): branch birth @ {args.date}"
    commit(
        repo_dir,
        message,
        date=args.date,
        allow_empty=True,
        author_name=name,
        author_email=email,
        committer_name=login or name,
        committer_email=email,
    )
    if args.push:
        from gh_backdate.core.git_ops import push

        push(repo_dir, "origin", args.branch, set_upstream=True)


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "create-branch",
        help="Create a branch and add a backdated empty 'birth' commit.",
    )
    p.add_argument("branch", help="New branch name.")
    p.add_argument("--base", default="main", help="Base branch to branch from (default: main).")
    p.add_argument("--date", required=True, help="Backdated 'birth' commit date.")
    p.add_argument("--message", help="Birth commit message (optional).")
    p.add_argument("--push", action="store_true", help="Push the new branch to origin.")

    p.set_defaults(func=handle)
    return p
