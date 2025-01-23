from __future__ import annotations


class BackdateError(Exception):
    """Base exception for legends."""


class ToolNotFound(BackdateError):
    """Raised when a required tool (git/gh) is not available on PATH."""
    def __init__(self, tool: str, hint: str | None = None):
        self.tool = tool
        self.hint = hint or ""
        super().__init__(self.__str__())

    def __str__(self) -> str:
        base = f"Required tool not found on PATH: {self.tool!r}"
        return f"{base}. {self.hint}" if self.hint else base


class CommandError(BackdateError):
    """Raised when a subprocess returns a non-zero exit code."""
    def __init__(self, cmd: list[str] | tuple[str, ...], returncode: int,
                 stdout: str = "", stderr: str = ""):
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(self.__str__())

    def __str__(self) -> str:
        lines = [
            f"Command failed (exit {self.returncode}): {' '.join(self.cmd)}",
        ]
        if self.stdout:
            lines.append(f"--- stdout ---\n{self.stdout.strip()}")
        if self.stderr:
            lines.append(f"--- stderr ---\n{self.stderr.strip()}")
        return "\n".join(lines)


class ConfigError(BackdateError):
    """Raised for configuration loading/validation issues."""


class DateParseError(BackdateError):
    """Raised when a date string cannot be normalized for git env."""


class GitError(BackdateError):
    """Generic Git failure wrapper."""


class GitHubCLIError(BackdateError):
    """Generic GitHub CLI (`gh`) failure wrapper."""
