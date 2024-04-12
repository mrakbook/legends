from __future__ import annotations

import argparse
from pathlib import Path

from legends.core.git_ops import init_repo, add, commit
from legends.core.gh_cli import repo_create
from legends.utils import resolve_github_identity, resolve_github_login


def handle(args: argparse.Namespace) -> None:
    repo_dir = Path(args.name).resolve()
    repo_dir.mkdir(parents=True, exist_ok=True)

    init_repo(repo_dir, base_branch=args.branch)

    readme = repo_dir / "README.md"
    if not readme.exists():
        readme.write_text(f"# {args.name}\n\n{args.description or ''}\n", encoding="utf-8")
    add(repo_dir, [readme.name])

    author_name = args.author_name
    author_email = args.author_email
    if not author_name or not author_email:
        name, email = resolve_github_identity()
        author_name = author_name or name
        author_email = author_email or email

    login = resolve_github_login()

    commit(
        repo_dir,
        args.message,
        date=args.date,
        author_name=author_name,
        author_email=author_email,
        committer_name=login or author_name,
        committer_email=author_email,
    )

    result = repo_create(
        args.name,
        source_dir=repo_dir,
        visibility=("private" if args.private else "public"),
        remote=args.remote,
        description=args.description or "",
        owner=args.owner,
    )
    print(result.stdout, end="")


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "create-repo",
        help="Create a GitHub repo from the local folder with a backdated initial commit.",
    )
    p.add_argument("name", help="Repository name (also local directory name).")
    p.add_argument("--owner", help="GitHub owner/org (optional).")
    p.add_argument("--description", default="", help="Repository description.")
    p.add_argument("--branch", default="main", help="Default branch name (default: main).")
    p.add_argument("--message", default="Initial commit", help="Initial commit message.")
    p.add_argument("--date", help="Initial commit date (e.g. '2024-12-01 12:00:00').")
    p.add_argument("--author-name", help="Override GIT_AUTHOR_NAME for initial commit.")
    p.add_argument("--author-email", help="Override GIT_AUTHOR_EMAIL for initial commit.")
    vis = p.add_mutually_exclusive_group()
    vis.add_argument("--private", action="store_true", help="Create repository as private (default).")
    vis.add_argument("--public", action="store_true", help="Create repository as public.")
    p.add_argument("--remote", default="origin", help="Remote name to set (default: origin).")

    p.set_defaults(func=handle)
    return p
