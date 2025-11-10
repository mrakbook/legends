#!/usr/bin/env bash
set -euo pipefail

# Build a single-file legends binary for macOS using PyInstaller.
# Produces:
#   dist/legends-darwin-arm64  (on Apple Silicon)
#   dist/legends-darwin-amd64  (on Intel)
# and matching .sha256 files.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ARCH="$(uname -m)"
case "$ARCH" in
  arm64)  OUT_ARCH="darwin-arm64" ;;
  x86_64) OUT_ARCH="darwin-amd64" ;;
  *) echo "Unsupported macOS arch: $ARCH" >&2; exit 1 ;;
esac

# Prefer the project venv if present
if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python3 -m pip install -U pip
python3 -m pip install -e .
python3 -m pip install pyinstaller

# Ensure entrypoint exists for PyInstaller
if [[ ! -f "entrypoints/legends_app.py" ]]; then
  echo "ERROR: entrypoints/legends_app.py not found. Create it as shown in the docs." >&2
  exit 2
fi

# Build
pyinstaller --onefile --name legends --paths src entrypoints/legends_app.py

# Prepare outputs
mkdir -p dist
cp "dist/legends" "dist/legends-${OUT_ARCH}"
( cd dist && shasum -a 256 "legends-${OUT_ARCH}" > "legends-${OUT_ARCH}.sha256" )

echo
echo "✅ Built:"
echo "  dist/legends-${OUT_ARCH}"
echo "  dist/legends-${OUT_ARCH}.sha256"
