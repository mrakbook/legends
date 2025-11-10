#!/usr/bin/env bash
set -euo pipefail

VENV="${VENV:-.venv-build}"

python3 -m venv "$VENV"
source "$VENV/bin/activate"

python -m pip install -U pip
python -m pip install build

echo "==> Building sdist & wheel..."
python -m build

echo "==> Installing wheel and smoke-testing..."
python -m pip install dist/*.whl
legends --help

echo
echo "✅ Build complete. Artifacts are in ./dist"
