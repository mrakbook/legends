from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional


class DateParseError(ValueError):
    pass


def normalize_git_date(date_str: str) -> str:
    """
    Normalize a date string into 'YYYY-MM-DDTHH:MM:SSZ' (UTC).
    Accepts:
      - 'YYYY-MM-DD'
      - 'YYYY-MM-DD HH:MM[:SS]'
      - 'YYYY-MM-DDTHH:MM[:SS]'
      - with optional 'Z' or '+/-HH:MM' offset

    Naive (no offset) times are treated as local time and converted to UTC.
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

        has_offset = any(x in s[10:] for x in ["+", "-"])
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            local_tz = datetime.now().astimezone().tzinfo or timezone.utc
            dt = dt.replace(tzinfo=local_tz)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as exc:
        raise DateParseError(f"Could not parse date: {date_str!r}") from exc


def build_commit_env(
    date: Optional[str],
    *,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None,
    committer_name: Optional[str] = None,
    committer_email: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build a minimal environment dict for git to apply backdated commit metadata.
    Defaults committer_* to author_* if not explicitly provided.
    """
    env: Dict[str, str] = {}
    if date:
        iso_utc = normalize_git_date(date)
        env["GIT_AUTHOR_DATE"] = iso_utc
        env["GIT_COMMITTER_DATE"] = iso_utc
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
