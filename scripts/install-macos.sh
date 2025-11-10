#!/usr/bin/env bash
# Install legends on macOS like terraform/kubectl:
#   curl -fsSL https://raw.githubusercontent.com/mrakbook/legends/main/scripts/install-macos.sh | bash
# Optional: VERSION=0.1.0 PREFIX=/usr/local bash install-macos.sh

set -euo pipefail

REPO="${REPO:-mrakbook/legends}"
VERSION="${VERSION:-}"
BIN_NAME="${BIN_NAME:-legends}"

# Detect arch → asset suffix
ARCH="$(uname -m)"
case "$ARCH" in
  arm64)  SUFFIX="darwin-arm64" ;;
  x86_64) SUFFIX="darwin-amd64" ;;
  *)
    echo "Unsupported macOS arch: $ARCH" >&2
    exit 1
    ;;
esac

# Choose install dir (can override with PREFIX or BIN_DIR)
DEFAULT_APPLE="/opt/homebrew/bin"
DEFAULT_INTEL="/usr/local/bin"
if [[ -n "${BIN_DIR:-}" ]]; then
  TARGET_DIR="$BIN_DIR"
else
  if [[ -d "$DEFAULT_APPLE" ]]; then
    TARGET_DIR="$DEFAULT_APPLE"
  else
    TARGET_DIR="$DEFAULT_INTEL"
  fi
fi

ASSET="${BIN_NAME}-${SUFFIX}"

if [[ -n "$VERSION" ]]; then
  BASE_URL="https://github.com/${REPO}/releases/download/v${VERSION}"
else
  BASE_URL="https://github.com/${REPO}/releases/latest/download"
fi

TMPDIR="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

echo "==> Downloading ${ASSET} from ${BASE_URL}"
curl -fsSL -o "${TMPDIR}/${ASSET}"         "${BASE_URL}/${ASSET}"
curl -fsSL -o "${TMPDIR}/${ASSET}.sha256"  "${BASE_URL}/${ASSET}.sha256"

echo "==> Verifying checksum"
( cd "${TMPDIR}" && shasum -a 256 -c "${ASSET}.sha256" )

chmod +x "${TMPDIR}/${ASSET}"

echo "==> Installing to ${TARGET_DIR}/${BIN_NAME}"
if [[ -w "$TARGET_DIR" ]]; then
  install -m 0755 "${TMPDIR}/${ASSET}" "${TARGET_DIR}/${BIN_NAME}"
else
  echo "    (elevating with sudo)"
  sudo install -m 0755 "${TMPDIR}/${ASSET}" "${TARGET_DIR}/${BIN_NAME}"
fi

echo
echo "✅ Installed: $(command -v ${BIN_NAME})"
echo "   Version check:"
set +e
"${BIN_NAME}" --help >/dev/null 2>&1 || true
set -e
