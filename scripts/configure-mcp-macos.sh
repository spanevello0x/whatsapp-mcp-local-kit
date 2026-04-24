#!/usr/bin/env bash
set -euo pipefail

BRIDGE_ROOT="$HOME/WhatsApp-MCP/whatsapp-mcp"
CONFIG_CODEX=0
CONFIG_CLAUDE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bridge-root) BRIDGE_ROOT="$2"; shift 2 ;;
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

UV="$(command -v uv || true)"
[[ -n "$UV" ]] || { echo "uv nao encontrado. Rode scripts/install-dependencies-macos.sh --install"; exit 2; }

SERVER_DIR="$BRIDGE_ROOT/whatsapp-mcp-server"
[[ -d "$SERVER_DIR" ]] || { echo "Servidor MCP nao encontrado: $SERVER_DIR" >&2; exit 2; }

if [[ "$CONFIG_CODEX" == "1" ]]; then
  if command -v codex >/dev/null 2>&1; then
    codex mcp add whatsapp -- "$UV" --directory "$SERVER_DIR" run main.py || true
    codex mcp list || true
  else
    echo "Codex CLI nao encontrado. Configure manualmente:"
    echo "codex mcp add whatsapp -- \"$UV\" --directory \"$SERVER_DIR\" run main.py"
  fi
fi

if [[ "$CONFIG_CLAUDE" == "1" ]]; then
  CLAUDE_DIR="$HOME/Library/Application Support/Claude"
  CONFIG_PATH="$CLAUDE_DIR/claude_desktop_config.json"
  mkdir -p "$CLAUDE_DIR"

  python3 - "$CONFIG_PATH" "$UV" "$SERVER_DIR" <<'PY'
from pathlib import Path
import json, shutil, sys

config_path = Path(sys.argv[1])
uv = sys.argv[2]
server_dir = sys.argv[3]

if config_path.exists() and config_path.read_text().strip():
    from datetime import datetime
    backup = config_path.with_suffix(config_path.suffix + ".bak-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(config_path, backup)
    data = json.loads(config_path.read_text())
    print(f"Backup Claude config: {backup}")
else:
    data = {}

data.setdefault("mcpServers", {})
data["mcpServers"]["whatsapp"] = {
    "command": uv,
    "args": ["--directory", server_dir, "run", "main.py"],
}
config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"Claude Desktop config atualizado: {config_path}")
PY

  echo "Feche o Claude Desktop completamente e abra de novo."
fi
