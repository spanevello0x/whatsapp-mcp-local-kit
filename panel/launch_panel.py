from __future__ import annotations

import runpy
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
VENV_SITE = BASE_DIR / ".venv" / "Lib" / "site-packages"
PANEL = BASE_DIR / "whatsapp_mcp_panel.py"

if VENV_SITE.exists():
    sys.path.insert(0, str(VENV_SITE))

sys.argv[0] = str(PANEL)
runpy.run_path(str(PANEL), run_name="__main__")

