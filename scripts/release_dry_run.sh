#!/usr/bin/env bash
set -euo pipefail

VENV="${VENV:-.venv-release-dryrun}"

python3 -m venv "$VENV"
source "$VENV/bin/activate"

python -m pip install -U pip
python -m pip install python-semantic-release build

echo "==> semantic-release NO-OP dry run"
semantic-release --noop -vv version --print
