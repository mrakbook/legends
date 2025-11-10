#!/usr/bin/env bash
set -euo pipefail

# Simple macOS installer for legends
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/mrakbook/legends/main/install.sh | bash
# Options:
#   LEGENDS_VERSION=vX.Y.Z  (default: latest)
#   LEGENDS_BIN_DIR=/usr/local/bin  (default: auto: /opt/homebrew/bin or /usr/local/bin)

OWNER="${LEGENDS_OWNER:-mrakbook}"
REPO="${LEGENDS_REPO:-legends}"
VERSION="${LEGENDS_VERSION:-}"
BIN_DIR="${LEGENDS_BIN_DIR:-}"

die() { echo "ERROR: $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

OS="$(uname -s)"
ARCH_RAW="$(uname -m)"

[[ "$OS" == "Darwin" ]] || die "This installer supports macOS only."

case "$ARCH_RAW" in
  arm64) ARCH="arm64" ;;
  x86_64) ARCH="amd64" ;;
  *) die "Unsupported CPU architecture: $ARCH_RAW" ;;
esac

# Resolve install directory
if [[ -z "${BIN_DIR}" ]]; then
  if [[ -d "/opt/homebrew/bin" ]]; then
    BIN_DIR="/opt/homebrew/bin"
  else
    BIN_DIR="/usr/local/bin"
  fi
fi

# Resolve version (latest if not provided)
if [[ -z "${VERSION}" ]]; then
  echo "Resolving latest version..."
  API_URL="https://api.github.com/repos/${OWNER}/${REPO}/releases/latest"
  if have curl; then
    VERSION="$(curl -fsSL "$API_URL" | grep -m1 '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')"
  else
    die "curl is required to resolve latest version"
  fi
  [[ -n "$VERSION" ]] || die "Failed to resolve latest version from GitHub API"
fi

ASSET="legends-darwin-${ARCH}"
BASE_DL="https://github.com/${OWNER}/${REPO}/releases/download/${VERSION}"

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo "Downloading ${ASSET} (${VERSION}) ..."
curl -fL -o "${TMPDIR}/${ASSET}" "${BASE_DL}/${ASSET}"

# Try to download checksum (best-effort)
if curl -fsSL -o "${TMPDIR}/${ASSET}.sha256" "${BASE_DL}/${ASSET}.sha256"; then
  echo "Verifying checksum..."
  (cd "${TMPDIR}" && shasum -a 256 -c "${ASSET}.sha256")
else
  echo "No checksum file found; skipping verification."
fi

chmod +x "${TMPDIR}/${ASSET}"

# Install
INSTALL_PATH="${BIN_DIR}/legends"
if [[ -w "${BIN_DIR}" ]]; then
  mv -f "${TMPDIR}/${ASSET}" "${INSTALL_PATH}"
else
  echo "Elevating privileges to write to ${BIN_DIR} ..."
  sudo mv -f "${TMPDIR}/${ASSET}" "${INSTALL_PATH}"
fi

echo "Installed: ${INSTALL_PATH}"
echo
echo "Run: legends --help"
