"""
legends
-------

Local-first automation for simulating historical GitHub activity via
backdated git commits, branches, and merge commits, plus PR orchestration
through the GitHub CLI.

Public API surface: the CLI (see `cli.py`).
"""

from importlib.metadata import version as _get_version, PackageNotFoundError

try:
    __version__ = _get_version(__package__ or "legends")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__"]
