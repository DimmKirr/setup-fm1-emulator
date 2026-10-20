#!/usr/bin/env bash
set -euo pipefail

REPO="joakimeriksson/fm1-emu"
VERSION="${1:-latest}"
INSTALL_DIR="${FM1_EMULATOR_HOME:-$HOME/.fm1-emulator}"

if [ "$VERSION" = "latest" ]; then
  VERSION=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
    | grep -o '"tag_name": *"[^"]*"' | cut -d'"' -f4)
  echo "Latest version: $VERSION"
fi

SEMVER="${VERSION#v}"

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64)  PLATFORM="linux-x86_64" ;;
  Linux-aarch64) PLATFORM="linux-arm64"   ;;
  Darwin-arm64)  PLATFORM="macos-arm64"   ;;
  *) echo "Unsupported platform: $(uname -s)-$(uname -m)"; exit 1 ;;
esac

if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/VERSION" ]; then
  INSTALLED=$(cat "$INSTALL_DIR/VERSION")
  if [ "$INSTALLED" = "$VERSION" ]; then
    echo "Already installed: $VERSION"
    echo ""
    echo "Add to your shell profile:"
    echo "  export PATH=\"$INSTALL_DIR/bin:\$PATH\""
    exit 0
  fi
fi

ASSET="fm1-emu-${SEMVER}-${PLATFORM}.tar.gz"
URL="https://github.com/$REPO/releases/download/$VERSION/$ASSET"

echo "Installing fm1-emu $VERSION ($PLATFORM) to $INSTALL_DIR..."

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "Downloading $URL..."
curl -fSL --retry 3 -o "$TMP/$ASSET" "$URL"

echo "Extracting binary..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/bin"
tar -xzf "$TMP/$ASSET" -C "$INSTALL_DIR/bin/"
chmod +x "$INSTALL_DIR/bin/fm1-emu"

echo "Cloning source at $VERSION..."
git clone --depth 1 --branch "$VERSION" \
  "https://github.com/$REPO.git" \
  "$INSTALL_DIR/source"

echo "$VERSION" > "$INSTALL_DIR/VERSION"

echo ""
echo "FM1 emulator installed to $INSTALL_DIR"
echo ""
echo "Add to your shell profile:"
echo "  export PATH=\"$INSTALL_DIR/bin:\$PATH\""
