from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional


class _SafeDict(dict):
    """format_map helper that leaves unknown {placeholders} intact."""
    def __missing__(self, key):
        return "{" + key + "}"


def _render_str(template_str: str, values: Mapping[str, object]) -> str:
    return template_str.format_map(_SafeDict(values))


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


@dataclass(frozen=True)
class TemplateFiles:
    root: Path
    commit_message: str = "commit_message.txt"
    pr_title: str = "pr_title.txt"
    pr_body: str = "pr_body.md"
    review_body: str = "review_body.md"
    merge_message: str = "merge_message.txt"

    def path(self, name: str) -> Path:
        return self.root / name


_TPL_DIR = Path(__file__).resolve().parent
FILES = TemplateFiles(root=_TPL_DIR)


def render_commit_message(
    *,
    summary: str,
    branch: str,
    date: str,
    type_: str = "chore",
    extra: Optional[Mapping[str, object]] = None,
) -> str:
    """
    Render the commit message from file template.

    Template placeholders:
      - {type}   (e.g., feat, fix, chore)
      - {branch}
      - {summary}
      - {date}
    """
    tpl = _read_text(FILES.path(FILES.commit_message))
    values = {
        "type": type_,
        "branch": branch,
        "summary": summary,
        "date": date,
    }
    if extra:
        values.update(extra)
    return _render_str(tpl, values)


def render_pr_title(
    *,
    summary: str,
    extra: Optional[Mapping[str, object]] = None,
) -> str:
    """
    Render PR title.

    Template placeholders:
      - {summary}
    """
    tpl = _read_text(FILES.path(FILES.pr_title))
    values = {"summary": summary}
    if extra:
        values.update(extra)
    return _render_str(tpl, values)


def render_pr_body(
    *,
    summary: str,
    branch: str,
    base: str,
    date: str,
    notes: str = "",
    extra: Optional[Mapping[str, object]] = None,
) -> str:
    """
    Render PR body (Markdown).

    Template placeholders:
      - {summary}
      - {branch}
      - {base}
      - {date}
      - {notes}
    """
    tpl = _read_text(FILES.path(FILES.pr_body))
    values = {
        "summary": summary,
        "branch": branch,
        "base": base,
        "date": date,
        "notes": notes,
    }
    if extra:
        values.update(extra)
    return _render_str(tpl, values)


def render_review_body(
    *,
    notes: str = "",
    today: Optional[str] = None,
    extra: Optional[Mapping[str, object]] = None,
) -> str:
    """
    Render a review body (Markdown).

    Template placeholders:
      - {today} (defaults to today's date in ISO format)
      - {notes}
    """
    tpl = _read_text(FILES.path(FILES.review_body))
    values = {
        "today": today or datetime.now().date().isoformat(),
        "notes": notes,
    }
    if extra:
        values.update(extra)
    return _render_str(tpl, values)


def render_merge_message(
    *,
    base: str,
    branch: str,
    pr_number: Optional[int] = None,
    title: Optional[str] = None,
    extra: Optional[Mapping[str, object]] = None,
) -> str:
    """
    Render merge commit message.

    File template uses:
      - {prefix}  -> computed line referencing either PR or branch
      - {title}   -> optional title (defaults to "Merge {branch}")
    """
    if pr_number is not None:
        prefix = f"Merge pull request #{pr_number} from {branch}"
    else:
        prefix = f"Merge branch '{branch}' into {base}"

    tpl = _read_text(FILES.path(FILES.merge_message))
    values = {
        "prefix": prefix,
        "title": title or f"Merge {branch}",
        "base": base,
        "branch": branch,
        "pr_number": pr_number if pr_number is not None else "",
    }
    if extra:
        values.update(extra)
    return _render_str(tpl, values)
