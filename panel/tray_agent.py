from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
VENV_SITES = []
for venv_name in (".venv-user", ".venv"):
    venv = BASE_DIR / venv_name
    VENV_SITES.append(venv / "Lib" / "site-packages")
    VENV_SITES.append(venv / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages")

for site in reversed(VENV_SITES):
    if site.exists():
        sys.path.insert(0, str(site))


def request(url: str, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def make_icon(icon_path: Path):
    from PIL import Image, ImageDraw

    if icon_path.exists():
        return Image.open(icon_path)
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6, 6, 58, 58), radius=14, fill=(11, 18, 32, 255))
    draw.ellipse((14, 13, 50, 49), fill=(25, 195, 125, 255))
    draw.ellipse((42, 42, 60, 60), fill=(217, 119, 6, 255))
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18763")
    parser.add_argument("--icon", default="")
    args = parser.parse_args()

    try:
        import pystray
    except Exception:
        return 2

    base_url = args.base_url.rstrip("/")
    icon_path = Path(args.icon) if args.icon else Path()

    def open_panel(_icon=None, _item=None) -> None:
        request(f"{base_url}/show")

    def sync_all(_icon=None, _item=None) -> None:
        request(f"{base_url}/sync-all")

    def pause_all(_icon=None, _item=None) -> None:
        request(f"{base_url}/pause-all")

    def shutdown_all(icon=None, _item=None) -> None:
        request(f"{base_url}/shutdown")
        if icon:
            icon.stop()

    def quit_agent(icon=None, _item=None) -> None:
        if icon:
            icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Abrir painel", open_panel, default=True),
        pystray.MenuItem("Sincronizar todos", sync_all),
        pystray.MenuItem("Pausar todos", pause_all),
        pystray.MenuItem("Fechar sistema", shutdown_all),
        pystray.MenuItem("Sair da bandeja", quit_agent),
    )
    icon = pystray.Icon("WhatsApp MCP Perfis", make_icon(icon_path), "WhatsApp MCP - Perfis", menu)

    def setup(_icon):
        while not request(f"{base_url}/status", timeout=0.5):
            time.sleep(1)
        _icon.visible = True

    icon.run(setup=setup)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
