from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .exceptions import ConfigError


@dataclass
class AppConfig:
    base_branch: str = "main"
    remote_name: str = "origin"

    visibility: str = "private"
    owner: str | None = None

    author_name: str | None = None
    author_email: str | None = None
    committer_name: str | None = None
    committer_email: str | None = None

    token_env: str = "GITHUB_TOKEN"

    dry_run: bool = False

    def visibility_flag(self) -> str:
        return "--private" if self.visibility.lower() == "private" else "--public"


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except Exception as exc:
        raise ConfigError(
            f"PyYAML not installed but YAML config requested: {path}. "
            "Install with `pip install pyyaml`, or omit the YAML file."
        ) from exc
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:
        raise ConfigError(f"Failed to read YAML config: {path}") from exc


def load_config(yaml_path: str | None = None) -> AppConfig:
    """
    Load configuration from (optional) YAML file and environment variables.

    Precedence: CLI args (handled in cli.py) > env vars > YAML > defaults.
    """
    cfg = AppConfig()

    if yaml_path:
        p = Path(yaml_path)
        if not p.exists():
            raise ConfigError(f"Config file not found: {p}")
        data = _read_yaml(p)
        if "base_branch" in data:
            cfg.base_branch = str(data["base_branch"])
        if "remote_name" in data:
            cfg.remote_name = str(data["remote_name"])
        if "visibility" in data:
            vis = str(data["visibility"]).lower()
            if vis not in {"private", "public"}:
                raise ConfigError("visibility must be 'private' or 'public'")
            cfg.visibility = vis
        if "owner" in data:
            cfg.owner = str(data["owner"]) if data["owner"] else None
        if "author" in data and isinstance(data["author"], dict):
            cfg.author_name = data["author"].get("name") or cfg.author_name
            cfg.author_email = data["author"].get("email") or cfg.author_email
        if "committer" in data and isinstance(data["committer"], dict):
            cfg.committer_name = data["committer"].get("name") or cfg.committer_name
            cfg.committer_email = data["committer"].get("email") or cfg.committer_email
        if "token_env" in data:
            cfg.token_env = str(data["token_env"])

    cfg.base_branch = os.getenv("GHB_BASE_BRANCH", cfg.base_branch)
    cfg.remote_name = os.getenv("GHB_REMOTE", cfg.remote_name)
    cfg.visibility = os.getenv("GHB_VISIBILITY", cfg.visibility).lower()
    cfg.owner = os.getenv("GHB_OWNER", cfg.owner) or cfg.owner

    cfg.author_name = os.getenv("GIT_AUTHOR_NAME", cfg.author_name) or cfg.author_name
    cfg.author_email = os.getenv("GIT_AUTHOR_EMAIL", cfg.author_email) or cfg.author_email
    cfg.committer_name = os.getenv("GIT_COMMITTER_NAME", cfg.committer_name) or cfg.committer_name
    cfg.committer_email = os.getenv("GIT_COMMITTER_EMAIL", cfg.committer_email) or cfg.committer_email

    cfg.token_env = os.getenv("GHB_TOKEN_ENV", cfg.token_env)

    dry = os.getenv("GHB_DRY_RUN")
    if isinstance(dry, str) and dry.strip():
        cfg.dry_run = dry.strip().lower() in {"1", "true", "yes", "on"}

    if cfg.visibility not in {"private", "public"}:
        raise ConfigError("GHB_VISIBILITY must be 'private' or 'public'")

    return cfg
