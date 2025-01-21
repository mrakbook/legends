from __future__ import annotations

import contextlib
import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence, Tuple, Optional

from .exceptions import CommandError, ToolNotFound, DateParseError

LOG = logging.getLogger("legends")
_handler = logging.StreamHandler()
_formatter = logging.Formatter("[%(levelname)s] %(message)s")
_handler.setFormatter(_formatter)
LOG.addHandler(_handler)
LOG.setLevel(logging.INFO)


def ensure_tool(name: str, hint: str | None = None) -> None:
    """Ensure an external tool is available on PATH."""
    if shutil.which(name) is None:
        raise ToolNotFound(
            name,
            hint=(hint or f"Install {name!r} and ensure it is available on PATH."),
        )


@dataclass
class RunResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str


def _run(
    cmd: Sequence[str],
    *,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture: bool = True,
) -> RunResult:
    """Run a command and optionally raise CommandError on failure."""
    LOG.debug("RUN: %s", " ".join(cmd))
    kwargs = {
        "cwd": str(cwd) if cwd else None,
        "env": env,
        "text": True,
    }
    if capture:
        kwargs.update({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE})
    else:
        kwargs.update({"stdout": None, "stderr": None})

    proc = subprocess.run(list(cmd), **kwargs)
    out, err = (proc.stdout or ""), (proc.stderr or "")
    if check and proc.returncode != 0:
        raise CommandError(list(cmd), proc.returncode, out, err)
    return RunResult(list(cmd), proc.returncode, out, err)


def git(args: Sequence[str], **kwargs) -> RunResult:
    ensure_tool("git", "See https://git-scm.com/downloads")
    return _run(["git", *args], **kwargs)


def gh(args: Sequence[str], **kwargs) -> RunResult:
    ensure_tool("gh", "See https://cli.github.com/")
    return _run(["gh", *args], **kwargs)


def normalize_git_date(date_str: str) -> str:
    """
    Normalize input into 'YYYY-MM-DDTHH:MM:SSZ' (UTC).

    Accepts:
      - YYYY-MM-DD
      - YYYY-MM-DD HH:MM[:SS]
      - YYYY-MM-DDTHH:MM[:SS]
      - with optional 'Z' or '+/-HH:MM' offset

    Naive (no offset) times are treated as *local time* and converted to UTC.
    """
    if not date_str:
        raise DateParseError("Empty date string")

    s = date_str.strip().replace(" ", "T")
    if len(s) == 10 and s.count("-") == 2:
        s = s + "T00:00:00"

    try:
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s[:-1])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            local_tz = datetime.now().astimezone().tzinfo or timezone.utc
            dt = dt.replace(tzinfo=local_tz)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as exc:
        raise DateParseError(f"Could not parse date: {date_str!r}") from exc


def build_commit_env(
    base_env: dict[str, str] | None,
    *,
    date: str | None = None,
    author_name: str | None = None,
    author_email: str | None = None,
    committer_name: str | None = None,
    committer_email: str | None = None,
) -> dict[str, str]:
    """Return an env dict with GIT_* variables applied for a dated commit.

    If committer_* is not provided, we default it to author_* to guarantee that
    both the author and committer identities match (important for GitHub UI).
    """
    env = dict(os.environ if base_env is None else base_env)
    if date:
        normalized = normalize_git_date(date)
        env["GIT_AUTHOR_DATE"] = normalized
        env["GIT_COMMITTER_DATE"] = normalized

    if author_name:
        env["GIT_AUTHOR_NAME"] = author_name
    if author_email:
        env["GIT_AUTHOR_EMAIL"] = author_email

    if not committer_name and author_name:
        committer_name = author_name
    if not committer_email and author_email:
        committer_email = author_email

    if committer_name:
        env["GIT_COMMITTER_NAME"] = committer_name
    if committer_email:
        env["GIT_COMMITTER_EMAIL"] = committer_email
    return env


def resolve_github_identity(prefer_verified: bool = True) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve the current GitHub identity from the authenticated `gh` CLI.

    Returns: (name, email) where email is either a verified primary email
    (when token has `user:email` scope) or the ID-based noreply
    '<id>+<login>@users.noreply.github.com'. On failure, returns (None, None).
    """
    try:
        ensure_tool("gh", "See https://cli.github.com/")
        login = gh(["api", "user", "--jq", ".login"]).stdout.strip()
        uid = gh(["api", "user", "--jq", ".id"]).stdout.strip()
        name = gh(["api", "user", "--jq", ".name // \"\""]).stdout.strip() or login

        email: Optional[str] = None
        if prefer_verified:
            try:
                email = gh(
                    ["api", "user/emails", "--jq", "map(select(.primary==true and .verified==true)) | .[0].email"]
                ).stdout.strip() or None
            except CommandError:
                email = None

        if not email:
            if login and uid:
                email = f"{uid}+{login}@users.noreply.github.com"
            elif login:
                email = f"{login}@users.noreply.github.com"
        return (name, email)
    except Exception:
        return (None, None)


def resolve_github_login() -> Optional[str]:
    """Return the authenticated GitHub username (login), or None on failure."""
    try:
        ensure_tool("gh", "See https://cli.github.com/")
        login = gh(["api", "user", "--jq", ".login"]).stdout.strip()
        return login or None
    except Exception:
        return None


@contextlib.contextmanager
def pushd(path: str | Path) -> Iterator[None]:
    """Temporarily chdir to `path`."""
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def json_loads(s: str) -> dict:
    try:
        return json.loads(s) if s else {}
    except json.JSONDecodeError:
        return {}
