from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping, Optional, Sequence


@dataclass
class RunResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str


class CoreCommandError(RuntimeError):
    """Raised when an external command fails."""

    def __init__(self, cmd: Sequence[str], returncode: int, stdout: str = "", stderr: str = ""):
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(self.__str__())

    def __str__(self) -> str:
        lines = [f"Command failed (exit {self.returncode}): {' '.join(self.cmd)}"]
        if self.stdout:
            lines.append(f"--- stdout ---\n{self.stdout.strip()}")
        if self.stderr:
            lines.append(f"--- stderr ---\n{self.stderr.strip()}")
        return "\n".join(lines)


def ensure_tool(name: str, hint: str | None = None) -> None:
    """Ensure a required tool is on PATH."""
    if shutil.which(name) is None:
        h = f" Install '{name}' and ensure it is available on PATH." if hint is None else f" {hint}"
        raise CoreCommandError([name, "--version"], 127, "", f"Required tool not found: {name}.{h}")


def _run(
    cmd: Sequence[str],
    *,
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    check: bool = True,
    capture: bool = True,
) -> RunResult:
    """Run a command and return a structured result (raises on failure if check=True)."""
    full_env: MutableMapping[str, str] = dict(os.environ)
    if env:
        full_env.update(env)

    kwargs: dict = {"cwd": str(cwd) if cwd else None, "env": full_env, "text": True}
    if capture:
        kwargs.update({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE})
    proc = subprocess.run(list(cmd), **kwargs)

    out, err = proc.stdout or "", proc.stderr or ""
    if check and proc.returncode != 0:
        raise CoreCommandError(list(cmd), proc.returncode, out, err)
    return RunResult(list(cmd), proc.returncode, out, err)


def git(args: Sequence[str], **kwargs) -> RunResult:
    """Run a git command."""
    ensure_tool("git", "See https://git-scm.com/downloads")
    return _run(["git", *args], **kwargs)


def gh(args: Sequence[str], **kwargs) -> RunResult:
    """Run a GitHub CLI command."""
    ensure_tool("gh", "See https://cli.github.com/")
    return _run(["gh", *args], **kwargs)
