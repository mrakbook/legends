from __future__ import annotations

import argparse
from pathlib import Path

from gh_backdate.core.git_ops import commit as git_commit
from gh_backdate.core import git
from gh_backdate.utils import resolve_github_identity, resolve_github_login


def handle(args: argparse.Namespace) -> None:
    repo_dir = Path(".").resolve()
    try:
        git(["rev-parse", "--verify", args.branch], cwd=repo_dir)
        git(["checkout", args.branch], cwd=repo_dir)
    except Exception:
        git(["checkout", "-b", args.branch], cwd=repo_dir)

    if args.touch:
        p = Path(args.touch)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write("")

        git(["add", args.touch], cwd=repo_dir)

    if args.add_all:
        git(["add", "-A"], cwd=repo_dir)

    name, email = resolve_github_identity()
    login = resolve_github_login()

    git_commit(
        repo_dir,
        args.message,
        date=args.date,
        allow_empty=args.allow_empty,
        author_name=name,
        author_email=email,
        committer_name=login or name,
        committer_email=email,
    )

    if args.push:
        try:
            git(["push", "origin", args.branch], cwd=repo_dir)
        except Exception:
            git(["push", "-u", "origin", args.branch], cwd=repo_dir)


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "commit",
        help="Create a backdated commit on a specified branch.",
    )
    p.add_argument("--branch", required=True, help="Branch to commit on.")
    p.add_argument("--date", required=True, help="Commit date (e.g. '2025-02-10 15:00').")
    p.add_argument("--message", required=True, help="Commit message.")
    p.add_argument("--allow-empty", action="store_true", help="Allow empty commit if there are no changes.")
    p.add_argument("--add-all", action="store_true", help="Stage all changes with 'git add -A' before commit.")
    p.add_argument("--touch", help="Create/modify this file before committing (ensures non-empty).")
    p.add_argument("--push", action="store_true", help="Push branch after committing.")

    p.set_defaults(func=handle)
    return p
