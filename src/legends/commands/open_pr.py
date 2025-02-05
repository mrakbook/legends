from __future__ import annotations

import argparse
from pathlib import Path

from gh_backdate.core.gh_cli import pr_create, pr_view_json


def handle(args: argparse.Namespace) -> None:
    repo_dir = Path(".").resolve()
    pr_number = pr_create(
        head=args.branch,
        base=args.base,
        title=args.title or args.branch,
        body=args.body or "",
        draft=args.draft,
        cwd=repo_dir,
    )
    info = pr_view_json(pr_number, ["url"], cwd=repo_dir)
    url = info.get("url", "")
    print(f"Opened PR #{pr_number}{f' → {url}' if url else ''}")


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "open-pr",
        help="Open a pull request via GitHub CLI from branch to base.",
    )
    p.add_argument("--branch", required=True, help="Head branch (source).")
    p.add_argument("--base", default="main", help="Base branch (target), default: main.")
    p.add_argument("--title", help="PR title (default: branch name).")
    p.add_argument("--body", help="PR body text.")
    p.add_argument("--draft", action="store_true", help="Open PR as draft.")

    p.set_defaults(func=handle)
    return p
