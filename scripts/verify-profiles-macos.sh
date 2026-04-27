#!/usr/bin/env bash
set -euo pipefail

PROFILES_DIR="$HOME/Documents/WhatsApp MCP Profiles"
PANEL_DIR="$HOME/Documents/WhatsApp MCP Panel"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profiles-dir) PROFILES_DIR="$2"; shift 2 ;;
    --panel-dir) PANEL_DIR="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROFILES_CONFIG="$PROFILES_DIR/profiles.json"
BRIDGE_BINARY="$PROFILES_DIR/bin/whatsapp-bridge"
PLIST="$HOME/Library/LaunchAgents/com.whatsapp-mcp.tray.plist"
DESKTOP_LAUNCHER="$HOME/Desktop/WhatsApp MCP Tray.command"
DESKTOP_APP="$HOME/Desktop/WhatsApp MCP Tray.app"

echo "== WhatsApp MCP Profiles Verify macOS =="
echo "ProfilesDir: $PROFILES_DIR"
echo "PanelDir:    $PANEL_DIR"

show_path() {
  local p="$1"
  if [[ -e "$p" ]]; then
    printf "%-100s true\n" "$p"
  else
    printf "%-100s false\n" "$p"
  fi
}

echo
echo "-- Arquivos principais --"
for p in \
  "$PROFILES_DIR" \
  "$PROFILES_CONFIG" \
  "$BRIDGE_BINARY" \
  "$PANEL_DIR" \
  "$PANEL_DIR/launch_panel.py" \
  "$PANEL_DIR/whatsapp_profiles_panel.py" \
  "$PANEL_DIR/.venv/bin/python" \
  "$PANEL_DIR/whatsapp-mcp-icon.png" \
  "$DESKTOP_APP" \
  "$DESKTOP_APP/Contents/MacOS/WhatsApp MCP Tray" \
  "$DESKTOP_LAUNCHER" \
  "$PLIST" \
  "$REPO_ROOT/profiles-mcp-server/main.py" \
  "$REPO_ROOT/profiles-mcp-server/pyproject.toml"; do
  show_path "$p"
done

echo
echo "-- Runtimes --"
for cmd in "uv --version" "go version" "python3 --version" "git --version" "clang --version"; do
  echo
  echo "> $cmd"
  bash -lc "$cmd" || true
done

echo
echo "-- Painel config --"
if [[ -f "$PANEL_DIR/panel_config.json" ]]; then
  python3 - "$PANEL_DIR/panel_config.json" <<'PY'
from pathlib import Path
import json, sys
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
for key in ("profiles_mode", "profiles_dir", "profiles_config", "profiles_base_confirmed", "initial_sync_hours"):
    print(f"{key}: {data.get(key)}")
PY
else
  echo "panel_config.json nao encontrado"
fi

echo
echo "-- Perfis --"
if [[ ! -f "$PROFILES_CONFIG" ]]; then
  echo "Nenhum profiles.json encontrado ainda."
else
  python3 - "$PROFILES_CONFIG" <<'PY'
from pathlib import Path
import json, os, socket, sqlite3, sys

config_path = Path(sys.argv[1])
config = json.loads(config_path.read_text(encoding="utf-8-sig"))
base = Path(config.get("profiles_dir") or config_path.parent)
projects = {p.get("slug"): p for p in config.get("projects", [])}

def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=0.4):
            return True
    except Exception:
        return False

def pid_alive(pid_path):
    try:
        pid = int(Path(pid_path).read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return True
    except Exception:
        return False

profiles = config.get("profiles", [])
if not profiles:
    print("Nenhum perfil cadastrado ainda. Isso e normal antes do primeiro uso da UI.")
for profile in sorted(profiles, key=lambda item: int(item.get("port") or 0)):
    project = projects.get(profile.get("project_slug"), {})
    project_folder = profile.get("project_folder") or project.get("folder_name") or profile.get("project") or "Sem projeto"
    profile_dir = Path(profile.get("profile_dir") or (base / "projetos" / project_folder / profile["slug"]))
    store = profile_dir / "whatsapp-bridge" / "store"
    db = store / "messages.db"
    session = store / "whatsapp.db"
    pid = profile_dir / ".bridge.pid"
    messages = chats = 0
    last = "-"
    if db.exists():
        try:
            with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=1) as conn:
                messages = conn.execute("select count(*) from messages").fetchone()[0]
                chats = conn.execute("select count(*) from chats").fetchone()[0]
                last = conn.execute("select max(timestamp) from messages").fetchone()[0] or "-"
        except Exception as exc:
            last = f"erro sqlite: {exc}"
    print(f"{profile.get('slug')} | {profile.get('name')} | port={profile.get('port')} | port_open={port_open(profile.get('port'))} | pid_alive={pid_alive(pid)} | session={session.exists()} | db={db.exists()} | messages={messages} | chats={chats} | last={last}")
PY
fi

echo
echo "-- MCP local --"
SERVER_DIR="$REPO_ROOT/profiles-mcp-server"
if command -v uv >/dev/null 2>&1; then
  UV_CACHE_DIR="$SERVER_DIR/.uv-cache" WHATSAPP_MCP_PROFILES_CONFIG="$PROFILES_CONFIG" \
    uv --directory "$SERVER_DIR" run python -c "import main; print('Perfis carregados pelo MCP:', len(main.list_profiles()))" || true
else
  echo "uv nao encontrado para validar MCP."
fi

echo
echo "== Done =="
