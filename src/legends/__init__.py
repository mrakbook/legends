"""
legends
-------

Local-first automation for simulating historical GitHub activity via
backdated git commits, branches, and merge commits, plus PR orchestration
through the GitHub CLI.

This package intentionally keeps dependencies to the Python stdlib and
shells out to `git` and `gh`.

Public API surface: the CLI (see `cli.py`).
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
