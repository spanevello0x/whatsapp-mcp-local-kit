#!/usr/bin/env bash
set -euo pipefail

PROFILES_DIR="$HOME/Documents/WhatsApp MCP Profiles"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profiles-dir) PROFILES_DIR="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BRIDGE_SOURCE="$REPO_ROOT/vendor/lharries-whatsapp-mcp/whatsapp-bridge"
BIN_DIR="$PROFILES_DIR/bin"
OUT_BIN="$BIN_DIR/whatsapp-bridge"

[[ -d "$BRIDGE_SOURCE" ]] || { echo "Bridge source nao encontrado: $BRIDGE_SOURCE" >&2; exit 2; }
command -v go >/dev/null 2>&1 || { echo "go nao encontrado. Rode scripts/install-dependencies-macos.sh --install"; exit 2; }
command -v clang >/dev/null 2>&1 || { echo "clang nao encontrado. Instale Xcode Command Line Tools."; exit 2; }

mkdir -p "$BIN_DIR"

cd "$BRIDGE_SOURCE"
export CGO_ENABLED=1
go mod download
go build -ldflags="-s -w" -o "$OUT_BIN" .
chmod +x "$OUT_BIN"
ls -lh "$OUT_BIN"
