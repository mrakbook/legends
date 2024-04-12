from __future__ import annotations

import argparse

from . import create_repo as _create_repo
from . import create_branch as _create_branch
from . import commit as _commit
from . import open_pr as _open_pr
from . import merge_pr as _merge_pr
from . import commit_all as _commit_all


def register_all(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """
    Register all subcommands onto an argparse subparsers object.
    """
    _create_repo.add_parser(subparsers)
    _create_branch.add_parser(subparsers)
    _commit.add_parser(subparsers)
    _open_pr.add_parser(subparsers)
    _merge_pr.add_parser(subparsers)
    _commit_all.add_parser(subparsers)
