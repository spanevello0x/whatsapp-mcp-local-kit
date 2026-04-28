from __future__ import annotations

import runpy
import sys
import json
import os
import time
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
VENV_SITES = []
for venv_name in (".venv-user", ".venv"):
    venv = BASE_DIR / venv_name
    VENV_SITES.append(venv / "Lib" / "site-packages")
    VENV_SITES.append(venv / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages")
CONFIG = BASE_DIR / "panel_config.json"
DEFAULT_PANEL = BASE_DIR / "whatsapp_mcp_panel.py"
PROFILES_PANEL = BASE_DIR / "whatsapp_profiles_panel.py"
LOG = BASE_DIR / "panel-launch.log"
LOCK = BASE_DIR / "panel-launch.lock"
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


def acquire_single_instance_lock():
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK.open("w", encoding="utf-8")
    if sys.platform == "win32":
        import msvcrt

        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            handle.write(str(os.getpid()))
            handle.flush()
            return handle
        except OSError:
            handle.close()
            return None
    import fcntl

    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        handle.write(str(Path.cwd()))
        handle.flush()
        return handle
    except OSError:
        handle.close()
        return None


def focus_existing_or_exit(config: dict) -> None:
    for _ in range(20):
        if show_existing_panel(config):
            return
        time.sleep(0.1)

for site in reversed(VENV_SITES):
    if site.exists():
        sys.path.insert(0, str(site))

try:
    try:
        LOG.unlink(missing_ok=True)
    except OSError:
        pass
    CONFIG_DATA = load_config()
    INSTANCE_LOCK = acquire_single_instance_lock()
    if INSTANCE_LOCK is None:
        focus_existing_or_exit(CONFIG_DATA)
        raise SystemExit(0)
    if show_existing_panel(CONFIG_DATA):
        raise SystemExit(0)
    PANEL = get_panel_path()
    sys.argv[0] = str(PANEL)
    runpy.run_path(str(PANEL), run_name="__main__")
except Exception as exc:
    LOG.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
    raise
