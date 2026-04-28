#!/usr/bin/env bash
set -euo pipefail

BRIDGE_ROOT="$HOME/WhatsApp-MCP/whatsapp-mcp"
PANEL_DIR="$HOME/Documents/WhatsApp MCP Panel"
PROFILES_DIR="$HOME/Documents/WhatsApp MCP Profiles"
PROFILES_MODE=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bridge-root) BRIDGE_ROOT="$2"; shift 2 ;;
    --panel-dir) PANEL_DIR="$2"; shift 2 ;;
    --profiles-dir) PROFILES_DIR="$2"; shift 2 ;;
    --profiles-mode) PROFILES_MODE=1; shift ;;
    --legacy-single-profile) PROFILES_MODE=0; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PANEL_SOURCE="$REPO_ROOT/panel/whatsapp_mcp_panel.py"
PROFILES_PANEL_SOURCE="$REPO_ROOT/panel/whatsapp_profiles_panel.py"
TRAY_AGENT_SOURCE="$REPO_ROOT/panel/tray_agent.py"
LAUNCHER_SOURCE="$REPO_ROOT/panel/launch_panel.py"
ICON_GENERATOR="$REPO_ROOT/scripts/generate-icons.py"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PLIST="$LAUNCH_AGENTS/com.whatsapp-mcp.tray.plist"
DESKTOP_LAUNCHER="$HOME/Desktop/WhatsApp MCP Tray.command"
DESKTOP_APP="$HOME/Desktop/WhatsApp MCP Tray.app"

command -v uv >/dev/null 2>&1 || { echo "uv nao encontrado. Rode scripts/install-dependencies-macos.sh --install"; exit 2; }

mkdir -p "$PANEL_DIR" "$PROFILES_DIR"
cp "$PANEL_SOURCE" "$PANEL_DIR/whatsapp_mcp_panel.py"
cp "$PROFILES_PANEL_SOURCE" "$PANEL_DIR/whatsapp_profiles_panel.py"
cp "$TRAY_AGENT_SOURCE" "$PANEL_DIR/tray_agent.py"
cp "$LAUNCHER_SOURCE" "$PANEL_DIR/launch_panel.py"

python3 - "$PANEL_DIR/panel_config.json" "$BRIDGE_ROOT" "$PROFILES_DIR" "$PROFILES_MODE" <<'PY'
from pathlib import Path
import json, sys

config_path = Path(sys.argv[1])
bridge_root = sys.argv[2]
profiles_dir = Path(sys.argv[3]).expanduser()
profiles_mode = sys.argv[4] == "1"

existing = {}
if config_path.exists() and config_path.read_text(encoding="utf-8-sig").strip():
    try:
        existing = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except Exception:
        existing = {}

config = {
    "bridge_root": bridge_root,
    "sync_min_minutes": 5,
    "sync_idle_minutes": 3,
    "sync_max_minutes": 25,
    "sync_extend_minutes": 10,
    "random_sync_min_minutes": 10,
    "random_sync_max_minutes": 50,
    "startup_resume_sync": True,
    "startup_resume_initial_delay_seconds": 30,
    "startup_resume_stagger_seconds": 120,
    "startup_resume_jitter_seconds": 45,
    "startup_resume_min_interval_minutes": 5,
}

if profiles_mode:
    profiles_dir.mkdir(parents=True, exist_ok=True)
    (profiles_dir / "projetos").mkdir(parents=True, exist_ok=True)
    profiles_config = profiles_dir / "profiles.json"
    base_confirmed = bool(existing.get("profiles_base_confirmed"))
    if not base_confirmed and profiles_config.exists() and profiles_config.read_text(encoding="utf-8-sig").strip():
        try:
            data = json.loads(profiles_config.read_text(encoding="utf-8-sig"))
            base_confirmed = bool(data.get("profiles") or data.get("projects"))
        except Exception:
            base_confirmed = False
    if not profiles_config.exists():
        profiles_config.write_text(json.dumps({
            "version": 1,
            "profiles_dir": str(profiles_dir),
            "next_port": 8101,
            "profiles": [],
            "projects": [],
        }, indent=2), encoding="utf-8")
    config.update({
        "profiles_mode": True,
        "profiles_dir": str(profiles_dir),
        "profiles_config": str(profiles_config),
        "profiles_base_confirmed": base_confirmed,
        "initial_sync_hours": 24,
        "control_port": 18763,
    })

config_path.write_text(json.dumps(config, indent=2, ensure_ascii=True), encoding="utf-8")
PY

export UV_CACHE_DIR="$PANEL_DIR/.uv-cache"
VENV="$PANEL_DIR/.venv"
PYTHON_BIN="$VENV/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  uv venv --python python3 "$VENV"
fi

"$PYTHON_BIN" - <<'PY' >/dev/null 2>&1 || {
import tkinter
PY
  echo "Python do painel nao consegue importar tkinter. Instale Python com Tkinter e rode o bootstrap novamente." >&2
  exit 2
}

MODULE_PROBE='import importlib.util; mods=["pystray","PIL","qrcode","AppKit"]; missing=[m for m in mods if importlib.util.find_spec(m) is None]; print(" ".join(missing))'
MISSING="$("$PYTHON_BIN" -c "$MODULE_PROBE" || true)"
if [[ -n "$MISSING" ]]; then
  echo "Instalando dependencias faltantes do painel: $MISSING"
  uv pip install --python "$PYTHON_BIN" pystray Pillow "qrcode[pil]" pyobjc-framework-Cocoa
fi

if [[ -f "$ICON_GENERATOR" ]]; then
  "$PYTHON_BIN" "$ICON_GENERATOR" --out-dir "$PANEL_DIR"
fi

APP_CONTENTS="$DESKTOP_APP/Contents"
APP_MACOS="$APP_CONTENTS/MacOS"
APP_RESOURCES="$APP_CONTENTS/Resources"
mkdir -p "$APP_MACOS" "$APP_RESOURCES"
cat > "$APP_MACOS/WhatsApp MCP Tray" <<EOF
#!/usr/bin/env bash
cd "$PANEL_DIR"
exec "$PYTHON_BIN" "$PANEL_DIR/launch_panel.py"
EOF
chmod +x "$APP_MACOS/WhatsApp MCP Tray"
if [[ -f "$PANEL_DIR/whatsapp-mcp-icon.icns" ]]; then
  cp "$PANEL_DIR/whatsapp-mcp-icon.icns" "$APP_RESOURCES/whatsapp-mcp-icon.icns"
fi
cat > "$APP_CONTENTS/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>WhatsApp MCP Tray</string>
  <key>CFBundleDisplayName</key>
  <string>WhatsApp MCP Tray</string>
  <key>CFBundleIdentifier</key>
  <string>local.whatsapp-mcp.tray</string>
  <key>CFBundleVersion</key>
  <string>1.0</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleExecutable</key>
  <string>WhatsApp MCP Tray</string>
  <key>CFBundleIconFile</key>
  <string>whatsapp-mcp-icon</string>
</dict>
</plist>
EOF
/usr/bin/touch "$DESKTOP_APP" >/dev/null 2>&1 || true

cat > "$DESKTOP_LAUNCHER" <<EOF
#!/usr/bin/env bash
cd "$PANEL_DIR"
"$PYTHON_BIN" "$PANEL_DIR/launch_panel.py"
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
    <string>$PANEL_DIR/launch_panel.py</string>
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

DOMAIN="gui/$(id -u)"
launchctl bootout "$DOMAIN" "$PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "$DOMAIN" "$PLIST" >/dev/null 2>&1 || true
launchctl enable "$DOMAIN/com.whatsapp-mcp.tray" >/dev/null 2>&1 || true

echo "Painel instalado em: $PANEL_DIR"
echo "Profiles dir: $PROFILES_DIR"
echo "Icones criados em: $PANEL_DIR"
echo "App criado: $DESKTOP_APP"
echo "Launcher criado: $DESKTOP_LAUNCHER"
echo "LaunchAgent criado: $PLIST"
