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

python_tk_ok() {
  python3 - <<'PY' >/dev/null 2>&1
import tkinter
PY
}

ensure_python_tk() {
  if python_tk_ok; then
    echo "[OK] python3 tkinter"
    return 0
  fi

  echo "[FALTA] python3 tkinter"
  if [[ "$INSTALL_WITH_BREW" != "1" ]]; then
    echo "Tkinter e necessario para abrir o painel. Instale Python com Tkinter ou rode com --install."
    return 1
  fi

  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew nao encontrado para tentar instalar tkinter." >&2
    return 1
  fi

  local py_mm
  py_mm="$(python3 - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
  local formula="python-tk@$py_mm"
  if brew info "$formula" >/dev/null 2>&1; then
    echo "Instalando $formula via Homebrew..."
    brew install "$formula"
  elif brew info python-tk >/dev/null 2>&1; then
    echo "Instalando python-tk via Homebrew..."
    brew install python-tk
  else
    echo "Nao encontrei formula Homebrew para Tkinter automaticamente."
    echo "Instale Python de https://www.python.org/downloads/macos/ ou procure a formula python-tk correspondente ao seu Python."
    return 1
  fi

  if python_tk_ok; then
    echo "[OK] python3 tkinter"
    return 0
  fi

  echo "Tkinter ainda nao carregou em python3. Reabra o terminal ou instale Python com Tkinter." >&2
  return 1
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
ensure_python_tk || true

if [[ "$INSTALL_FFMPEG" == "1" ]]; then
  install_brew_pkg ffmpeg ffmpeg -version
fi

echo
echo "Verificacao final:"
check_tool git --version || true
check_tool go version || true
check_tool python3 --version || true
ensure_python_tk || true
check_tool uv --version || true
check_tool clang --version || true
