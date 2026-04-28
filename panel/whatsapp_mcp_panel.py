from __future__ import annotations

import argparse
import ctypes
import json
import os
import random
import re
import signal
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import messagebox as mb
from tkinter import ttk
import tkinter as tk

PANEL_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PANEL_DIR / "panel_config.json"
DEFAULT_BRIDGE_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "CLAUDE COWORK" / "Whatsapp" / "whatsapp-mcp"
IS_WINDOWS = os.name == "nt"
PANEL_ICON = PANEL_DIR / ("whatsapp-mcp-icon.ico" if IS_WINDOWS else "whatsapp-mcp-icon.png")
APP_USER_MODEL_ID = "WhatsAppMCP.LocalTray"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
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

LEGACY_SYNC_WINDOW_MINUTES = int(CONFIG.get("sync_window_minutes", 8))
SYNC_MIN_SECONDS = int(CONFIG.get("sync_min_minutes", min(5, LEGACY_SYNC_WINDOW_MINUTES))) * 60
SYNC_IDLE_SECONDS = int(CONFIG.get("sync_idle_minutes", 3)) * 60
SYNC_MAX_SECONDS = int(CONFIG.get("sync_max_minutes", max(25, LEGACY_SYNC_WINDOW_MINUTES))) * 60
SYNC_EXTEND_SECONDS = int(CONFIG.get("sync_extend_minutes", 10)) * 60
SYNC_IDLE_SECONDS = max(60, SYNC_IDLE_SECONDS)
SYNC_MAX_SECONDS = max(SYNC_MAX_SECONDS, SYNC_MIN_SECONDS + SYNC_IDLE_SECONDS)
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


def set_process_app_id() -> None:
    if not IS_WINDOWS:
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


def apply_window_icon(window: tk.Misc) -> None:
    if IS_WINDOWS and PANEL_ICON.exists():
        try:
            window.iconbitmap(default=str(PANEL_ICON))
            return
        except tk.TclError:
            try:
                window.iconbitmap(str(PANEL_ICON))
                return
            except tk.TclError:
                pass
    icon_png = PANEL_DIR / "whatsapp-mcp-icon.png"
    if icon_png.exists():
        try:
            photo = tk.PhotoImage(file=str(icon_png))
            window.iconphoto(True, photo)
            setattr(window, "_whatsapp_mcp_icon", photo)
        except tk.TclError:
            pass


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


def db_snapshot() -> dict:
    snapshot = {"messages": None, "chats": None, "last": None, "mtime": None, "error": None}
    if MESSAGES_DB.exists():
        snapshot["mtime"] = MESSAGES_DB.stat().st_mtime
    try:
        snapshot.update(db_stats())
    except Exception as exc:
        snapshot["error"] = str(exc)
    return snapshot


def read_log(lines: int = 30) -> list[str]:
    if not LOG_PATH.exists():
        return ["Log ainda nao encontrado."]
    raw = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    return [strip_ansi(line) for line in raw if line.strip()][-lines:]


def status_from_state(running: bool, paused: bool) -> tuple[str, str]:
    if running:
        return "running", "Sincronizando agora"
    if paused:
        return "stopped", "Pausado / stopado"
    return "waiting", "Aguardando proximo sync"


def human_duration(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {seconds:02d}s"
    return f"{seconds}s"


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
        set_process_app_id()
        self.root = tk.Tk()
        apply_window_icon(self.root)
        self.root.title("WhatsApp MCP Tray")
        self.root.geometry("900x600")
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.sync_session: dict | None = None
        self.closing_sync = False
        self.next_sync_at: float | None = None
        self.last_action = "Painel iniciado."
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
        button_font = ("Segoe UI", 9, "bold")
        self.sync_button = tk.Button(controls, text="Sincronizar agora", bg=BLUE, fg=TEXT, font=button_font, command=lambda: self.start_sync(True))
        self.sync_button.pack(side=tk.LEFT, padx=4)
        self.pause_button = tk.Button(controls, text="Pausar", bg=RED, fg=TEXT, font=button_font, command=self.pause)
        self.pause_button.pack(side=tk.LEFT, padx=4)
        self.resume_button = tk.Button(controls, text="Retomar random", bg=GREEN, fg=TEXT, font=button_font, command=self.resume)
        self.resume_button.pack(side=tk.LEFT, padx=4)
        self.folder_button = tk.Button(controls, text="Pasta", bg="#334155", fg=TEXT, font=button_font, command=self.open_messages_folder)
        self.folder_button.pack(side=tk.LEFT, padx=4)
        self.copy_button = tk.Button(controls, text="Copiar DB", bg="#334155", fg=TEXT, font=button_font, command=self.copy_messages_path)
        self.copy_button.pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Sair", font=button_font, command=self.quit).pack(side=tk.RIGHT, padx=4)
        tk.Button(controls, text="Ocultar", font=button_font, command=self.hide).pack(side=tk.RIGHT, padx=4)
        self.info = tk.Text(body, height=12, bg=BG, fg=TEXT, relief=tk.FLAT, wrap=tk.WORD, font=("Segoe UI", 9))
        self.info.tag_configure("key", foreground=TEXT, font=("Segoe UI", 9, "bold"))
        self.info.tag_configure("good", foreground=GREEN, font=("Segoe UI", 9, "bold"))
        self.info.tag_configure("warn", foreground=YELLOW, font=("Segoe UI", 9, "bold"))
        self.info.tag_configure("bad", foreground=RED, font=("Segoe UI", 9, "bold"))
        self.info.tag_configure("muted", foreground=MUTED)
        self.info.config(state=tk.DISABLED)
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

    def remaining(self, ts: float | None) -> str:
        if not ts:
            return "-"
        return human_duration(ts - time.time())

    def _signature(self, stats: dict) -> tuple:
        return (stats.get("messages"), stats.get("last"), stats.get("mtime"))

    def _begin_sync_session(self, manual: bool) -> None:
        now = time.time()
        stats = db_snapshot()
        self.sync_session = {
            "started_at": now,
            "min_until": now + SYNC_MIN_SECONDS,
            "max_until": now + SYNC_MAX_SECONDS,
            "last_activity_at": now,
            "baseline_messages": stats.get("messages") or 0,
            "current_messages": stats.get("messages") or 0,
            "last_message": stats.get("last"),
            "last_signature": self._signature(stats),
            "manual": manual,
        }

    def _observe_sync_activity(self, stats: dict) -> None:
        if not self.sync_session:
            return
        now = time.time()
        signature = self._signature(stats)
        if signature != self.sync_session.get("last_signature"):
            self.sync_session["last_activity_at"] = now
            self.sync_session["last_signature"] = signature
        if stats.get("messages") is not None:
            self.sync_session["current_messages"] = stats.get("messages") or 0
        if stats.get("last"):
            self.sync_session["last_message"] = stats.get("last")

    def new_messages_this_sync(self) -> int:
        if not self.sync_session:
            return 0
        return max(0, int(self.sync_session.get("current_messages", 0)) - int(self.sync_session.get("baseline_messages", 0)))

    def complete_sync(self, reason: str) -> None:
        new_count = self.new_messages_this_sync()
        stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        LAST_SYNC_PATH.write_text(f"{stamp} ({reason}; {new_count} novas msgs)", encoding="utf-8")
        self.last_action = f"Sync concluida: {reason}. Porta fechando."
        self.sync_session = None
        self.closing_sync = True
        self.schedule_next()
        threading.Thread(target=lambda: stop_bridge(False), daemon=True).start()

    def status_for(self, running: bool, paused: bool) -> tuple[str, str]:
        if paused:
            return "stopped", "Pausado / stopado"
        if running:
            if self.closing_sync:
                return "running", "Fechando porta"
            if self.sync_session and time.time() >= self.sync_session.get("min_until", 0):
                return "running", "Estabilizando para fechar"
            return "running", "Sincronizando agora"
        return "waiting", "Aguardando proximo sync"

    def start_sync(self, manual: bool) -> None:
        PAUSED_FLAG.unlink(missing_ok=True)
        self.closing_sync = False
        self.next_sync_at = None
        now = time.time()
        if bridge_running():
            if not self.sync_session:
                self._begin_sync_session(manual)
            self.sync_session["max_until"] = max(self.sync_session.get("max_until", now), now) + SYNC_EXTEND_SECONDS
            self.sync_session["last_activity_at"] = now
            self.last_action = f"Sync ja estava ativa; janela estendida em {human_duration(SYNC_EXTEND_SECONDS)}."
        else:
            self._begin_sync_session(manual)
            self.last_action = "Sync manual iniciada." if manual else "Sync random iniciada."
            threading.Thread(target=start_bridge, daemon=True).start()
        self.refresh()

    def schedule_next(self) -> None:
        self.next_sync_at = time.time() + random.randint(RANDOM_SYNC_MIN_SECONDS, RANDOM_SYNC_MAX_SECONDS)

    def pause(self) -> None:
        if mb.askyesno("Pausar", "Fechar bridge e pausar sincronizacao random?"):
            self.sync_session = None
            self.closing_sync = True
            self.last_action = "Sincronizacao pausada pelo usuario."
            threading.Thread(target=stop_bridge, daemon=True).start()

    def resume(self) -> None:
        PAUSED_FLAG.unlink(missing_ok=True)
        if bridge_running():
            self._begin_sync_session(True)
            self.next_sync_at = None
            self.last_action = "Random retomado; bridge ja estava rodando."
        else:
            self.schedule_next()
            self.last_action = "Random retomado; proxima sync sorteada."
        self.refresh()

    def open_messages_folder(self) -> None:
        folder = MESSAGES_DB.parent
        try:
            if os.name == "nt":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
            self.last_action = f"Pasta da base aberta: {folder}"
        except Exception as exc:
            self.last_action = f"Erro ao abrir pasta da base: {exc}"
        self.refresh()

    def copy_messages_path(self) -> None:
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(str(MESSAGES_DB))
            self.root.update()
            self.last_action = f"Caminho copiado: {MESSAGES_DB}"
        except Exception as exc:
            self.last_action = f"Erro ao copiar caminho: {exc}"
        self.refresh()

    def tick(self) -> None:
        if not PAUSED_FLAG.exists():
            now = time.time()
            running = bridge_running()
            if running:
                if self.closing_sync:
                    pass
                elif not self.sync_session:
                    self._begin_sync_session(False)
                    self.last_action = "Bridge detectada rodando; janela de sync monitorada."
                if self.sync_session:
                    stats = db_snapshot()
                    self._observe_sync_activity(stats)
                    last_activity_at = self.sync_session.get("last_activity_at", now)
                    max_until = self.sync_session.get("max_until", now)
                    min_until = self.sync_session.get("min_until", now)
                    if now >= max_until:
                        self.complete_sync("timeout maximo")
                    elif now >= min_until and now - last_activity_at >= SYNC_IDLE_SECONDS:
                        self.complete_sync("sem atividade na base")
            else:
                self.closing_sync = False
                if self.sync_session:
                    self.sync_session = None
                    self.last_action = "Bridge fechada; aguardando proxima sync."
                if self.next_sync_at is None:
                    self.schedule_next()
                elif now >= self.next_sync_at:
                    self.start_sync(False)
        self.refresh()
        self.root.after(POLL_MS, self.tick)

    def set_info_rows(self, rows: list[tuple[str, str, str | None]]) -> None:
        self.info.config(state=tk.NORMAL)
        self.info.delete("1.0", tk.END)
        for key, value, tag in rows:
            self.info.insert(tk.END, f"{key}: ", ("key",))
            self.info.insert(tk.END, value, (tag,) if tag else ())
            self.info.insert(tk.END, "\n")
        self.info.config(state=tk.DISABLED)

    def refresh(self) -> None:
        running = bridge_running()
        port = bridge_port_open()
        paused = PAUSED_FLAG.exists()
        status_key, status_label = self.status_for(running, paused)
        tray_label = status_label
        if running and self.sync_session:
            tray_label = f"{status_label} ({self.new_messages_this_sync()} novas)"
        self.update_tray_status(status_key, tray_label)
        self.status.config(text=status_label, fg=GREEN if running else (RED if status_key == "stopped" else YELLOW))
        self.sync_button.config(text=f"Estender +{human_duration(SYNC_EXTEND_SECONDS)}" if running else "Sincronizar agora")
        self.pause_button.config(state=tk.DISABLED if paused else tk.NORMAL)
        self.resume_button.config(state=tk.NORMAL if paused else tk.DISABLED)
        try:
            last_sync = LAST_SYNC_PATH.read_text(encoding="utf-8").strip()
        except OSError:
            last_sync = "Ainda nao registrada"
        stats = db_snapshot()
        if stats.get("error"):
            db_line = f"Erro DB: {stats.get('error')}"
        else:
            db_line = f"{stats.get('messages', 0):,} mensagens em {stats.get('chats', 0):,} chats; ultima msg {stats.get('last', '-')}".replace(",", ".")
        if running:
            if self.closing_sync:
                sync_line = "fechando a bridge e liberando a porta"
                next_line = "ja sorteada para depois do fechamento"
                port_line = "aberta (fechando)"
                activity_line = "-"
                new_line = "-"
            else:
                if not self.sync_session:
                    self._begin_sync_session(False)
                now = time.time()
                self._observe_sync_activity(stats)
                idle_for = now - self.sync_session.get("last_activity_at", now)
                idle_left = max(0, SYNC_IDLE_SECONDS - idle_for)
                if now < self.sync_session.get("min_until", now):
                    sync_line = f"minimo ate {self.fmt(self.sync_session.get('min_until'))}; depois fecha se ficar {human_duration(SYNC_IDLE_SECONDS)} sem atividade"
                else:
                    sync_line = f"fecha em {human_duration(idle_left)} se nao entrar nada novo; timeout {self.fmt(self.sync_session.get('max_until'))}"
                next_line = "sera sorteada quando esta sync terminar"
                port_line = "aberta (normal durante sincronizacao)"
                activity_line = f"ha {human_duration(idle_for)}"
                new_line = f"{self.new_messages_this_sync()} novas mensagens nesta janela"
        elif paused:
            sync_line = "pausada"
            next_line = "random pausado"
            port_line = "aberta" if port else "fechada"
            activity_line = "-"
            new_line = "-"
        else:
            self.closing_sync = False
            sync_line = "nenhuma sync em andamento"
            next_line = self.fmt(self.next_sync_at)
            port_line = "aberta" if port else "fechada (ok para pesquisar a base local)"
            activity_line = "-"
            new_line = "-"
        self.set_info_rows([
            ("Estado", status_label, "good" if running else ("bad" if paused else "warn")),
            ("MCP para pesquisa", "disponivel mesmo com a porta fechada", "good"),
            ("Bridge", "rodando" if running else "fechada", "good" if running else "muted"),
            ("Porta 8080", port_line, "warn" if port else "good"),
            ("Fechamento da sync", sync_line, "warn" if running else "muted"),
            ("Novas nesta janela", new_line, "good" if running else "muted"),
            ("Ultima atividade da base", activity_line, "warn" if running else "muted"),
            ("Ultima sync concluida", last_sync, "good"),
            ("Proxima sync", next_line, "warn" if not paused else "muted"),
            ("Base local", db_line, "good" if not stats.get("error") else "bad"),
            ("Arquivo mensagens", str(MESSAGES_DB), "muted"),
            ("Ultima acao", self.last_action, "muted"),
        ])
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
