from __future__ import annotations

import runpy
import sys
import json
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
VENV_SITES = [
    BASE_DIR / ".venv-user" / "Lib" / "site-packages",
    BASE_DIR / ".venv" / "Lib" / "site-packages",
]
CONFIG = BASE_DIR / "panel_config.json"
DEFAULT_PANEL = BASE_DIR / "whatsapp_mcp_panel.py"
PROFILES_PANEL = BASE_DIR / "whatsapp_profiles_panel.py"
LOG = BASE_DIR / "panel-launch.log"
DEFAULT_CONTROL_PORT = 18763


def get_panel_path() -> Path:
    if CONFIG.exists():
        try:
            config = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
            if config.get("profiles_mode") and PROFILES_PANEL.exists():
                return PROFILES_PANEL
        except Exception:
            pass
    return DEFAULT_PANEL


def load_config() -> dict:
    if not CONFIG.exists():
        return {}
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def show_existing_panel(config: dict) -> bool:
    if not config.get("profiles_mode"):
        return False
    port = int(config.get("control_port", DEFAULT_CONTROL_PORT))
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/show", timeout=0.5) as response:
            return response.status == 200
    except Exception:
        return False

for site in reversed(VENV_SITES):
    if site.exists():
        sys.path.insert(0, str(site))

try:
    try:
        LOG.unlink(missing_ok=True)
    except OSError:
        pass
    CONFIG_DATA = load_config()
    if show_existing_panel(CONFIG_DATA):
        raise SystemExit(0)
    PANEL = get_panel_path()
    sys.argv[0] = str(PANEL)
    runpy.run_path(str(PANEL), run_name="__main__")
except Exception as exc:
    LOG.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
    raise
