#!/usr/bin/env bash
set -euo pipefail

BRIDGE_ROOT="$HOME/WhatsApp-MCP/whatsapp-mcp"
PANEL_DIR="$HOME/Documents/WhatsApp MCP Panel"
INSTALL_MISSING=0
PATCH_LOCALHOST=0
CONFIG_CODEX=0
CONFIG_CLAUDE=0
SKIP_BUILD=0
SKIP_PANEL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bridge-root) BRIDGE_ROOT="$2"; shift 2 ;;
    --panel-dir) PANEL_DIR="$2"; shift 2 ;;
    --install-missing-dependencies) INSTALL_MISSING=1; shift ;;
    --patch-localhost) PATCH_LOCALHOST=1; shift ;;
    --configure-codex-mcp) CONFIG_CODEX=1; shift ;;
    --configure-claude-mcp) CONFIG_CLAUDE=1; shift ;;
    --configure-all-mcp) CONFIG_CODEX=1; CONFIG_CLAUDE=1; shift ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    --skip-panel) SKIP_PANEL=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENDORED_BRIDGE="$REPO_ROOT/vendor/lharries-whatsapp-mcp"

echo "== WhatsApp MCP Local Kit bootstrap macOS =="
echo "BridgeRoot: $BRIDGE_ROOT"
echo "PanelDir:   $PANEL_DIR"

if [[ "$INSTALL_MISSING" == "1" ]]; then
  "$SCRIPT_DIR/install-dependencies-macos.sh" --install
fi

required=(git go python3 uv)
missing=0
for tool in "${required[@]}"; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "[FALTA] $tool"
    missing=1
  else
    echo "[OK] $tool -> $(command -v "$tool")"
  fi
done

if ! xcode-select -p >/dev/null 2>&1; then
  echo "[FALTA] Xcode Command Line Tools"
  missing=1
fi

if [[ "$missing" == "1" ]]; then
  echo
  echo "Instale as dependencias faltantes ou rode:"
  echo "./scripts/bootstrap-macos.sh --install-missing-dependencies --patch-localhost"
  exit 2
fi

if [[ ! -d "$BRIDGE_ROOT" ]]; then
  [[ -d "$VENDORED_BRIDGE" ]] || { echo "Bridge vendorizada nao encontrada: $VENDORED_BRIDGE" >&2; exit 2; }
  mkdir -p "$BRIDGE_ROOT"
  echo
  echo "Copiando bridge incluida neste repositorio..."
  cp -R "$VENDORED_BRIDGE/whatsapp-bridge" "$BRIDGE_ROOT/"
  cp -R "$VENDORED_BRIDGE/whatsapp-mcp-server" "$BRIDGE_ROOT/"
  cp "$VENDORED_BRIDGE/LICENSE" "$BRIDGE_ROOT/LICENSE.upstream-lharries-whatsapp-mcp"
  cp "$VENDORED_BRIDGE/README-lharries-whatsapp-mcp.md" "$BRIDGE_ROOT/README.upstream-lharries-whatsapp-mcp.md"
else
  echo
  echo "Bridge ja existe. Nao vou substituir: $BRIDGE_ROOT"
fi

if [[ "$SKIP_BUILD" != "1" ]]; then
  build_args=(--bridge-root "$BRIDGE_ROOT")
  [[ "$PATCH_LOCALHOST" == "1" ]] && build_args+=(--patch-localhost)
  "$SCRIPT_DIR/build-bridge-macos.sh" "${build_args[@]}"
fi

if [[ "$SKIP_PANEL" != "1" ]]; then
  "$SCRIPT_DIR/install-panel-macos.sh" --bridge-root "$BRIDGE_ROOT" --panel-dir "$PANEL_DIR"
fi

if [[ "$CONFIG_CODEX" == "1" || "$CONFIG_CLAUDE" == "1" ]]; then
  mcp_args=(--bridge-root "$BRIDGE_ROOT")
  [[ "$CONFIG_CODEX" == "1" ]] && mcp_args+=(--codex)
  [[ "$CONFIG_CLAUDE" == "1" ]] && mcp_args+=(--claude)
  "$SCRIPT_DIR/configure-mcp-macos.sh" "${mcp_args[@]}"
fi

SESSION_DB="$BRIDGE_ROOT/whatsapp-bridge/store/whatsapp.db"
echo
echo "== Proximos passos =="
if [[ ! -f "$SESSION_DB" ]]; then
  echo "Sessao do WhatsApp ainda nao encontrada."
  echo "Rode para escanear QR:"
  echo "./scripts/first-login-macos.sh"
else
  echo "Sessao local encontrada: $SESSION_DB"
fi
echo "Abra o launcher no Desktop ou reinicie a sessao para o LaunchAgent carregar."
echo "Para validar: ./scripts/verify-local-macos.sh"

