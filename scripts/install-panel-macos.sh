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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PANEL_SOURCE="$REPO_ROOT/panel/whatsapp_mcp_panel.py"
ICON_GENERATOR="$REPO_ROOT/scripts/generate-icons.py"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST="$LAUNCH_AGENTS/com.whatsapp-mcp.tray.plist"
DESKTOP_LAUNCHER="$HOME/Desktop/WhatsApp MCP Tray.command"

command -v uv >/dev/null 2>&1 || { echo "uv nao encontrado. Rode scripts/install-dependencies-macos.sh --install"; exit 2; }

mkdir -p "$PANEL_DIR"
cp "$PANEL_SOURCE" "$PANEL_DIR/whatsapp_mcp_panel.py"

python3 - "$PANEL_DIR/panel_config.json" "$BRIDGE_ROOT" <<'PY'
from pathlib import Path
import json, sys
path = Path(sys.argv[1])
bridge_root = sys.argv[2]
path.write_text(json.dumps({
    "bridge_root": bridge_root,
    "sync_window_minutes": 8,
    "random_sync_min_minutes": 10,
    "random_sync_max_minutes": 50,
}, indent=2), encoding="utf-8")
PY

export UV_CACHE_DIR="$PANEL_DIR/.uv-cache"
VENV="$PANEL_DIR/.venv"
PYTHON_BIN="$VENV/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  uv venv "$VENV"
  uv pip install --python "$PYTHON_BIN" pystray Pillow "qrcode[pil]" pyobjc-framework-Cocoa
fi

if [[ -f "$ICON_GENERATOR" ]]; then
  "$PYTHON_BIN" "$ICON_GENERATOR" --out-dir "$PANEL_DIR"
fi

cat > "$DESKTOP_LAUNCHER" <<EOF
#!/usr/bin/env bash
cd "$PANEL_DIR"
"$PYTHON_BIN" "$PANEL_DIR/whatsapp_mcp_panel.py"
EOF
chmod +x "$DESKTOP_LAUNCHER"

mkdir -p "$LAUNCH_AGENTS"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.whatsapp-mcp.tray</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON_BIN</string>
    <string>$PANEL_DIR/whatsapp_mcp_panel.py</string>
    <string>--minimized</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$PANEL_DIR</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardOutPath</key>
  <string>$PANEL_DIR/launchagent.out.log</string>
  <key>StandardErrorPath</key>
  <string>$PANEL_DIR/launchagent.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST" >/dev/null 2>&1 || true

echo "Painel instalado em: $PANEL_DIR"
echo "Icones criados em: $PANEL_DIR"
echo "Launcher criado: $DESKTOP_LAUNCHER"
echo "LaunchAgent criado: $PLIST"
