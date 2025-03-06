#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
	cat <<'USAGE'
Usage: scripts/install.sh [--venv .venv] [--python python3] [--dev]
  --venv <path>     Path to virtualenv directory (default: .venv)
  --python <bin>    Python interpreter to use (default: python3)
  --dev             Install dev extras (ruff, black, pytest, mypy)
Examples:
  scripts/install.sh
  scripts/install.sh --dev
  scripts/install.sh --venv .env --python python3.11
USAGE
}

VENV=".venv"
PYBIN="python3"
DEV=0

while [[ $# -gt 0 ]]; do
	case "$1" in
	-h | --help)
		usage
		exit 0
		;;
	--venv)
		VENV="${2:-}"
		shift 2
		;;
	--python)
		PYBIN="${2:-}"
		shift 2
		;;
	--dev)
		DEV=1
		shift
		;;
	*)
		echo "Unknown arg: $1" >&2
		usage
		exit 2
		;;
	esac
done

have() { command -v "$1" >/dev/null 2>&1; }

if ! have "$PYBIN"; then
	echo "ERROR: Python not found: $PYBIN" >&2
	exit 1
fi

echo "==> Creating virtualenv at: $VENV (python = $PYBIN)"
"$PYBIN" -m venv "$VENV"

source "$VENV/bin/activate"

echo "==> Upgrading pip"
python -m pip install -U pip

if ((DEV)); then
	echo "==> Installing package (editable) with dev extras"
	python -m pip install -e ".[dev]"
else
	echo "==> Installing package (editable)"
	python -m pip install -e .
fi

echo
echo "✅ Done."
echo "To activate:  source $VENV/bin/activate"
echo "To test CLI:  python -m legends --help  (or: legends --help)"
