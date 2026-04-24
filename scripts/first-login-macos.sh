#!/usr/bin/env bash
set -euo pipefail

BRIDGE_ROOT="$HOME/WhatsApp-MCP/whatsapp-mcp"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bridge-root) BRIDGE_ROOT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

BRIDGE_DIR="$BRIDGE_ROOT/whatsapp-bridge"
BIN="$BRIDGE_ROOT/build-tmp/whatsapp-bridge"

[[ -d "$BRIDGE_DIR" ]] || { echo "Bridge dir not found: $BRIDGE_DIR" >&2; exit 2; }

echo "Este terminal ficara aberto para mostrar o QR Code, se o WhatsApp ainda nao estiver autenticado."
echo "No celular: WhatsApp > Dispositivos conectados > Conectar um dispositivo."
echo "Depois que conectar e comecar a sincronizar, voce pode fechar com Ctrl+C."

cd "$BRIDGE_DIR"
if [[ -x "$BIN" ]]; then
  "$BIN"
else
  go run main.go
fi

