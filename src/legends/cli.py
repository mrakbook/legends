from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Optional

from .config import AppConfig, load_config
from .exceptions import BackdateError, CommandError
from .utils import (
    RunResult,
    build_commit_env,
    gh,
    git,
    json_loads,
    pushd,
    ensure_tool,
    resolve_github_identity,
    resolve_github_login,
    LOG,
)


def _bool_flag(parser: argparse.ArgumentParser, name: str, *, default: bool, help: str):
    """
    Register a --<name>/--no-<name> boolean flag pair.

    We always store it in argparse's Namespace using a valid Python identifier:
    e.g. name='delete-branch' -> dest='delete_branch' -> ns.delete_branch (bool)
    """
    dest = name.replace("-", "_")
    g = parser.add_mutually_exclusive_group()
    g.add_argument(f"--{name}", dest=dest, action="store_true", help=help)
    g.add_argument(f"--no-{name}", dest=dest, action="store_false", help=f"Disable {help}")
    parser.set_defaults(**{dest: default})


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="legends",
        description="Automate historical GitHub repo activity with backdated commits and merges.",
    )
    p.add_argument("--config", help="Optional YAML config file.")
    p.add_argument("--dry-run", action="store_true", help="Print actions without executing.")
    p.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity.")

    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("create-repo", help="Create repo with a backdated initial commit.")
    pr.add_argument("name", help="Repository name (will create a directory).")
    pr.add_argument("--owner", help="GitHub owner/org (optional).")
    pr.add_argument("--date", help="Initial commit date (e.g., '2024-12-01 12:00:00').")
    visibility = pr.add_mutually_exclusive_group()
    visibility.add_argument("--private", action="store_true", help="Create as private.")
    visibility.add_argument("--public", action="store_true", help="Create as public.")
    pr.add_argument("--description", default="", help="Repository description.")
    pr.add_argument("--readme", default="README.md", help="Initial README filename.")
    pr.add_argument("--branch", default=None, help="Main branch name (default from config).")

    pb = sub.add_parser("create-branch", help="Create a branch with a backdated empty commit.")
    pb.add_argument("branch", help="New branch name.")
    pb.add_argument("--base", default=None, help="Base branch (default from config).")
    pb.add_argument("--date", required=True, help="Branch 'creation' commit date.")
    pb.add_argument("--message", default=None, help="Initial commit message (optional).")
    pb.add_argument("--push", action="store_true", help="Push the new branch to origin.")

    pc = sub.add_parser("commit", help="Make a backdated commit on a branch.")
    pc.add_argument("--branch", required=True, help="Target branch.")
    pc.add_argument("--date", required=True, help="Commit date.")
    pc.add_argument("--message", required=True, help="Commit message.")
    pc.add_argument("--allow-empty", action="store_true", help="Allow empty commit if no changes.")
    pc.add_argument("--add-all", action="store_true", help="Run 'git add -A' before commit.")
    pc.add_argument("--touch", help="Create/modify this file to ensure a non-empty commit.")
    pc.add_argument("--push", action="store_true", help="Push branch after committing.")

    pp = sub.add_parser("open-pr", help="Open a PR from branch to base via GitHub CLI.")
    pp.add_argument("--branch", required=True, help="Head branch.")
    pp.add_argument("--base", default=None, help="Base branch (default from config).")
    pp.add_argument("--title", required=False, help="PR title.")
    pp.add_argument("--body", required=False, help="PR body text.")
    pp.add_argument("--draft", action="store_true", help="Open PR as draft.")

    pm = sub.add_parser("merge-pr", help="Merge a branch locally with a backdated merge commit.")
    pm.add_argument("--branch", help="Branch to merge (if PR number not given).")
    pm.add_argument("--pr", type=int, help="PR number (optional if branch is provided).")
    pm.add_argument("--base", default=None, help="Base branch (default from config).")
    pm.add_argument("--date", required=True, help="Merge commit date.")
    pm.add_argument("--message", help="Merge commit message override.")
    _bool_flag(pm, "delete-branch", default=True, help="Delete remote branch after merge.")

    pa = sub.add_parser("commit-all", help="Commit -> PR -> backdated merge (one shot).")
    pa.add_argument("--branch", required=True, help="Feature branch.")
    pa.add_argument("--base", default=None, help="Base branch (default from config).")
    pa.add_argument("--commit-date", required=True, help="Commit date.")
    pa.add_argument("--message", required=True, help="Commit message.")
    pa.add_argument("--pr-title", required=False, help="PR title (defaults to commit message).")
    pa.add_argument("--pr-body", required=False, help="PR body.")
    pa.add_argument("--merge-date", required=True, help="Merge commit date.")
    _bool_flag(pa, "delete-branch", default=True, help="Delete remote branch after merge.")

    return p.parse_args()


def _apply_verbosity(level: int):
    if level >= 2:
        LOG.setLevel(logging.DEBUG)
    elif level == 1:
        LOG.setLevel(logging.INFO)
    else:
        LOG.setLevel(logging.WARNING)


def _resolve_config(ns: argparse.Namespace) -> AppConfig:
    cfg = load_config(ns.config) if ns.config else load_config(None)
    if ns.dry_run:
        cfg.dry_run = True
    return cfg


def _hydrate_identity(cfg: AppConfig) -> AppConfig:
    """
    Ensure cfg has author/committer identity. If not provided via YAML/env,
    resolve from `gh`. Committer.name is set to the GitHub *username*.
    """
    if not cfg.author_name or not cfg.author_email:
        gh_name, gh_email = resolve_github_identity()
        if not cfg.author_name and gh_name:
            cfg.author_name = gh_name
        if not cfg.author_email and gh_email:
            cfg.author_email = gh_email

    login = resolve_github_login()
    if not cfg.committer_name:
        cfg.committer_name = login or cfg.author_name
    if not cfg.committer_email:
        cfg.committer_email = cfg.author_email

    LOG.debug(
        "Identity -> author: %r <%r>, committer: %r <%r>",
        cfg.author_name, cfg.author_email, cfg.committer_name, cfg.committer_email
    )
    return cfg


def _maybe_touch(path: str | None):
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write("")


def _exec_git(
    args: list[str],
    *,
    dry: bool,
    env: dict | None = None,
    cwd: str | Path | None = None
) -> RunResult | None:
    LOG.info("git %s", " ".join(args))
    if dry:
        return None
    return git(args, env=env, cwd=cwd)


def _exec_gh(
    args: list[str],
    *,
    dry: bool,
    env: dict | None = None,
    cwd: str | Path | None = None
) -> RunResult | None:
    LOG.info("gh %s", " ".join(args))
    if dry:
        return None
    return gh(args, env=env, cwd=cwd)


def _commit_env(cfg: AppConfig, date: Optional[str]) -> dict:
    return build_commit_env(
        os.environ,
        date=date,
        author_name=cfg.author_name,
        author_email=cfg.author_email,
        committer_name=cfg.committer_name or cfg.author_name,
        committer_email=cfg.committer_email or cfg.author_email,
    )

def cmd_create_repo(ns: argparse.Namespace, cfg: AppConfig) -> None:
    ensure_tool("git")
    ensure_tool("gh")

    repo_name = ns.name
    owner = ns.owner or cfg.owner
    base_branch = ns.branch or cfg.base_branch

    visibility = "public" if getattr(ns, "public", False) else "private" if getattr(ns, "private", False) else cfg.visibility
    vis_flag = "--public" if visibility == "public" else "--private"

    repo_dir = Path(repo_name).resolve()

    if repo_dir.exists() and any(repo_dir.iterdir()):
        raise BackdateError(f"Target directory already exists and is not empty: {repo_dir}")

    repo_dir.mkdir(parents=True, exist_ok=True)
    with pushd(repo_dir):
        _exec_git(["init", "."], dry=cfg.dry_run)
        readme = Path(ns.readme)
        if not readme.exists():
            readme.write_text(f"# {repo_name}\n\n{ns.description}\n", encoding="utf-8")
        _exec_git(["add", readme.name], dry=cfg.dry_run)

        env = _commit_env(cfg, ns.date)
        _exec_git(["commit", "-m", "Initial commit"], dry=cfg.dry_run, env=env)
        if base_branch and base_branch != "master":
            _exec_git(["branch", "-M", base_branch], dry=cfg.dry_run)

        owner_prefix = f"{owner}/" if owner else ""
        args = [
            "repo", "create", f"{owner_prefix}{repo_name}",
            vis_flag, "--source=.", "--remote", cfg.remote_name, "--push", "-y",
        ]
        if ns.description:
            args.extend(["--description", ns.description])
        _exec_gh(args, dry=cfg.dry_run)


def cmd_create_branch(ns: argparse.Namespace, cfg: AppConfig) -> None:
    base = ns.base or cfg.base_branch
    msg = ns.message or f"chore({ns.branch}): branch birth"
    _exec_git(["checkout", base], dry=cfg.dry_run)
    _exec_git(["checkout", "-b", ns.branch], dry=cfg.dry_run)
    env = _commit_env(cfg, ns.date)
    _exec_git(["commit", "--allow-empty", "-m", msg], dry=cfg.dry_run, env=env)
    if getattr(ns, "push", False):
        try:
            _exec_git(["push", "-u", cfg.remote_name, ns.branch], dry=cfg.dry_run)
        except CommandError:
            _exec_git(["push", cfg.remote_name, ns.branch], dry=cfg.dry_run)


def cmd_commit(ns: argparse.Namespace, cfg: AppConfig) -> None:
    _exec_git(["checkout", ns.branch], dry=cfg.dry_run)
    if ns.touch:
        _maybe_touch(ns.touch)
        _exec_git(["add", ns.touch], dry=cfg.dry_run)
    if ns.add_all:
        _exec_git(["add", "-A"], dry=cfg.dry_run)
    args = ["commit", "-m", ns.message]
    if ns.allow_empty:
        args.insert(1, "--allow-empty")
    env = _commit_env(cfg, ns.date)
    _exec_git(args, dry=cfg.dry_run, env=env)
    if getattr(ns, "push", False):
        try:
            _exec_git(["push", cfg.remote_name, ns.branch], dry=cfg.dry_run)
        except CommandError:
            _exec_git(["push", "-u", cfg.remote_name, ns.branch], dry=cfg.dry_run)


def _get_pr_number_for_branch(branch: str) -> Optional[int]:
    try:
        r = gh(["pr", "list", "--state", "open", "--head", branch, "--json", "number"])
        data = json_loads(r.stdout)
        if isinstance(data, list) and data:
            return int(data[0]["number"])
    except CommandError:
        return None
    return None


def cmd_open_pr(ns: argparse.Namespace, cfg: AppConfig) -> None:
    """
    Push the head branch (setting upstream if needed) and then open a PR.
    This avoids 'Head sha can't be blank' / 'No commits between <base> and <head>' errors
    when creating a PR for a branch that hasn't been pushed yet.
    """
    base = ns.base or cfg.base_branch

    try:
        _exec_git(["rev-parse", "--verify", ns.branch], dry=cfg.dry_run)
    except CommandError as e:
        raise BackdateError(
            f"Branch {ns.branch!r} does not exist locally. Did you run 'create-branch' and 'commit'?"
        ) from e

    try:
        _exec_git(["push", "-u", cfg.remote_name, ns.branch], dry=cfg.dry_run)
    except CommandError:
        _exec_git(["push", cfg.remote_name, ns.branch], dry=cfg.dry_run)
    try:
        diff = git(["rev-list", "--left-right", "--count", f"{base}...{ns.branch}"])
        ahead_behind = (diff.stdout or "0\t0").strip().replace(" ", "\t").split("\t")
        ahead = int(ahead_behind[0]) if ahead_behind else 0
        if ahead == 0:
            LOG.warning(
                "No commits found on %s compared to %s. The PR may be empty.",
                ns.branch, base
            )
    except Exception:
        pass

    args = ["pr", "create", "--head", ns.branch, "--base", base]
    if ns.title:
        args += ["--title", ns.title]
    if ns.body:
        args += ["--body", ns.body]
    if getattr(ns, "draft", False):
        args += ["--draft"]
    _exec_gh(args, dry=cfg.dry_run)


def cmd_merge_pr(ns: argparse.Namespace, cfg: AppConfig) -> None:
    base = ns.base or cfg.base_branch
    branch = ns.branch
    pr_number = ns.pr

    if not pr_number and branch:
        pr_number = _get_pr_number_for_branch(branch)

    _exec_git(["checkout", base], dry=cfg.dry_run)
    _exec_git(["pull", cfg.remote_name, base], dry=cfg.dry_run)

    if not branch:
        if pr_number is None:
            raise BackdateError("Provide --branch or --pr for merge-pr.")
        try:
            r = gh(["pr", "view", str(pr_number), "--json", "headRefName"])
            info = json.loads(r.stdout) if r.stdout else {}
            branch = info.get("headRefName")
        except CommandError:
            raise BackdateError("Could not resolve branch name for PR; pass --branch explicitly.")
    _exec_git(["merge", "--no-ff", "--no-commit", branch], dry=cfg.dry_run)

    default_msg = (
        f"Merge pull request #{pr_number} from {branch}"
        if pr_number
        else f"Merge branch '{branch}' into {base}"
    )
    msg = ns.message or default_msg
    env = _commit_env(cfg, ns.date)
    _exec_git(["commit", "-m", msg], dry=cfg.dry_run, env=env)

    _exec_git(["push", cfg.remote_name, base], dry=cfg.dry_run)

    if getattr(ns, "delete_branch", True):
        if pr_number:
            state = ""
            try:
                info = gh(["pr", "view", str(pr_number), "--json", "state"]).stdout
                data = json_loads(info)
                state = (data.get("state") or "").upper()
            except CommandError:
                state = ""

            if state == "OPEN":
                try:
                    _exec_gh(["pr", "close", str(pr_number), "--delete-branch"], dry=cfg.dry_run)
                except CommandError:
                    _exec_git(["push", cfg.remote_name, "--delete", branch], dry=cfg.dry_run)
            else:
                _exec_git(["push", cfg.remote_name, "--delete", branch], dry=cfg.dry_run)
        else:
            _exec_git(["push", cfg.remote_name, "--delete", branch], dry=cfg.dry_run)


def cmd_commit_all(ns: argparse.Namespace, cfg: AppConfig) -> None:
    base = ns.base or cfg.base_branch
    branch = ns.branch

    exists = False
    try:
        r = git(["rev-parse", "--verify", branch])
        exists = r.returncode == 0
    except CommandError:
        exists = False

    if exists:
        _exec_git(["checkout", branch], dry=cfg.dry_run)
    else:
        _exec_git(["checkout", base], dry=cfg.dry_run)
        _exec_git(["checkout", "-b", branch], dry=cfg.dry_run)

    marker = Path(".backdate_work.txt")
    if not cfg.dry_run:
        marker.write_text(f"{ns.commit_date} :: {ns.message}\n", encoding="utf-8")
    _exec_git(["add", str(marker)], dry=cfg.dry_run)

    env_c = _commit_env(cfg, ns.commit_date)
    _exec_git(["commit", "-m", ns.message], dry=cfg.dry_run, env=env_c)

    try:
        _exec_git(["push", cfg.remote_name, branch], dry=cfg.dry_run)
    except CommandError:
        _exec_git(["push", "-u", cfg.remote_name, branch], dry=cfg.dry_run)

    pr_title = ns.pr_title or ns.message
    args = ["pr", "create", "--head", branch, "--base", base, "--title", pr_title]
    if ns.pr_body:
        args += ["--body", ns.pr_body]
    _exec_gh(args, dry=cfg.dry_run)

    pr_number: Optional[int] = None
    if not cfg.dry_run:
        try:
            r = gh(["pr", "list", "--state", "open", "--head", branch, "--json", "number"])
            data = json_loads(r.stdout)
            if isinstance(data, list) and data:
                pr_number = int(data[0]["number"])
        except CommandError:
            pr_number = None

    _exec_git(["checkout", base], dry=cfg.dry_run)
    _exec_git(["pull", cfg.remote_name, base], dry=cfg.dry_run)
    _exec_git(["merge", "--no-ff", "--no-commit", branch], dry=cfg.dry_run)

    env_m = _commit_env(cfg, ns.merge_date)
    merge_msg = (
        f"Merge pull request #{pr_number} from {branch}"
        if pr_number else f"Merge branch '{branch}' into {base}"
    )
    _exec_git(["commit", "-m", merge_msg], dry=cfg.dry_run, env=env_m)

    if getattr(ns, "delete_branch", True):
        if pr_number:
            state = ""
            try:
                info = gh(["pr", "view", str(pr_number), "--json", "state"]).stdout
                data = json_loads(info)
                state = (data.get("state") or "").upper()
            except CommandError:
                state = ""

            if state == "OPEN":
                try:
                    _exec_gh(["pr", "close", str(pr_number), "--delete-branch"], dry=cfg.dry_run)
                except CommandError:
                    _exec_git(["push", cfg.remote_name, "--delete", branch], dry=cfg.dry_run)
            else:
                _exec_git(["push", cfg.remote_name, "--delete", branch], dry=cfg.dry_run)
        else:
            _exec_git(["push", cfg.remote_name, "--delete", branch], dry=cfg.dry_run)

    _exec_git(["push", cfg.remote_name, base], dry=cfg.dry_run)

def main() -> int:
    ns = _parse_args()
    if ns.verbose >= 2:
        LOG.setLevel(logging.DEBUG)
    elif ns.verbose == 1:
        LOG.setLevel(logging.INFO)
    else:
        LOG.setLevel(logging.WARNING)

    try:
        cfg = _resolve_config(ns)
        cfg = _hydrate_identity(cfg)
        LOG.debug("Config: %s", cfg)

        cmd = ns.cmd.replace("-", "_")
        if cmd == "create_repo":
            cmd_create_repo(ns, cfg)
        elif cmd == "create_branch":
            cmd_create_branch(ns, cfg)
        elif cmd == "commit":
            cmd_commit(ns, cfg)
        elif cmd == "open_pr":
            cmd_open_pr(ns, cfg)
        elif cmd == "merge_pr":
            cmd_merge_pr(ns, cfg)
        elif cmd == "commit_all":
            cmd_commit_all(ns, cfg)
        else:
            raise BackdateError(f"Unknown command: {ns.cmd}")
        return 0
    except BackdateError as e:
        LOG.error(str(e))
        return 2
    except CommandError as e:
        LOG.error(str(e))
        return 3
    except KeyboardInterrupt:
        LOG.error("Interrupted.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
