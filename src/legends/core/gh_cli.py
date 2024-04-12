from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

from . import RunResult, gh


def repo_create(
    name: str,
    *,
    source_dir: Path,
    visibility: str = "private",
    remote: str = "origin",
    description: str = "",
    owner: Optional[str] = None,
) -> RunResult:
    """
    Create a remote repo via GitHub CLI and push current local repo.
    """
    full_name = f"{owner}/{name}" if owner else name
    vis_flag = "--private" if visibility.lower() == "private" else "--public"

    args = [
        "repo",
        "create",
        full_name,
        vis_flag,
        "--source",
        str(source_dir),
        "--remote",
        remote,
        "--push",
        "-y",
    ]
    if description:
        args.extend(["--description", description])
    return gh(args, cwd=source_dir)


def pr_create(
    *,
    head: str,
    base: str,
    title: str,
    body: str = "",
    draft: bool = False,
    cwd: Path,
) -> int:
    """
    Create a PR and return its number.
    """
    args = ["pr", "create", "--head", head, "--base", base, "--title", title]
    if body:
        args.extend(["--body", body])
    if draft:
        args.append("--draft")
    gh(args, cwd=cwd)

    num = pr_number_for_branch(head, cwd=cwd)
    if num is None:
        raise RuntimeError("PR was created but the PR number could not be resolved.")
    return num


def pr_number_for_branch(head: str, *, cwd: Path) -> Optional[int]:
    """Return PR number for a head branch (first open PR), or None."""
    r = gh(["pr", "list", "--state", "open", "--head", head, "--json", "number"], cwd=cwd)
    try:
        data = json.loads(r.stdout)
        if isinstance(data, list) and data:
            return int(data[0]["number"])
    except Exception:
        return None
    return None


def pr_close(number: int, *, delete_branch: bool = True, cwd: Path) -> None:
    args = ["pr", "close", str(number)]
    if delete_branch:
        args.append("--delete-branch")
    gh(args, cwd=cwd)


def pr_comment(number: int, *, body: str, cwd: Path) -> None:
    gh(["pr", "comment", str(number), "--body", body], cwd=cwd)


def pr_review(number: int, *, body: str = "", approve: bool = True, cwd: Path) -> None:
    args = ["pr", "review", str(number)]
    if approve:
        args.append("--approve")
    if body:
        args.extend(["--body", body])
    gh(args, cwd=cwd)


def pr_view_json(number: int, fields: Sequence[str], *, cwd: Path | None = None) -> dict:
    """
    View a PR and return selected fields as JSON dict (e.g., ["url", "headRefName"]).
    """
    r = gh(["pr", "view", str(number), "--json", ",".join(fields)], cwd=cwd)
    try:
        return json.loads(r.stdout) if r.stdout else {}
    except Exception:
        return {}
