#!/usr/bin/env bash
set -euo pipefail

INSTALL_WITH_BREW=0
INSTALL_FFMPEG=0

for arg in "$@"; do
  case "$arg" in
    --install|--use-brew) INSTALL_WITH_BREW=1 ;;
    --install-ffmpeg) INSTALL_FFMPEG=1 ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

check_tool() {
  local name="$1"
  shift || true
  if command -v "$name" >/dev/null 2>&1; then
    echo "[OK] $name -> $(command -v "$name")"
    "$name" "$@" || true
    return 0
  fi
  echo "[FALTA] $name"
  return 1
}

install_brew_pkg() {
  local tool="$1"
  local package="$2"
  shift 2 || true

  if command -v "$tool" >/dev/null 2>&1; then
    check_tool "$tool" "$@" >/dev/null || true
    return
  fi

  if [[ "$INSTALL_WITH_BREW" != "1" ]]; then
    echo "Para instalar automaticamente: brew install $package"
    return
  fi

  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew nao encontrado. Instale em https://brew.sh/ e rode novamente." >&2
    exit 2
  fi

  echo "Instalando $package via Homebrew..."
  brew install "$package"
}

echo "== Dependencias WhatsApp MCP Local Kit macOS =="

if ! xcode-select -p >/dev/null 2>&1; then
  echo "[FALTA] Xcode Command Line Tools"
  echo "Abrindo instalador da Apple. Depois que terminar, rode este script de novo."
  xcode-select --install || true
  exit 2
else
  echo "[OK] Xcode Command Line Tools -> $(xcode-select -p)"
fi

install_brew_pkg git git --version
install_brew_pkg go go version
install_brew_pkg python3 python --version
install_brew_pkg uv uv --version

if [[ "$INSTALL_FFMPEG" == "1" ]]; then
  install_brew_pkg ffmpeg ffmpeg -version
fi

echo
echo "Verificacao final:"
check_tool git --version || true
check_tool go version || true
check_tool python3 --version || true
check_tool uv --version || true
check_tool clang --version || true

