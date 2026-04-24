from __future__ import annotations

import argparse
import json
import os
import random
import re
import signal
import socket
import sqlite3
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import messagebox as mb
from tkinter import ttk
import tkinter as tk

CONFIG_PATH = Path(__file__).with_name("panel_config.json")
DEFAULT_BRIDGE_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "CLAUDE COWORK" / "Whatsapp" / "whatsapp-mcp"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


CONFIG = load_config()
if os.name == "nt":
    default_bridge_root = DEFAULT_BRIDGE_ROOT
    bridge_binary = "whatsapp-bridge.exe"
else:
    default_bridge_root = Path.home() / "WhatsApp-MCP" / "whatsapp-mcp"
    bridge_binary = "whatsapp-bridge"

BASE_DIR = Path(CONFIG.get("bridge_root", str(default_bridge_root)))
WORK_DIR = BASE_DIR / "whatsapp-bridge"
EXE_PATH = BASE_DIR / "build-tmp" / bridge_binary
EXE_FALLBACK_PATH = WORK_DIR / bridge_binary
LOG_PATH = BASE_DIR / "bridge.log"
MESSAGES_DB = WORK_DIR / "store" / "messages.db"
PAUSED_FLAG = BASE_DIR / ".bridge-paused"
LAST_SYNC_PATH = BASE_DIR / ".bridge-last-sync"
PID_PATH = BASE_DIR / ".bridge.pid"

SYNC_WINDOW_SECONDS = int(CONFIG.get("sync_window_minutes", 8)) * 60
RANDOM_SYNC_MIN_SECONDS = int(CONFIG.get("random_sync_min_minutes", 10)) * 60
RANDOM_SYNC_MAX_SECONDS = int(CONFIG.get("random_sync_max_minutes", 50)) * 60
POLL_MS = 4000
ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

BG = "#111827"
PANEL = "#172033"
TEXT = "#edf2f7"
MUTED = "#a7b0c0"
GREEN = "#16a34a"
RED = "#dc2626"
YELLOW = "#d97706"
BLUE = "#2563eb"

STATUS_COLORS = {
    "running": (22, 163, 74, 255),
    "waiting": (217, 119, 6, 255),
    "stopped": (107, 114, 128, 255),
}


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def bridge_running() -> bool:
    if os.name != "nt" and PID_PATH.exists():
        try:
            pid = int(PID_PATH.read_text(encoding="utf-8").strip())
            if pid_alive(pid):
                return True
        except (OSError, ValueError):
            pass
        PID_PATH.unlink(missing_ok=True)

    if os.name != "nt":
        return bridge_port_open()

    result = subprocess.run(
        ["tasklist", "/fi", "imagename eq whatsapp-bridge.exe", "/fo", "csv", "/nh"],
        capture_output=True,
        text=True,
        timeout=4,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return "whatsapp-bridge.exe" in result.stdout.lower()


def bridge_port_open() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 8080), timeout=0.7):
            return True
    except OSError:
        return False


def start_bridge() -> None:
    if bridge_running():
        return
    exe = EXE_PATH if EXE_PATH.exists() else EXE_FALLBACK_PATH
    if not exe.exists():
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as log:
            log.write(f"\n[{datetime.now().isoformat()}] Executavel da bridge nao encontrado: {EXE_PATH}\n")
            log.write("Compile com scripts/build-bridge.ps1 antes de sincronizar.\n")
        return
    PAUSED_FLAG.unlink(missing_ok=True)
    log = open(LOG_PATH, "a", encoding="utf-8", errors="replace")
    popen_kwargs = {
        "cwd": str(WORK_DIR),
        "stdout": log,
        "stderr": subprocess.STDOUT,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    else:
        popen_kwargs["start_new_session"] = True

    proc = subprocess.Popen([str(exe)], **popen_kwargs)
    if os.name != "nt":
        PID_PATH.write_text(str(proc.pid), encoding="utf-8")


def stop_bridge(paused: bool = True) -> None:
    if paused:
        PAUSED_FLAG.write_text(datetime.now().isoformat(), encoding="utf-8")
    else:
        PAUSED_FLAG.unlink(missing_ok=True)
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/f", "/im", "whatsapp-bridge.exe"],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return

    if PID_PATH.exists():
        try:
            pid = int(PID_PATH.read_text(encoding="utf-8").strip())
            os.kill(pid, signal.SIGTERM)
            for _ in range(20):
                if not pid_alive(pid):
                    break
                time.sleep(0.1)
            if pid_alive(pid):
                os.kill(pid, signal.SIGKILL)
        except (OSError, ValueError, ProcessLookupError):
            pass
        PID_PATH.unlink(missing_ok=True)


def db_stats() -> dict:
    if not MESSAGES_DB.exists():
        return {"error": "messages.db nao encontrado"}
    with sqlite3.connect(f"file:{MESSAGES_DB}?mode=ro", uri=True, timeout=1.0) as conn:
        cur = conn.cursor()
        return {
            "messages": cur.execute("select count(*) from messages").fetchone()[0],
            "chats": cur.execute("select count(*) from chats").fetchone()[0],
            "last": cur.execute("select max(timestamp) from messages").fetchone()[0],
        }


def read_log(lines: int = 30) -> list[str]:
    if not LOG_PATH.exists():
        return ["Log ainda nao encontrado."]
    raw = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    return [strip_ansi(line) for line in raw if line.strip()][-lines:]


def status_from_state(running: bool, paused: bool) -> tuple[str, str]:
    if running:
        return "running", "Rodando"
    if paused:
        return "stopped", "Stopado"
    return "waiting", "Aguardando proximo sync"


def make_tray_icon(status: str, size: int = 64):
    from PIL import Image, ImageDraw

    accent = STATUS_COLORS.get(status, STATUS_COLORS["waiting"])
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    scale = size / 64

    def xy(x1, y1, x2, y2):
        return tuple(int(v * scale) for v in (x1, y1, x2, y2))

    draw.rounded_rectangle(xy(5, 5, 59, 59), radius=int(15 * scale), fill=(11, 18, 32, 255))
    draw.ellipse(xy(11, 10, 53, 52), fill=(16, 27, 45, 255), outline=(25, 195, 125, 255), width=max(1, int(3 * scale)))
    draw.rounded_rectangle(xy(17, 16, 45, 38), radius=int(9 * scale), fill=(25, 195, 125, 255))
    draw.polygon([(int(23 * scale), int(36 * scale)), (int(18 * scale), int(48 * scale)), (int(31 * scale), int(39 * scale))], fill=(25, 195, 125, 255))
    draw.rounded_rectangle(xy(22, 23, 40, 28), radius=int(3 * scale), fill=(239, 255, 247, 255))
    draw.ellipse(xy(38, 38, 60, 60), fill=accent, outline=(220, 234, 254, 255), width=max(1, int(3 * scale)))
    draw.ellipse(xy(45, 45, 53, 53), fill=(255, 255, 255, 255))
    return img


class App:
    def __init__(self, minimized: bool = False) -> None:
        self.root = tk.Tk()
        self.root.title("WhatsApp MCP Tray")
        self.root.geometry("740x560")
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.sync_end_at: float | None = None
        self.next_sync_at: float | None = None
        self.tray_icon = None
        self.tray_status_key = ""
        self.tray_status_label = "Aguardando proximo sync"
        self._ui()
        self._tray()
        if minimized:
            self.root.withdraw()
        if not PAUSED_FLAG.exists():
            self.start_sync(False)
        self.root.after(POLL_MS, self.tick)

    def _ui(self) -> None:
        top = tk.Frame(self.root, bg=PANEL, padx=16, pady=12)
        top.pack(fill=tk.X)
        tk.Label(top, text="WhatsApp MCP Tray", bg=PANEL, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        self.status = tk.Label(top, text="Aguardando", bg=PANEL, fg=YELLOW, font=("Segoe UI", 12, "bold"))
        self.status.pack(side=tk.RIGHT)
        body = tk.Frame(self.root, bg=BG, padx=16, pady=12)
        body.pack(fill=tk.BOTH, expand=True)
        controls = tk.Frame(body, bg=BG)
        controls.pack(fill=tk.X)
        tk.Button(controls, text="Sincronizar agora", bg=BLUE, fg=TEXT, command=lambda: self.start_sync(True)).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Pausar", bg=RED, fg=TEXT, command=self.pause).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Retomar random", bg=GREEN, fg=TEXT, command=self.resume).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Ocultar", command=self.hide).pack(side=tk.RIGHT, padx=4)
        self.info = tk.Label(body, text="-", bg=BG, fg=TEXT, justify=tk.LEFT, anchor="w")
        self.info.pack(fill=tk.X, pady=12)
        self.log = tk.Text(body, bg="#0b1220", fg=TEXT, relief=tk.FLAT, font=("Consolas", 9))
        scroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.pack(fill=tk.BOTH, expand=True)

    def _tray(self) -> None:
        threading.Thread(target=self._tray_worker, daemon=True).start()

    def _tray_worker(self) -> None:
        try:
            import pystray
            menu = pystray.Menu(
                pystray.MenuItem(lambda _item: f"Status: {self.tray_status_label}", None, enabled=False),
                pystray.MenuItem("Abrir painel", lambda _i, _it: self.root.after(0, self.show), default=True),
                pystray.MenuItem("Sincronizar agora", lambda _i, _it: self.root.after(0, lambda: self.start_sync(True))),
                pystray.MenuItem("Pausar", lambda _i, _it: self.root.after(0, self.pause)),
                pystray.MenuItem("Sair", lambda _i, _it: self.root.after(0, self.quit)),
            )
            self.tray_icon = pystray.Icon("WhatsApp MCP", make_tray_icon("waiting"), "WhatsApp MCP - Aguardando proximo sync", menu)
            self.tray_icon.run()
        except Exception:
            pass

    def update_tray_status(self, key: str, label: str) -> None:
        self.tray_status_label = label
        if not self.tray_icon or key == self.tray_status_key:
            return
        self.tray_status_key = key
        try:
            self.tray_icon.icon = make_tray_icon(key)
            self.tray_icon.title = f"WhatsApp MCP - {label}"
            self.tray_icon.update_menu()
        except Exception:
            pass

    def fmt(self, ts: float | None) -> str:
        return "-" if not ts else datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M:%S")

    def start_sync(self, manual: bool) -> None:
        PAUSED_FLAG.unlink(missing_ok=True)
        self.sync_end_at = time.time() + SYNC_WINDOW_SECONDS
        self.next_sync_at = None
        threading.Thread(target=start_bridge, daemon=True).start()

    def schedule_next(self) -> None:
        self.next_sync_at = time.time() + random.randint(RANDOM_SYNC_MIN_SECONDS, RANDOM_SYNC_MAX_SECONDS)

    def pause(self) -> None:
        if mb.askyesno("Pausar", "Fechar bridge e pausar sincronizacao random?"):
            threading.Thread(target=stop_bridge, daemon=True).start()

    def resume(self) -> None:
        PAUSED_FLAG.unlink(missing_ok=True)
        self.schedule_next()

    def tick(self) -> None:
        if not PAUSED_FLAG.exists():
            now = time.time()
            if bridge_running() and self.sync_end_at and now >= self.sync_end_at:
                LAST_SYNC_PATH.write_text(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), encoding="utf-8")
                threading.Thread(target=lambda: stop_bridge(False), daemon=True).start()
                self.sync_end_at = None
                self.schedule_next()
            elif not bridge_running():
                if self.next_sync_at is None:
                    self.schedule_next()
                elif now >= self.next_sync_at:
                    self.start_sync(False)
        self.refresh()
        self.root.after(POLL_MS, self.tick)

    def refresh(self) -> None:
        running = bridge_running()
        port = bridge_port_open()
        status_key, status_label = status_from_state(running, PAUSED_FLAG.exists())
        self.update_tray_status(status_key, status_label)
        self.status.config(text=status_label, fg=GREEN if running else (RED if status_key == "stopped" else YELLOW))
        try:
            last_sync = LAST_SYNC_PATH.read_text(encoding="utf-8").strip()
        except OSError:
            last_sync = "Ainda nao registrada"
        try:
            stats = db_stats()
            db_line = f"{stats.get('messages', 0):,} mensagens em {stats.get('chats', 0):,} chats; ultima msg {stats.get('last', '-')}".replace(",", ".")
        except Exception as exc:
            db_line = f"Erro DB: {exc}"
        self.info.config(text=(
            f"Bridge: {'rodando' if running else 'fechado'} | porta 8080: {'aberta' if port else 'fechada'}\n"
            f"Sync atual ate: {self.fmt(self.sync_end_at)}\n"
            f"Ultima sync: {last_sync}\n"
            f"Proxima sync: {'em andamento' if running else self.fmt(self.next_sync_at)}\n"
            f"Base: {db_line}"
        ))
        self.log.delete("1.0", tk.END)
        self.log.insert(tk.END, "\n".join(read_log()))

    def hide(self) -> None:
        self.root.withdraw()

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()

    def quit(self) -> None:
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimized", action="store_true")
    args = parser.parse_args()
    App(minimized=args.minimized).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
