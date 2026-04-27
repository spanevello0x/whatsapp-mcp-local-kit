#!/usr/bin/env bash
set -euo pipefail

PROFILES_DIR="$HOME/Documents/WhatsApp MCP Profiles"
CONFIG_CODEX=0
CONFIG_CLAUDE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profiles-dir) PROFILES_DIR="$2"; shift 2 ;;
    --codex) CONFIG_CODEX=1; shift ;;
    --claude) CONFIG_CLAUDE=1; shift ;;
    --all) CONFIG_CODEX=1; CONFIG_CLAUDE=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ "$CONFIG_CODEX" != "1" && "$CONFIG_CLAUDE" != "1" ]]; then
  echo "Use --codex, --claude ou --all"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR="$REPO_ROOT/profiles-mcp-server"
PROFILES_CONFIG="$PROFILES_DIR/profiles.json"
UV_CACHE_DIR_PATH="$SERVER_DIR/.uv-cache"

UV="$(command -v uv || true)"
[[ -n "$UV" ]] || { echo "uv nao encontrado. Rode scripts/install-dependencies-macos.sh --install"; exit 2; }
[[ -d "$SERVER_DIR" ]] || { echo "Servidor MCP de perfis nao encontrado: $SERVER_DIR" >&2; exit 2; }

mkdir -p "$PROFILES_DIR" "$UV_CACHE_DIR_PATH"
if [[ ! -f "$PROFILES_CONFIG" ]]; then
  python3 - "$PROFILES_CONFIG" "$PROFILES_DIR" <<'PY'
from pathlib import Path
import json, sys
path = Path(sys.argv[1])
profiles_dir = sys.argv[2]
path.write_text(json.dumps({
    "version": 1,
    "profiles_dir": profiles_dir,
    "next_port": 8101,
    "profiles": [],
    "projects": [],
}, indent=2), encoding="utf-8")
PY
fi

if [[ "$CONFIG_CODEX" == "1" ]]; then
  if command -v codex >/dev/null 2>&1; then
    codex mcp add whatsapp-profiles \
      --env "WHATSAPP_MCP_PROFILES_CONFIG=$PROFILES_CONFIG" \
      --env "UV_CACHE_DIR=$UV_CACHE_DIR_PATH" \
      -- "$UV" --directory "$SERVER_DIR" run main.py || true
    codex mcp list || true
  else
    echo "Codex CLI nao encontrado. Configure manualmente:"
    echo "codex mcp add whatsapp-profiles --env WHATSAPP_MCP_PROFILES_CONFIG=\"$PROFILES_CONFIG\" --env UV_CACHE_DIR=\"$UV_CACHE_DIR_PATH\" -- \"$UV\" --directory \"$SERVER_DIR\" run main.py"
  fi
fi

if [[ "$CONFIG_CLAUDE" == "1" ]]; then
  CLAUDE_DIR="$HOME/Library/Application Support/Claude"
  CONFIG_PATH="$CLAUDE_DIR/claude_desktop_config.json"
  mkdir -p "$CLAUDE_DIR"

  python3 - "$CONFIG_PATH" "$UV" "$SERVER_DIR" "$PROFILES_CONFIG" "$UV_CACHE_DIR_PATH" <<'PY'
from pathlib import Path
from datetime import datetime
import json, shutil, sys

config_path = Path(sys.argv[1])
uv = sys.argv[2]
server_dir = sys.argv[3]
profiles_config = sys.argv[4]
uv_cache = sys.argv[5]

if config_path.exists() and config_path.read_text().strip():
    backup = config_path.with_suffix(config_path.suffix + ".bak-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(config_path, backup)
    data = json.loads(config_path.read_text())
    print(f"Backup Claude config: {backup}")
else:
    data = {}

data.setdefault("mcpServers", {})
data["mcpServers"]["whatsapp-profiles"] = {
    "command": uv,
    "args": ["--directory", server_dir, "run", "main.py"],
    "env": {
        "WHATSAPP_MCP_PROFILES_CONFIG": profiles_config,
        "UV_CACHE_DIR": uv_cache,
    },
}
config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"Claude Desktop config atualizado: {config_path}")
PY

  echo "Feche o Claude Desktop completamente e abra de novo."
fi

echo "Profiles config: $PROFILES_CONFIG"
