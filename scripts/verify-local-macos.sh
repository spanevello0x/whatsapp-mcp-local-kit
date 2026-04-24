#!/usr/bin/env bash
set -euo pipefail

BRIDGE_ROOT="$HOME/WhatsApp-MCP/whatsapp-mcp"
PANEL_DIR="$HOME/Documents/WhatsApp MCP Panel"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bridge-root) BRIDGE_ROOT="$2"; shift 2 ;;
    --panel-dir) PANEL_DIR="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

echo "== WhatsApp MCP Local Verify macOS =="
echo "BridgeRoot: $BRIDGE_ROOT"
echo "PanelDir:   $PANEL_DIR"

paths=(
  "$BRIDGE_ROOT"
  "$BRIDGE_ROOT/whatsapp-bridge"
  "$BRIDGE_ROOT/whatsapp-mcp-server"
  "$BRIDGE_ROOT/whatsapp-bridge/store/messages.db"
  "$BRIDGE_ROOT/whatsapp-bridge/store/whatsapp.db"
  "$BRIDGE_ROOT/build-tmp/whatsapp-bridge"
  "$PANEL_DIR"
  "$PANEL_DIR/whatsapp_mcp_panel.py"
  "$PANEL_DIR/whatsapp-mcp-icon.png"
  "$PANEL_DIR/.venv/bin/python"
  "$HOME/Desktop/WhatsApp MCP Tray.command"
  "$HOME/Library/LaunchAgents/com.whatsapp-mcp.tray.plist"
)

for p in "${paths[@]}"; do
  if [[ -e "$p" ]]; then
    printf "%-90s true\n" "$p"
  else
    printf "%-90s false\n" "$p"
  fi
done

echo
echo "-- Runtimes --"
for cmd in "uv --version" "go version" "python3 --version" "git --version" "clang --version"; do
  echo
  echo "> $cmd"
  bash -lc "$cmd" || true
done

echo
echo "-- Porta local 8080 --"
if nc -z 127.0.0.1 8080 >/dev/null 2>&1; then
  echo "127.0.0.1:8080 aberta"
else
  echo "127.0.0.1:8080 fechada"
fi

DB="$BRIDGE_ROOT/whatsapp-bridge/store/messages.db"
if [[ -f "$DB" ]]; then
  echo
  echo "-- SQLite stats --"
  python3 - "$DB" <<'PY'
import sqlite3, sys
p = sys.argv[1]
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=1)
cur = conn.cursor()
print("messages", cur.execute("select count(*) from messages").fetchone()[0])
print("chats", cur.execute("select count(*) from chats").fetchone()[0])
print("range", cur.execute("select min(timestamp), max(timestamp) from messages").fetchone())
PY
fi

echo
echo "== Done =="
