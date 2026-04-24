#!/usr/bin/env bash
set -euo pipefail

BRIDGE_ROOT="$HOME/WhatsApp-MCP/whatsapp-mcp"
PATCH_LOCALHOST=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bridge-root) BRIDGE_ROOT="$2"; shift 2 ;;
    --patch-localhost) PATCH_LOCALHOST=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

BRIDGE_DIR="$BRIDGE_ROOT/whatsapp-bridge"
MAIN_GO="$BRIDGE_DIR/main.go"
OUT_DIR="$BRIDGE_ROOT/build-tmp"
OUT_BIN="$OUT_DIR/whatsapp-bridge"

[[ -d "$BRIDGE_DIR" ]] || { echo "Bridge dir not found: $BRIDGE_DIR" >&2; exit 2; }
[[ -f "$MAIN_GO" ]] || { echo "main.go not found: $MAIN_GO" >&2; exit 2; }

if [[ "$PATCH_LOCALHOST" == "1" ]]; then
  if grep -q 'fmt.Sprintf(":%d", port)' "$MAIN_GO"; then
    cp "$MAIN_GO" "$MAIN_GO.bak"
    python3 - "$MAIN_GO" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
s = s.replace('fmt.Sprintf(":%d", port)', 'fmt.Sprintf("127.0.0.1:%d", port)')
p.write_text(s)
PY
    echo "Patch localhost aplicado. Backup: $MAIN_GO.bak"
  else
    echo "Patch localhost nao aplicado: padrao esperado nao encontrado ou ja alterado."
  fi
fi

mkdir -p "$OUT_DIR"
cd "$BRIDGE_DIR"
export CGO_ENABLED=1
go mod download
go build -ldflags="-s -w" -o "$OUT_BIN" .
ls -lh "$OUT_BIN"

