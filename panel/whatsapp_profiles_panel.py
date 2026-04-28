from __future__ import annotations

import argparse
import ctypes
import faulthandler
import json
import os
import queue
import random
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox as mb
from tkinter import simpledialog
from tkinter import ttk
import tkinter as tk
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PANEL_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PANEL_DIR / "panel_config.json"
ACTION_LOG = PANEL_DIR / "panel-actions.log"
STACK_DUMP = PANEL_DIR / "panel-stack-dump.log"
DEFAULT_PROFILES_DIR = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documents" / "WhatsApp MCP Profiles"
IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"
POLL_MS = 5000
CONTROL_HOST = "127.0.0.1"
ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

BG = "#111827"
PANEL = "#172033"
PANEL_2 = "#0b1220"
TEXT = "#edf2f7"
MUTED = "#a7b0c0"
GREEN = "#16a34a"
RED = "#dc2626"
YELLOW = "#d97706"
BLUE = "#2563eb"
PURPLE = "#6d28d9"
GRAY = "#334155"
BUTTON_DISABLED_BG = "#243044"
BUTTON_DISABLED_FG = "#8b95a6"
BUTTON_HOVER_TINT = "#ffffff"

STATUS_COLORS = {
    "running": (22, 163, 74, 255),
    "waiting": (217, 119, 6, 255),
    "stopped": (107, 114, 128, 255),
}


def blend_hex(color: str, overlay: str, alpha: float) -> str:
    base = color.lstrip("#")
    top = overlay.lstrip("#")
    if len(base) != 6 or len(top) != 6:
        return color
    values = []
    for index in (0, 2, 4):
        b = int(base[index : index + 2], 16)
        t = int(top[index : index + 2], 16)
        values.append(round(b * (1 - alpha) + t * alpha))
    return "#" + "".join(f"{value:02x}" for value in values)


class ActionButton(tk.Label):
    """Theme-independent button for macOS, where native tk.Button ignores colors."""

    def __init__(self, parent: tk.Widget, text: str, color: str, command, width: int | None = None) -> None:
        self._normal_bg = color
        self._hover_bg = blend_hex(color, BUTTON_HOVER_TINT, 0.12)
        self._pressed_bg = blend_hex(color, "#000000", 0.10)
        self._command = command
        self._enabled = True
        super().__init__(
            parent,
            text=text,
            bg=self._normal_bg,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=7,
            width=width or 0,
            anchor=tk.CENTER,
            cursor="pointinghand",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=blend_hex(color, "#000000", 0.18),
            highlightcolor=blend_hex(color, "#000000", 0.18),
            takefocus=True,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Return>", self._on_key)
        self.bind("<space>", self._on_key)

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        if cnf:
            kwargs.update(cnf)
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "state" in kwargs:
            state = kwargs.pop("state")
            self._enabled = state != tk.DISABLED and str(state) != "disabled"
            kwargs["cursor"] = "pointinghand" if self._enabled else "arrow"
        if "bg" in kwargs or "background" in kwargs:
            color = kwargs.pop("bg", kwargs.pop("background", self._normal_bg))
            self._normal_bg = color
            self._hover_bg = blend_hex(color, BUTTON_HOVER_TINT, 0.12)
            self._pressed_bg = blend_hex(color, "#000000", 0.10)
            kwargs["highlightbackground"] = blend_hex(color, "#000000", 0.18)
            kwargs["highlightcolor"] = blend_hex(color, "#000000", 0.18)
        if self._enabled:
            kwargs.setdefault("bg", self._normal_bg)
            kwargs.setdefault("fg", TEXT)
        else:
            kwargs.setdefault("bg", BUTTON_DISABLED_BG)
            kwargs.setdefault("fg", BUTTON_DISABLED_FG)
        return super().configure(**kwargs)

    config = configure

    def _on_enter(self, _event=None) -> None:
        if self._enabled:
            super().configure(bg=self._hover_bg)

    def _on_leave(self, _event=None) -> None:
        super().configure(bg=self._normal_bg if self._enabled else BUTTON_DISABLED_BG)

    def _on_press(self, _event=None) -> None:
        if self._enabled:
            super().configure(bg=self._pressed_bg)

    def _on_release(self, event=None) -> None:
        if not self._enabled:
            return
        inside = event is None or (0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height())
        super().configure(bg=self._hover_bg if inside else self._normal_bg)
        if inside and self._command:
            self._command()

    def _on_key(self, _event=None) -> str:
        if self._enabled and self._command:
            self._command()
        return "break"

OLD_AUTOCREATED_PROJECT_SLUGS = {"geral", "vendedores", "pessoal", "administrativo"}
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def load_panel_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    return {}


CONFIG = load_panel_config()
CONTROL_PORT = int(CONFIG.get("control_port", 18763))
PROFILES_DIR = Path(CONFIG.get("profiles_dir", str(DEFAULT_PROFILES_DIR)))
PROFILES_CONFIG = Path(CONFIG.get("profiles_config", str(PROFILES_DIR / "profiles.json")))
STATE_PATH = PROFILES_DIR / "profiles_state.json"
BRIDGE_BINARY = PROFILES_DIR / "bin" / ("whatsapp-bridge.exe" if os.name == "nt" else "whatsapp-bridge")
STARTUP_DIR = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
STARTUP_SHORTCUT = STARTUP_DIR / "WhatsApp MCP Tray.lnk"
LEGACY_STARTUP_SHORTCUT = STARTUP_DIR / "WhatsApp MCP Painel.lnk"
WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_RUN_NAME = "WhatsApp MCP Tray"
PANEL_RUNTIME_VENV = PANEL_DIR / ".venv-user" if (PANEL_DIR / ".venv-user").exists() else PANEL_DIR / ".venv"
PANEL_VENV_PYTHONW = PANEL_RUNTIME_VENV / "Scripts" / "pythonw.exe" if IS_WINDOWS else PANEL_RUNTIME_VENV / "bin" / "python"
PANEL_LAUNCHER = PANEL_DIR / "launch_panel.py"
PANEL_ICON = PANEL_DIR / ("whatsapp-mcp-icon.ico" if IS_WINDOWS else "whatsapp-mcp-icon.png")
APP_USER_MODEL_ID = "WhatsAppMCP.LocalTray"
MAC_LAUNCH_AGENT_DIR = Path.home() / "Library" / "LaunchAgents"
MAC_LAUNCH_AGENT = MAC_LAUNCH_AGENT_DIR / "com.whatsapp-mcp.tray.plist"

INITIAL_SYNC_HOURS = int(CONFIG.get("initial_sync_hours", 24))
INITIAL_SYNC_MIN_SECONDS = int(CONFIG.get("initial_sync_min_minutes", 10)) * 60
INITIAL_SYNC_IDLE_SECONDS = int(CONFIG.get("initial_sync_idle_minutes", 3)) * 60
INITIAL_SYNC_STABLE_SECONDS = int(CONFIG.get("initial_sync_stable_minutes", 5)) * 60
INITIAL_SYNC_LIVE_LAG_SECONDS = int(CONFIG.get("initial_sync_live_lag_minutes", 45)) * 60
INITIAL_SYNC_LIVE_RATE_PER_MINUTE = float(CONFIG.get("initial_sync_live_rate_per_minute", 20))
SYNC_MIN_SECONDS = int(CONFIG.get("sync_min_minutes", 5)) * 60
SYNC_IDLE_SECONDS = int(CONFIG.get("sync_idle_minutes", 3)) * 60
SYNC_MAX_SECONDS = int(CONFIG.get("sync_max_minutes", 25)) * 60
RANDOM_SYNC_MIN_SECONDS = int(CONFIG.get("random_sync_min_minutes", 10)) * 60
RANDOM_SYNC_MAX_SECONDS = int(CONFIG.get("random_sync_max_minutes", 50)) * 60
STARTUP_RESUME_SYNC_ENABLED = str(CONFIG.get("startup_resume_sync", True)).strip().lower() not in {"0", "false", "no", "off"}
STARTUP_RESUME_INITIAL_DELAY_SECONDS = int(CONFIG.get("startup_resume_initial_delay_seconds", 30))
STARTUP_RESUME_STAGGER_SECONDS = int(CONFIG.get("startup_resume_stagger_seconds", 120))
STARTUP_RESUME_JITTER_SECONDS = int(CONFIG.get("startup_resume_jitter_seconds", 45))
STARTUP_RESUME_MIN_INTERVAL_SECONDS = int(CONFIG.get("startup_resume_min_interval_minutes", 5)) * 60
QR_AUTH_AUTO_RETURN_MS = int(CONFIG.get("qr_auth_auto_return_seconds", 3)) * 1000
STARTUP_RESUME_CLEAR_PAUSED = str(CONFIG.get("startup_resume_clear_paused", True)).strip().lower() not in {"0", "false", "no", "off"}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def now_for(dt: datetime | None = None) -> datetime:
    if dt and dt.tzinfo is not None:
        return datetime.now(dt.tzinfo)
    return datetime.now()


def seconds_since_dt(dt: datetime | None) -> float | None:
    if not dt:
        return None
    return max(0.0, (now_for(dt) - dt).total_seconds())


def message_lag_seconds(timestamp: str | None) -> float | None:
    return seconds_since_dt(parse_iso(timestamp))


def fmt_dt(value: str | None) -> str:
    dt = parse_iso(value)
    if not dt:
        return "-"
    return dt.strftime("%d/%m/%Y %H:%M:%S")


def human_duration(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    seconds = max(0, int(seconds))
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days}d {hours:02d}h"
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {sec:02d}s"
    return f"{sec}s"


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def save_panel_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=True), encoding="utf-8")


def refresh_profile_globals(base_dir: Path) -> None:
    global PROFILES_DIR, PROFILES_CONFIG, STATE_PATH, BRIDGE_BINARY
    PROFILES_DIR = Path(base_dir)
    PROFILES_CONFIG = PROFILES_DIR / "profiles.json"
    STATE_PATH = PROFILES_DIR / "profiles_state.json"
    BRIDGE_BINARY = PROFILES_DIR / "bin" / ("whatsapp-bridge.exe" if os.name == "nt" else "whatsapp-bridge")


def set_profiles_base_dir(base_dir: str | Path) -> None:
    global CONFIG
    new_dir = Path(base_dir).expanduser()
    old_config_path = PROFILES_CONFIG
    old_bin = PROFILES_DIR / "bin"
    refresh_profile_globals(new_dir)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    (PROFILES_DIR / "projetos").mkdir(parents=True, exist_ok=True)
    if old_bin.exists() and old_bin != PROFILES_DIR / "bin" and not (PROFILES_DIR / "bin").exists():
        try:
            shutil.copytree(old_bin, PROFILES_DIR / "bin")
        except OSError:
            pass
    CONFIG["profiles_dir"] = str(PROFILES_DIR)
    CONFIG["profiles_config"] = str(PROFILES_CONFIG)
    CONFIG["profiles_base_confirmed"] = True
    save_panel_config(CONFIG)
    if old_config_path != PROFILES_CONFIG:
        try:
            old_config_path.parent.mkdir(parents=True, exist_ok=True)
            old_config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "profiles_dir": str(PROFILES_DIR),
                        "profiles_config": str(PROFILES_CONFIG),
                        "redirect": True,
                    },
                    indent=2,
                    ensure_ascii=True,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass


def mark_base_confirmed_if_existing() -> bool:
    if CONFIG.get("profiles_base_confirmed"):
        return True
    if PROFILES_CONFIG.exists():
        try:
            raw = PROFILES_CONFIG.read_text(encoding="utf-8-sig")
            data = json.loads(raw) if raw.strip() else {}
            if data.get("profiles") or data.get("projects"):
                CONFIG["profiles_base_confirmed"] = True
                save_panel_config(CONFIG)
                return True
        except (OSError, json.JSONDecodeError):
            pass
    return False


def action_log(message: str) -> None:
    try:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with ACTION_LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp} {message}\n")
    except OSError:
        pass


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


def activate_macos_app() -> None:
    if not IS_MAC:
        return
    try:
        from AppKit import NSApplicationActivateIgnoringOtherApps, NSRunningApplication

        NSRunningApplication.currentApplication().activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
    except Exception:
        try:
            subprocess.Popen(
                ["osascript", "-e", 'tell application "WhatsApp MCP Tray" to activate'],
                capture_output=True,
                text=True,
            )
        except Exception:
            pass


def center_child_window(window: tk.Toplevel, parent: tk.Misc, width: int, height: int) -> None:
    try:
        parent.update_idletasks()
        window.update_idletasks()
        parent_width = max(parent.winfo_width(), parent.winfo_reqwidth(), 1)
        parent_height = max(parent.winfo_height(), parent.winfo_reqheight(), 1)
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        x = parent_x + max(0, (parent_width - width) // 2)
        y = parent_y + max(0, (parent_height - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    except tk.TclError:
        window.geometry(f"{width}x{height}")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or f"perfil-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def phone_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_phone_digits(value: str) -> str:
    digits = phone_digits(value)
    if digits.startswith("55") and len(digits) == 12 and digits[4:5] == "9":
        return digits[:4] + "9" + digits[4:]
    return digits


def format_phone_number(value: str) -> str:
    digits = normalize_phone_digits(value)
    if not digits:
        return ""
    if digits.startswith("55") and len(digits) >= 12:
        area = digits[2:4]
        local = digits[4:]
        return f"+55 ({area}) {local}"
    if len(digits) >= 10:
        area = digits[:2]
        local = digits[2:]
        return f"+55 ({area}) {local}"
    if value.strip().startswith("+"):
        return value.strip()
    return digits


def jid_to_phone(value: str) -> str:
    local = (value or "").split("@", 1)[0].strip()
    local = local.split(":", 1)[0]
    return format_phone_number(local)


def detected_number_should_replace(profile: dict, detected: str) -> bool:
    detected_digits = phone_digits(detected)
    existing_digits = phone_digits(profile.get("number") or "")
    if not detected_digits:
        return False
    if not existing_digits:
        return True
    if existing_digits == detected_digits:
        return False
    if existing_digits.startswith("55"):
        for suffix_len in range(1, 5):
            if len(existing_digits) > suffix_len and normalize_phone_digits(existing_digits[:-suffix_len]) == detected_digits:
                return True
    return False


def apply_detected_profile_number(profile: dict, detected: str) -> bool:
    if not detected_number_should_replace(profile, detected):
        return False
    profile["number"] = detected
    profile["number_digits"] = phone_digits(detected)
    profile["updated_at"] = now_iso()
    return True


def detected_phone_from_log_line(line: str) -> str:
    if line.startswith("SELF_JID:"):
        return jid_to_phone(line.split(":", 1)[1].strip())
    match = re.search(r"Successfully paired\s+([0-9:]+@s\.whatsapp\.net)", line)
    if match:
        return jid_to_phone(match.group(1))
    return ""


def should_replace_detected_number(current: str, detected: str) -> bool:
    return detected_number_should_replace({"number": current}, detected)


def profile_configured(profile: dict) -> bool:
    if profile_is_starter(profile):
        return False
    name = str(profile.get("name", "")).strip()
    project = str(profile.get("project_slug", "") or profile.get("project", "")).strip()
    return bool(name and project)


def profile_is_starter(profile: dict) -> bool:
    number = str(profile.get("number", "")).strip().upper()
    name = str(profile.get("name", "")).strip().lower()
    project = str(profile.get("project_slug", "") or profile.get("project", "")).strip()
    return number in ("", "PREENCHER_NUMERO") and name in ("", "perfil 1", "primeiro numero") and not project


def normalize_project_name(name: str) -> str:
    return " ".join((name or "").strip().split())


def normalize_profile_name(name: str) -> str:
    return " ".join((name or "").replace("\u00b6", "1").strip().split())


def safe_folder_name(value: str, fallback: str = "Projeto") -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", normalize_project_name(value))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip(" .-")
    if not cleaned:
        cleaned = fallback
    if os.name == "nt" and cleaned.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        cleaned = f"{cleaned} - pasta"
    return cleaned[:80]


def unique_project_folder(projects: list[dict], preferred: str, exclude_slug: str | None = None) -> str:
    base = safe_folder_name(preferred, "Projeto")
    used = {
        str(project.get("folder_name") or project.get("project_folder") or project.get("slug") or "").strip().lower()
        for project in projects
        if project.get("slug") != exclude_slug
    }
    folder = base
    index = 2
    while folder.lower() in used:
        folder = f"{base} {index}"
        index += 1
    return folder


def ensure_project_folder(config: dict, project: dict) -> Path:
    folder = str(project.get("folder_name") or "").strip()
    if not folder:
        old_slug = str(project.get("slug") or slugify(project.get("name") or "Projeto"))
        old_slug_dir = PROFILES_DIR / "projetos" / old_slug
        if old_slug_dir.exists():
            folder = old_slug
        else:
            folder = unique_project_folder(config.setdefault("projects", []), project.get("name") or old_slug, exclude_slug=project.get("slug"))
        project["folder_name"] = folder
    path = PROFILES_DIR / "projetos" / folder
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_project(config: dict, name: str) -> dict:
    clean = normalize_project_name(name)
    if not clean:
        raise ValueError("Project name is required")
    projects = config.setdefault("projects", [])
    for project in projects:
        if str(project.get("name", "")).strip().lower() == clean.lower():
            project.setdefault("slug", slugify(clean))
            project["name"] = clean
            ensure_project_folder(config, project)
            return project
    used = {p.get("slug") for p in projects}
    slug = slugify(clean)
    base_slug = slug
    index = 2
    while slug in used:
        slug = f"{base_slug}-{index}"
        index += 1
    project = {"slug": slug, "name": clean, "created_at": now_iso()}
    project["folder_name"] = unique_project_folder(projects, clean, exclude_slug=slug)
    projects.append(project)
    ensure_project_folder(config, project)
    return project


def project_name(config: dict, profile: dict) -> str:
    slug = profile.get("project_slug")
    for project in config.get("projects", []):
        if project.get("slug") == slug:
            return project.get("name", slug)
    return profile.get("project") or slug or "-"


def cleanup_unused_autocreated_projects(config: dict) -> None:
    used = {
        str(profile.get("project_slug") or profile.get("project") or "").strip().lower()
        for profile in config.get("profiles", [])
        if not profile_is_starter(profile)
    }
    if used:
        return
    config["projects"] = [
        project
        for project in config.get("projects", [])
        if str(project.get("slug", "")).strip().lower() not in OLD_AUTOCREATED_PROJECT_SLUGS
    ]


def repaired_legacy_brazil_number(value: str) -> str:
    digits = phone_digits(value)
    if not digits.startswith("55") or len(digits) <= 13:
        return ""
    candidates: list[tuple[int, int, str]] = []
    for suffix_len in range(1, 5):
        if len(digits) <= suffix_len:
            continue
        candidate = digits[:-suffix_len]
        normalized = normalize_phone_digits(candidate)
        if normalized.startswith("55") and len(normalized) == 13:
            score = 0 if len(candidate) == 12 and candidate[4:5] == "9" else 1
            candidates.append((score, suffix_len, normalized))
    if not candidates:
        return ""
    _, _suffix_len, normalized = sorted(candidates)[0]
    return format_phone_number(normalized)


def repair_legacy_detected_numbers(config: dict) -> None:
    for profile in config.get("profiles", []):
        if profile_is_starter(profile):
            continue
        repaired = repaired_legacy_brazil_number(profile.get("number") or profile.get("number_digits") or "")
        if not repaired:
            continue
        repaired_digits = phone_digits(repaired)
        if phone_digits(profile.get("number") or "") == repaired_digits:
            continue
        profile["number"] = repaired
        profile["number_digits"] = repaired_digits
        profile["legacy_number_repaired_at"] = now_iso()
        profile["updated_at"] = now_iso()


def ensure_profiles_config() -> dict:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    (PROFILES_DIR / "projetos").mkdir(parents=True, exist_ok=True)
    if PROFILES_CONFIG.exists():
        raw = PROFILES_CONFIG.read_text(encoding="utf-8-sig")
        config = json.loads(raw) if raw.strip() else {}
    else:
        config = {}
    config.setdefault("version", 1)
    config.setdefault("profiles_dir", str(PROFILES_DIR))
    config.setdefault("next_port", 8101)
    config.setdefault("profiles", [])
    config.setdefault("projects", [])
    cleanup_unused_autocreated_projects(config)
    repair_legacy_detected_numbers(config)
    for project in config.get("projects", []):
        ensure_project_folder(config, project)
    for profile in config.get("profiles", []):
        if profile.get("name"):
            profile["name"] = normalize_profile_name(str(profile.get("name", "")))
        if profile_is_starter(profile):
            continue
        if not profile.get("project_slug"):
            project = ensure_project(config, profile.get("project") or "Sem projeto")
            profile["project_slug"] = project["slug"]
            profile["project"] = project["name"]
        else:
            project = next((item for item in config.get("projects", []) if item.get("slug") == profile.get("project_slug")), None)
            if not project:
                project = ensure_project(config, profile.get("project") or profile.get("project_slug") or "Sem projeto")
                profile["project_slug"] = project["slug"]
                profile["project"] = project["name"]
        ensure_project_folder(config, project)
        profile["project_folder"] = project.get("folder_name") or project.get("slug")
    return config


def save_profiles_config(config: dict) -> None:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_CONFIG.write_text(json.dumps(config, indent=2, ensure_ascii=True), encoding="utf-8")


def load_state() -> dict:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_PATH.exists():
        return {"version": 1, "profiles": {}, "pending_deletes": []}
    raw = STATE_PATH.read_text(encoding="utf-8-sig")
    state = json.loads(raw) if raw.strip() else {}
    state.setdefault("version", 1)
    state.setdefault("profiles", {})
    state.setdefault("pending_deletes", [])
    return state


def save_state(state: dict) -> None:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=True), encoding="utf-8")


def profile_paths(profile: dict) -> dict[str, Path]:
    custom_dir = str(profile.get("profile_dir", "") or "").strip()
    if custom_dir:
        profile_dir = Path(custom_dir)
    else:
        project_folder = str(profile.get("project_folder") or profile.get("project_slug") or slugify(profile.get("project") or "sem-projeto"))
        profile_dir = PROFILES_DIR / "projetos" / project_folder / profile["slug"]
    bridge_dir = profile_dir / "whatsapp-bridge"
    store_dir = bridge_dir / "store"
    return {
        "profile_dir": profile_dir,
        "bridge_dir": bridge_dir,
        "store_dir": store_dir,
        "messages_db": store_dir / "messages.db",
        "session_db": store_dir / "whatsapp.db",
        "pid_path": profile_dir / ".bridge.pid",
        "out_log": profile_dir / "bridge.out.log",
        "err_log": profile_dir / "bridge.err.log",
    }


def path_is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def ensure_profile_dirs(profile: dict) -> None:
    paths = profile_paths(profile)
    paths["store_dir"].mkdir(parents=True, exist_ok=True)


def port_open(port: int) -> bool:
    if port <= 0:
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.03)
            return sock.connect_ex(("127.0.0.1", int(port))) == 0
    except OSError:
        return False


def process_id_alive(pid: int) -> bool:
    if os.name == "nt":
        try:
            kernel32 = ctypes.windll.kernel32
            process = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if process:
                kernel32.CloseHandle(process)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def pid_alive(pid_path: Path) -> bool:
    if not pid_path.exists():
        return False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    return process_id_alive(pid)


def profile_running(profile: dict) -> bool:
    paths = profile_paths(profile)
    alive = pid_alive(paths["pid_path"])
    if not alive:
        paths["pid_path"].unlink(missing_ok=True)
    return alive or port_open(int(profile.get("port", 0) or 0))


def process_ids_for_port(port: int) -> list[int]:
    if port <= 0:
        return []
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True,
                text=True,
                timeout=6,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError):
            return []
        pids: set[int] = set()
        suffix = f":{int(port)}"
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 5 or parts[0].upper() != "TCP":
                continue
            local_addr = parts[1]
            state = parts[3].upper()
            pid = parts[-1]
            if state == "LISTENING" and local_addr.endswith(suffix) and pid.isdigit():
                pids.add(int(pid))
        return sorted(pids)
    try:
        result = subprocess.run(
            ["lsof", f"-tiTCP:{int(port)}", "-sTCP:LISTEN"],
            capture_output=True,
            text=True,
            timeout=4,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return sorted({int(line.strip()) for line in result.stdout.splitlines() if line.strip().isdigit()})


def terminate_process(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/f", "/t", "/pid", str(pid)],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return
    try:
        os.kill(pid, 15)
    except OSError:
        pass


def stop_profile(profile: dict, wait_seconds: float = 4.0) -> None:
    paths = profile_paths(profile)
    pid_path = paths["pid_path"]
    port = int(profile.get("port", 0) or 0)
    pids: set[int] = set(process_ids_for_port(port))
    try:
        if pid_path.exists():
            pids.add(int(pid_path.read_text(encoding="utf-8").strip()))
    except (OSError, ValueError):
        pid_path.unlink(missing_ok=True)
    for pid in sorted(pids):
        terminate_process(pid)
    deadline = time.time() + max(0.0, wait_seconds)
    while time.time() < deadline:
        alive = any(process_id_alive(pid) for pid in pids)
        if not alive and not port_open(port):
            break
        time.sleep(0.2)
    pid_path.unlink(missing_ok=True)


def pending_delete_dir() -> Path:
    return PROFILES_DIR / "_pending-delete"


def unique_pending_delete_path(profile_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = pending_delete_dir() / f"{profile_dir.name}-{stamp}"
    candidate = base
    index = 2
    while candidate.exists():
        candidate = base.with_name(f"{base.name}-{index}")
        index += 1
    return candidate


def add_pending_delete(state: dict, path: Path, profile_name: str, error: str) -> None:
    pending = state.setdefault("pending_deletes", [])
    path_text = str(path)
    for item in pending:
        if item.get("path") == path_text:
            item["last_error"] = error
            item["updated_at"] = now_iso()
            return
    pending.append(
        {
            "path": path_text,
            "profile": profile_name,
            "created_at": now_iso(),
            "last_error": error,
        }
    )


def try_delete_profile_dir(profile_dir: Path, state: dict, profile_name: str) -> tuple[bool, str | None]:
    if not profile_dir.exists():
        return True, None
    try:
        shutil.rmtree(profile_dir)
        return True, None
    except OSError as first_error:
        cleanup_dir = profile_dir
        try:
            target = unique_pending_delete_path(profile_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            profile_dir.rename(target)
            cleanup_dir = target
        except OSError:
            cleanup_dir = profile_dir
        add_pending_delete(state, cleanup_dir, profile_name, str(first_error))
        return False, str(first_error)


def start_profile(profile: dict, visible: bool = False) -> tuple[bool, str]:
    ensure_profile_dirs(profile)
    if not BRIDGE_BINARY.exists():
        return False, f"Bridge nao encontrada: {BRIDGE_BINARY}"
    if profile_running(profile):
        return True, "Bridge ja esta rodando."

    paths = profile_paths(profile)
    env = os.environ.copy()
    env["WHATSAPP_MCP_PORT"] = str(profile.get("port"))
    kwargs = {
        "cwd": str(paths["bridge_dir"]),
        "env": env,
    }
    if os.name == "nt":
        if visible:
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        else:
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    else:
        kwargs["start_new_session"] = True

    if visible:
        proc = subprocess.Popen([str(BRIDGE_BINARY)], **kwargs)
    else:
        out = open(paths["out_log"], "a", encoding="utf-8", errors="replace")
        err = open(paths["err_log"], "a", encoding="utf-8", errors="replace")
        kwargs["stdout"] = out
        kwargs["stderr"] = err
        try:
            proc = subprocess.Popen([str(BRIDGE_BINARY)], **kwargs)
        finally:
            out.close()
            err.close()
    paths["pid_path"].write_text(str(proc.pid), encoding="ascii")
    return True, f"Bridge iniciada no perfil {profile.get('slug')}."


def db_stats(profile: dict) -> dict:
    if not profile_configured(profile):
        return empty_db_stats()
    db = profile_paths(profile)["messages_db"]
    if not db.exists():
        return empty_db_stats()
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=0.2) as conn:
        cur = conn.cursor()
        messages = cur.execute("select count(*) from messages").fetchone()[0]
        chats = cur.execute("select count(*) from chats").fetchone()[0]
        last = cur.execute("select max(timestamp) from messages").fetchone()[0]
    return {"exists": True, "messages": messages, "chats": chats, "last": last, "mtime": None}


def empty_db_stats() -> dict:
    return {"exists": False, "messages": 0, "chats": 0, "last": None, "mtime": None}


def cached_db_stats(profile: dict, state: dict | None = None) -> dict:
    if not profile_configured(profile):
        return empty_db_stats()
    state = state or {}
    messages = state.get("current_messages", state.get("last_observed_messages"))
    chats = state.get("current_chats")
    last = state.get("current_last_message")
    signature = str(state.get("last_signature") or "")
    if signature:
        parts = signature.split("|", 2)
        if messages is None and parts:
            try:
                messages = int(parts[0])
            except (TypeError, ValueError):
                messages = 0
        if not last and len(parts) > 1 and parts[1] not in {"", "None"}:
            last = parts[1]
    db_exists = False
    try:
        db_exists = profile_paths(profile)["messages_db"].exists()
    except OSError:
        db_exists = False
    return {
        "exists": bool(db_exists or messages or last),
        "messages": int(messages or 0),
        "chats": None if chats is None else int(chats or 0),
        "last": last,
        "mtime": state.get("current_db_mtime"),
        "cached": True,
    }


def read_profile_log(profile: dict, lines: int = 80) -> list[str]:
    paths = profile_paths(profile)
    log_path = paths["out_log"]
    if not log_path.exists():
        return ["Log ainda nao encontrado para este perfil."]
    with log_path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - 65536), os.SEEK_SET)
        raw = handle.read().decode("utf-8", errors="replace").splitlines()
    return [strip_ansi(line) for line in raw if line.strip()][-lines:]


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


def load_wscript_shell():
    try:
        import win32com.client

        return win32com.client.Dispatch("WScript.Shell")
    except Exception as exc:
        raise RuntimeError(f"COM/WScript indisponivel para gerenciar atalhos: {exc}") from exc


def panel_pythonw_path() -> Path:
    running_python = Path(sys.executable)
    if running_python.exists() and (not IS_WINDOWS or running_python.name.lower() == "pythonw.exe"):
        return running_python
    pyvenv_cfg = PANEL_RUNTIME_VENV / "pyvenv.cfg"
    if IS_WINDOWS and pyvenv_cfg.exists():
        try:
            for line in pyvenv_cfg.read_text(encoding="utf-8-sig").splitlines():
                if line.lower().startswith("home"):
                    python_home = line.split("=", 1)[1].strip()
                    candidate = Path(python_home) / "pythonw.exe"
                    if candidate.exists() and "CodexSandboxOffline" not in str(candidate):
                        return candidate
        except OSError:
            pass
    return PANEL_VENV_PYTHONW


def read_shortcut(path: Path) -> dict:
    return {
        "exists": path.exists(),
        "target": "",
        "arguments": "",
        "working_directory": "",
    }


def is_expected_autostart(info: dict) -> bool:
    expected_target = str(panel_pythonw_path())
    expected_launcher = str(PANEL_LAUNCHER)
    return (
        info.get("exists")
        and info.get("target") == expected_target
        and expected_launcher in info.get("arguments", "")
        and "--minimized" in info.get("arguments", "")
    )


def expected_windows_autostart_command() -> str:
    return f'"{panel_pythonw_path()}" "{PANEL_LAUNCHER}" --minimized'


def read_windows_autostart() -> str:
    if not IS_WINDOWS:
        return ""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, WINDOWS_RUN_NAME)
            return str(value)
    except Exception:
        return ""


def write_windows_autostart(command: str) -> None:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, WINDOWS_RUN_NAME, 0, winreg.REG_SZ, command)


def delete_windows_autostart() -> None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, WINDOWS_RUN_NAME)
    except FileNotFoundError:
        pass


def cleanup_windows_startup_shortcuts() -> list[str]:
    notes: list[str] = []
    for shortcut_path in [STARTUP_SHORTCUT, LEGACY_STARTUP_SHORTCUT]:
        if shortcut_path.exists():
            try:
                shortcut_path.unlink()
            except OSError as exc:
                notes.append(f"nao removi {shortcut_path.name}: {exc}")
    return notes


def autostart_state() -> tuple[str, str]:
    if IS_MAC:
        if MAC_LAUNCH_AGENT.exists():
            return "on", "Ativo: existe LaunchAgent para iniciar o painel com o macOS."
        return "off", "Desativado: o painel nao inicia automaticamente com o macOS."
    if not IS_WINDOWS:
        return "unsupported", "Auto-start automatico nesta UI esta disponivel apenas em Windows e macOS."
    registry_value = read_windows_autostart()
    if registry_value:
        if registry_value == expected_windows_autostart_command():
            return "on", "Ativo: Registro do Windows inicia o painel minimizado."
        return "review", "Revisar: auto-start do Registro aponta para caminho antigo."
    if STARTUP_SHORTCUT.exists() or LEGACY_STARTUP_SHORTCUT.exists():
        return "review", "Revisar: existe atalho legado na pasta Startup. O padrao atual e Registro do Windows."
    return "off", "Desativado: o painel nao inicia automaticamente com o Windows."


def write_mac_launch_agent(python_bin: Path) -> None:
    MAC_LAUNCH_AGENT_DIR.mkdir(parents=True, exist_ok=True)
    out_log = PANEL_DIR / "launchagent.out.log"
    err_log = PANEL_DIR / "launchagent.err.log"
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.whatsapp-mcp.tray</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_bin}</string>
    <string>{PANEL_LAUNCHER}</string>
    <string>--minimized</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{PANEL_DIR}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardOutPath</key>
  <string>{out_log}</string>
  <key>StandardErrorPath</key>
  <string>{err_log}</string>
</dict>
</plist>
"""
    MAC_LAUNCH_AGENT.write_text(plist, encoding="utf-8")


def reload_mac_launch_agent() -> None:
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", domain, str(MAC_LAUNCH_AGENT)], capture_output=True, text=True, timeout=5)
    subprocess.run(["launchctl", "bootstrap", domain, str(MAC_LAUNCH_AGENT)], capture_output=True, text=True, timeout=5)
    subprocess.run(["launchctl", "enable", f"{domain}/com.whatsapp-mcp.tray"], capture_output=True, text=True, timeout=5)


def set_autostart_enabled(enabled: bool) -> tuple[bool, str]:
    if IS_MAC:
        try:
            if enabled:
                python_bin = panel_pythonw_path()
                if not python_bin.exists():
                    return False, f"Python do painel nao encontrado: {python_bin}"
                if not PANEL_LAUNCHER.exists():
                    return False, f"Launcher do painel nao encontrado: {PANEL_LAUNCHER}"
                write_mac_launch_agent(python_bin)
                try:
                    reload_mac_launch_agent()
                except Exception:
                    pass
                return True, "Auto-start ativado. O painel vai iniciar minimizado com o macOS."
            if MAC_LAUNCH_AGENT.exists():
                try:
                    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(MAC_LAUNCH_AGENT)], capture_output=True, text=True, timeout=5)
                except Exception:
                    pass
                MAC_LAUNCH_AGENT.unlink()
            return True, "Auto-start desativado."
        except Exception as exc:
            return False, f"Nao consegui alterar o auto-start no macOS: {exc}"
    if not IS_WINDOWS:
        return False, "Auto-start automatico nesta UI esta disponivel apenas em Windows e macOS."
    try:
        if enabled:
            pythonw = panel_pythonw_path()
            if not pythonw.exists():
                return False, f"pythonw.exe do painel nao encontrado: {pythonw}"
            if not PANEL_LAUNCHER.exists():
                return False, f"Launcher do painel nao encontrado: {PANEL_LAUNCHER}"
            write_windows_autostart(expected_windows_autostart_command())
            notes = cleanup_windows_startup_shortcuts()
            suffix = f" Itens legados em Startup precisam revisao manual: {'; '.join(notes)}." if notes else ""
            return True, f"Auto-start ativado via Registro do Windows. O painel vai iniciar minimizado.{suffix}"
        delete_windows_autostart()
        notes = cleanup_windows_startup_shortcuts()
        suffix = f" Alguns atalhos legados nao foram removidos: {'; '.join(notes)}." if notes else ""
        return True, f"Auto-start desativado.{suffix}"
    except Exception as exc:
        return False, f"Nao consegui alterar o auto-start: {exc}"


class ProfileDialog:
    def __init__(self, app: "ProfilesApp", profile: dict | None = None) -> None:
        self.app = app
        self.profile = profile
        first_profile = bool(profile and profile_is_starter(profile))
        self.win = tk.Toplevel(app.root)
        self.win.withdraw()
        apply_window_icon(self.win)
        self.win.title("Adicionar numero WhatsApp" if first_profile or not profile else "Editar numero WhatsApp")
        self.win.configure(bg=BG)
        self.win.transient(app.root)

        frame = tk.Frame(self.win, bg=BG, padx=16, pady=14)
        frame.pack(fill=tk.BOTH, expand=True)

        title = "Adicionar numero" if first_profile or not profile else "Editar numero"
        tk.Label(frame, text=title, bg=BG, fg=TEXT, font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        project_value = project_name(app.config, profile) if profile and not profile_is_starter(profile) else ""
        self.project = self._project_entry(frame, 1, "Projeto", project_value)
        self.name = self._entry(frame, 3, "Nome do perfil", profile.get("name", "") if profile and not first_profile else "")
        raw_number = "" if (profile and str(profile.get("number", "")).upper() == "PREENCHER_NUMERO") else (profile.get("number", "") if profile else "")
        self.number = self._entry(frame, 4, "Numero WhatsApp", format_phone_number(raw_number))
        self.number.bind("<FocusOut>", lambda _event: self.format_number_field())
        tk.Label(
            frame,
            text="Opcional. Pode deixar vazio: depois do QR o painel tenta identificar o numero automaticamente. Exemplo ficticio: +55 (11) 91234-5678.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 8),
            wraplength=510,
            justify=tk.LEFT,
        ).grid(row=5, column=1, columnspan=2, sticky="w", pady=(0, 5))
        self.description = self._entry(frame, 6, "Descricao", profile.get("description", "") if profile and not first_profile else "")

        note = (
            "Digite um novo projeto ou escolha um projeto ja criado. "
            "Ao salvar, o painel cria a pasta do projeto e a pasta deste perfil dentro da base geral."
        )
        tk.Label(frame, text=note, bg=BG, fg=MUTED, wraplength=620, justify=tk.LEFT).grid(row=7, column=0, columnspan=3, sticky="w", pady=12)

        buttons = tk.Frame(frame, bg=BG)
        buttons.grid(row=8, column=0, columnspan=3, sticky="e", pady=(12, 0))
        app._button(buttons, "Cancelar", GRAY, self.win.destroy, width=10).pack(side=tk.RIGHT, padx=4)
        app._button(buttons, "Salvar", GREEN, self.save, width=10).pack(side=tk.RIGHT, padx=4)

        frame.columnconfigure(1, weight=1)
        center_child_window(self.win, app.root, 680, 430)
        self.win.deiconify()
        self.win.lift(app.root)
        self.win.grab_set()
        self.win.focus_force()

    def _entry(self, parent: tk.Frame, row: int, label: str, value: str) -> tk.Entry:
        tk.Label(parent, text=label, bg=BG, fg=TEXT, font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
        entry = tk.Entry(parent)
        entry.insert(0, value)
        entry.grid(row=row, column=1, sticky="ew", pady=5)
        return entry

    def _project_entry(self, parent: tk.Frame, row: int, label: str, value: str) -> ttk.Combobox:
        tk.Label(parent, text=label, bg=BG, fg=TEXT, font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
        values = sorted({p.get("name", "") for p in self.app.config.get("projects", []) if p.get("name")}, key=str.lower)
        combo = ttk.Combobox(parent, values=values)
        combo.set(value or "")
        combo.grid(row=row, column=1, columnspan=2, sticky="ew", pady=5)
        help_text = "Digite um novo projeto" if not values else "Escolha um projeto existente ou digite outro para criar"
        tk.Label(parent, text=help_text, bg=BG, fg=MUTED, font=("Segoe UI", 8), justify=tk.LEFT).grid(row=row + 1, column=1, columnspan=2, sticky="w", pady=(0, 5))
        return combo

    def format_number_field(self) -> None:
        formatted = format_phone_number(self.number.get())
        self.number.delete(0, tk.END)
        self.number.insert(0, formatted)

    def save(self) -> None:
        name = normalize_profile_name(self.name.get())
        number = format_phone_number(self.number.get().strip())
        description = self.description.get().strip()
        project_text = normalize_project_name(self.project.get())
        if not name:
            mb.showwarning("Perfil", "Informe um nome para o perfil.")
            return
        if not project_text:
            mb.showwarning("Projeto", "Informe ou selecione um projeto.")
            return
        if not CONFIG.get("profiles_base_confirmed"):
            mb.showwarning("Pasta geral", "Escolha a pasta geral da base antes de cadastrar o primeiro perfil.")
            self.app.open_base_setup(first_time=True, after=lambda: ProfileDialog(self.app, self.profile))
            self.win.destroy()
            return

        config = self.app.config
        project = ensure_project(config, project_text)
        number_key = phone_digits(number)
        duplicate = None
        if number_key:
            duplicate = next((p for p in config.get("profiles", []) if p is not self.profile and phone_digits(str(p.get("number", ""))) == number_key), None)
        if duplicate and not mb.askyesno("Numero repetido", f"Ja existe um perfil com este numero: {duplicate.get('name')}.\n\nCriar outro perfil separado mesmo assim?"):
            return

        existing = None
        if self.profile and not profile_is_starter(self.profile):
            for item in config.get("profiles", []):
                if item.get("slug") == self.profile.get("slug"):
                    existing = item
                    break
        if existing:
            existing["name"] = name
            existing["number"] = number
            existing["number_digits"] = number_key
            existing["description"] = description
            existing["project"] = project["name"]
            existing["project_slug"] = project["slug"]
            existing["project_folder"] = project.get("folder_name") or project.get("slug")
            existing["profile_dir"] = ""
            existing["updated_at"] = now_iso()
            profile = existing
            should_open_qr = False
        else:
            config["profiles"] = [p for p in config.get("profiles", []) if not profile_is_starter(p)]
            used = {p["slug"] for p in config.get("profiles", [])}
            base_slug = slugify(f"{project['name']}-{name}-{number_key}" if number_key else f"{project['name']}-{name}")
            slug = base_slug
            index = 2
            while slug in used:
                slug = f"{base_slug}-{index}"
                index += 1
            port = int(config.get("next_port", 8101))
            used_ports = {int(p.get("port", 0)) for p in config.get("profiles", [])}
            while port in used_ports:
                port += 1
            profile = {
                "slug": slug,
                "name": name,
                "number": number,
                "number_digits": number_key,
                "description": description,
                "project": project["name"],
                "project_slug": project["slug"],
                "project_folder": project.get("folder_name") or project.get("slug"),
                "profile_dir": "",
                "port": port,
                "enabled": True,
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
            config.setdefault("profiles", []).append(profile)
            config["next_port"] = port + 1
            should_open_qr = True

        ensure_profile_dirs(profile)
        save_profiles_config(config)
        self.app.last_action = f"Perfil salvo: {profile['name']}."
        self.app.reload_data(select_slug=profile["slug"])
        self.win.destroy()
        if should_open_qr:
            self.app.root.after(350, self.app.open_qr_for_selected)


class ProfilesApp:
    def __init__(self, minimized: bool = False) -> None:
        self.config = ensure_profiles_config()
        save_profiles_config(self.config)
        self.state = load_state()
        self.selected_slug: str | None = None
        self.last_action = "Painel de perfis iniciado."
        self.qr_windows: dict[str, tk.Toplevel] = {}
        self.control_server = None
        self.tray_icon = None
        self.tray_process = None
        self.tray_started = False
        self.shutting_down = False
        self.settings_window = None
        self.base_setup_window = None
        self.tray_status_key = ""
        self.tray_status_label = "Aguardando perfis"
        self.ui_actions: queue.Queue = queue.Queue()
        self.root_hwnd: int | None = None
        self.start_minimized = minimized
        self.refreshing = False

        set_process_app_id()
        self.root = tk.Tk()
        apply_window_icon(self.root)
        self.root.title("WhatsApp MCP - Perfis")
        self.root.geometry("1080x720")
        self.root.configure(bg=BG)
        try:
            self.root.attributes("-topmost", False)
        except tk.TclError:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.bind("<<ShowPanel>>", lambda _event: self.show())
        self.install_macos_reopen_handler()
        self._ui()
        try:
            self.root.update_idletasks()
            self.root_hwnd = int(self.root.winfo_id())
            action_log(f"window-created hwnd={self.root_hwnd}")
        except tk.TclError as exc:
            action_log(f"window-created-error {exc}")
        if minimized:
            self.root.withdraw()
        self.root.after(200, self.process_ui_actions)
        self.root.after(500, self.startup_ready)
        self.root.after(1000, self.heartbeat)
        self.root.after(POLL_MS, self.tick)

    def install_macos_reopen_handler(self) -> None:
        if not IS_MAC:
            return
        try:
            self.root.createcommand("whatsapp_mcp_reopen", self.show)
            self.root.tk.eval("proc ::tk::mac::ReopenApplication {} {whatsapp_mcp_reopen}")
        except tk.TclError as exc:
            action_log(f"mac-reopen-handler-error {exc}")

    def _ui(self) -> None:
        top = tk.Frame(self.root, bg=PANEL, padx=16, pady=12)
        top.pack(fill=tk.X)
        tk.Label(top, text="WhatsApp MCP - Perfis Locais", bg=PANEL, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        self.status = tk.Label(top, text="Carregando", bg=PANEL, fg=YELLOW, font=("Segoe UI", 12, "bold"))
        self.status.pack(side=tk.RIGHT)

        body = tk.Frame(self.root, bg=BG, padx=16, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        global_bar = tk.Frame(body, bg=BG)
        global_bar.pack(fill=tk.X, pady=(0, 10))
        self.add_button = self._button(global_bar, "Cadastrar primeiro perfil", PURPLE, self.new_profile, width=22)
        self.add_button.pack(side=tk.LEFT, padx=4)
        self.sync_all_button = self._button(global_bar, "Sync todos", GREEN, self.sync_all, width=13)
        self.sync_all_button.pack(side=tk.LEFT, padx=4)
        self.pause_all_button = self._button(global_bar, "Pausar todos", RED, self.pause_all, width=13)
        self.pause_all_button.pack(side=tk.LEFT, padx=4)
        self.settings_button = self._button(global_bar, "Configuracoes", GRAY, self.open_settings, width=16)
        self.settings_button.pack(side=tk.RIGHT, padx=(10, 4))

        self.summary_frame = tk.Frame(body, bg=PANEL, padx=12, pady=10)
        self.summary_frame.pack(fill=tk.X, pady=(0, 10))
        self.summary_labels: dict[str, tk.Label] = {}
        for key, title in [
            ("profiles", "Numeros"),
            ("projects", "Projetos"),
            ("running", "Rodando"),
            ("waiting", "Aguardando sync"),
            ("paused", "Pausados"),
            ("messages", "Mensagens"),
        ]:
            box = tk.Frame(self.summary_frame, bg=PANEL)
            box.pack(side=tk.LEFT, padx=(0, 24))
            tk.Label(box, text=title, bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
            value = tk.Label(box, text="-", bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold"))
            value.pack(anchor="w")
            self.summary_labels[key] = value

        self.step_frame = tk.Frame(body, bg=PANEL, padx=12, pady=10)
        self.step_frame.pack(fill=tk.X, pady=(0, 10))
        step_top = tk.Frame(self.step_frame, bg=PANEL)
        step_top.pack(fill=tk.X)
        step_text = tk.Frame(step_top, bg=PANEL)
        step_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(step_text, text="Proximo passo", bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.next_title = tk.Label(step_text, text="Selecione um perfil", bg=PANEL, fg=TEXT, font=("Segoe UI", 14, "bold"), wraplength=720, justify=tk.LEFT)
        self.next_title.pack(anchor="w", fill=tk.X, pady=(2, 2))
        self.next_detail = tk.Label(step_text, text="", bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=720, justify=tk.LEFT)
        self.next_detail.pack(anchor="w", fill=tk.X)
        self.primary_button = self._button(step_top, "Proximo passo", BLUE, self.primary_selected_action, width=24)
        self.primary_button.pack(side=tk.RIGHT, padx=(12, 0))

        self.actions = tk.Frame(self.step_frame, bg=PANEL)
        self.actions.pack(fill=tk.X, pady=(10, 0))
        self.edit_button = self._button(self.actions, "Editar", GRAY, self.edit_selected, width=14)
        self.edit_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=4)
        self.qr_button = self._button(self.actions, "Conectar QR", BLUE, self.open_qr_for_selected, width=16)
        self.qr_button.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.sync_button = self._button(self.actions, "Sync agora", GREEN, self.sync_selected, width=14)
        self.sync_button.grid(row=0, column=2, sticky="ew", padx=4, pady=4)
        self.pause_button = self._button(self.actions, "Pausar", RED, self.toggle_pause_selected, width=14)
        self.pause_button.grid(row=0, column=3, sticky="ew", padx=4, pady=4)
        self.folder_button = self._button(self.actions, "Abrir projeto", GRAY, self.open_selected_folder, width=14)
        self.folder_button.grid(row=0, column=4, sticky="ew", padx=4, pady=4)
        self.copy_button = self._button(self.actions, "Copiar DB", GRAY, self.copy_selected_db, width=14)
        self.copy_button.grid(row=0, column=5, sticky="ew", padx=4, pady=4)
        self.remove_button = self._button(self.actions, "Excluir perfil", RED, self.remove_selected_profile, width=14)
        self.remove_button.grid(row=0, column=6, sticky="ew", padx=(4, 0), pady=4)
        for index in range(7):
            self.actions.columnconfigure(index, weight=1)

        self.info = tk.Text(self.step_frame, height=5, bg=PANEL, fg=TEXT, relief=tk.FLAT, wrap=tk.WORD, font=("Segoe UI", 9))
        self.info.tag_configure("key", foreground=TEXT, font=("Segoe UI", 9, "bold"))
        self.info.tag_configure("good", foreground=GREEN, font=("Segoe UI", 9, "bold"))
        self.info.tag_configure("warn", foreground=YELLOW, font=("Segoe UI", 9, "bold"))
        self.info.tag_configure("bad", foreground=RED, font=("Segoe UI", 9, "bold"))
        self.info.tag_configure("muted", foreground=MUTED)
        self.info.configure(state=tk.DISABLED)
        self.info.pack(fill=tk.X, pady=(6, 0))

        main = tk.Frame(body, bg=BG)
        main.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main, bg=BG)
        left.pack(fill=tk.BOTH, expand=True)
        tk.Label(left, text="Perfis cadastrados", bg=BG, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        columns = ("project", "name", "number", "status", "messages", "last", "next")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=10)
        headings = {
            "project": "Projeto",
            "name": "Perfil",
            "number": "Numero",
            "status": "Fase",
            "messages": "Msgs",
            "last": "Ultima msg",
            "next": "Proxima acao",
        }
        widths = {"project": 115, "name": 170, "number": 150, "status": 170, "messages": 70, "last": 150, "next": 205}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.on_tree_activate)
        self.tree.bind("<Return>", self.on_tree_activate)
        self.empty_state = tk.Frame(left, bg=PANEL_2, padx=24, pady=22)
        tk.Label(self.empty_state, text="Nenhum WhatsApp cadastrado", bg=PANEL_2, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(
            self.empty_state,
            text="Cadastre o primeiro perfil e conecte o QR. A pasta geral e as opcoes do sistema ficam no botao Configuracoes.",
            bg=PANEL_2,
            fg=MUTED,
            font=("Segoe UI", 10),
            wraplength=620,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(8, 14))
        self.empty_base_label = tk.Label(self.empty_state, text="", bg=PANEL_2, fg=MUTED, font=("Segoe UI", 9), wraplength=620, justify=tk.LEFT)
        self.empty_base_label.pack(anchor="w", pady=(0, 12))
        self._button(self.empty_state, "Cadastrar primeiro perfil", PURPLE, self.new_profile, width=26).pack(anchor="w")

        log_frame = tk.Frame(body, bg=BG)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        tk.Label(log_frame, text="Log do perfil selecionado", bg=BG, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
        log_body = tk.Frame(log_frame, bg=BG)
        log_body.pack(fill=tk.BOTH, expand=True)
        self.log = tk.Text(log_body, bg=PANEL_2, fg=TEXT, relief=tk.FLAT, font=("Consolas", 9), height=8)
        scroll = ttk.Scrollbar(log_body, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _button(self, parent: tk.Widget, text: str, color: str, command, width: int | None = None) -> ActionButton:
        return ActionButton(parent, text, color, command, width)

    def primary_selected_action(self) -> None:
        profile = self.selected_profile()
        if not profile:
            self.new_profile()
            return
        configured = profile_configured(profile)
        state = self.state_for(profile["slug"])
        session = self.session_ready(profile, state) if configured else False
        running = profile_running(profile) if configured else False
        _title, _body, _text, _color, command, enabled = self.selected_action_plan(profile, session, running)
        if enabled:
            command()

    def _control(self) -> None:
        action_log("control-start")
        app = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path.startswith("/show"):
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"ok")
                    app.post_ui_action(app.show)
                    return
                if self.path.startswith("/status"):
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"running")
                    return
                if self.path.startswith("/sync-all"):
                    app.post_ui_action(app.sync_all)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"ok")
                    return
                if self.path.startswith("/pause-all"):
                    app.post_ui_action(app.pause_all)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"ok")
                    return
                if self.path.startswith("/shutdown"):
                    app.post_ui_action(lambda: app.shutdown_system(confirm=False))
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"ok")
                    return
                if self.path.startswith("/dump"):
                    with STACK_DUMP.open("w", encoding="utf-8") as handle:
                        faulthandler.dump_traceback(file=handle, all_threads=True)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"dumped")
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, _format: str, *_args) -> None:
                return

        try:
            self.control_server = ThreadingHTTPServer((CONTROL_HOST, CONTROL_PORT), Handler)
            threading.Thread(target=self.control_server.serve_forever, daemon=True).start()
            action_log(f"control-ready {CONTROL_HOST}:{CONTROL_PORT}")
        except OSError:
            self.control_server = None
            action_log(f"control-error port={CONTROL_PORT}")

    def _tray(self) -> None:
        if self.tray_started:
            return
        self.tray_started = True
        action_log("tray-start")
        try:
            pythonw = panel_pythonw_path()
            tray_agent = PANEL_DIR / "tray_agent.py"
            if not pythonw.exists() or not tray_agent.exists():
                action_log("tray-disabled missing-pythonw-or-agent")
                return
            args = [
                str(pythonw),
                str(tray_agent),
                "--base-url",
                f"http://{CONTROL_HOST}:{CONTROL_PORT}",
                "--icon",
                str(PANEL_ICON),
            ]
            kwargs = {}
            if os.name == "nt":
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.tray_process = subprocess.Popen(args, cwd=str(PANEL_DIR), **kwargs)
            action_log("tray-agent-started")
        except Exception as exc:
            try:
                (PANEL_DIR / "panel-tray.log").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
            except Exception:
                pass
            action_log(f"tray-error {exc}")

    def set_tray(self, key: str, label: str) -> None:
        self.tray_status_label = label
        if key == self.tray_status_key:
            return
        self.tray_status_key = key

    def startup_ready(self) -> None:
        try:
            action_log(f"startup-ready state={self.root.state()} minimized={self.start_minimized}")
            self.reload_data()
            if not self.start_minimized:
                self.show()
            self._control()
            self.schedule_startup_resume()
            self._tray()
            if not self.start_minimized:
                self.root.after(600, self.ensure_base_folder_confirmed)
            action_log("startup-ready-end")
        except Exception as exc:
            action_log(f"startup-ready-error {exc}")

    def schedule_startup_resume(self) -> None:
        if not STARTUP_RESUME_SYNC_ENABLED:
            return
        now = datetime.now()
        last_resume = parse_iso(self.state.get("last_startup_resume_at"))
        recent_resume = bool(last_resume and (now - last_resume).total_seconds() < STARTUP_RESUME_MIN_INTERVAL_SECONDS)

        eligible: list[tuple[dict, dict]] = []
        initial_pending_count = 0
        resumed_paused_count = 0
        for profile in self.configured_profiles():
            state = self.state_for(profile["slug"])
            initial_until = parse_iso(state.get("initial_sync_until"))
            initial_pending = bool(initial_until and not state.get("initial_sync_completed_at"))
            was_paused = bool(state.get("paused"))
            if was_paused and STARTUP_RESUME_CLEAR_PAUSED:
                state["paused"] = False
                state.pop("paused_by_user_at", None)
                state["startup_auto_resumed_at"] = now.isoformat(timespec="seconds")
                if initial_pending:
                    state["last_action"] = "Pausa anterior removida ao abrir o painel; primeira sync inteligente retomada."
                else:
                    state["last_action"] = "Pausa anterior removida ao abrir o painel."
                resumed_paused_count += 1
            elif was_paused:
                continue
            if profile_running(profile):
                continue
            if not self.session_ready(profile, state):
                continue
            if recent_resume and not was_paused and not initial_pending:
                continue
            if initial_pending:
                state["startup_resume_requested_at"] = now.isoformat(timespec="seconds")
                initial_pending_count += 1
                continue
            eligible.append((profile, state))

        def last_sync_key(item: tuple[dict, dict]) -> datetime:
            return parse_iso(item[1].get("last_sync_at")) or datetime.min

        eligible.sort(key=last_sync_key)
        for index, (_profile, state) in enumerate(eligible):
            jitter = random.randint(0, max(0, STARTUP_RESUME_JITTER_SECONDS))
            delay = STARTUP_RESUME_INITIAL_DELAY_SECONDS + (index * STARTUP_RESUME_STAGGER_SECONDS) + jitter
            scheduled = now + timedelta(seconds=delay)
            current_next = parse_iso(state.get("next_sync_at"))
            if not current_next or current_next <= now or current_next > scheduled:
                state["next_sync_at"] = scheduled.isoformat(timespec="seconds")
            state["sync_mode"] = "random"
            state["startup_resume_requested_at"] = now.isoformat(timespec="seconds")
            state["last_action"] = f"Sync de retomada agendada ao abrir o painel: {fmt_dt(state.get('next_sync_at'))}."

        total = len(eligible) + initial_pending_count
        if total:
            self.state["last_startup_resume_at"] = now.isoformat(timespec="seconds")
            self.last_action = (
                f"Sync de retomada agendada para {total} perfil(is), "
                f"com intervalo de {human_duration(STARTUP_RESUME_STAGGER_SECONDS)} para evitar sobrecarga."
            )
        elif resumed_paused_count:
            self.last_action = f"{resumed_paused_count} perfil(is) sairam da pausa ao abrir o painel."
        if total or resumed_paused_count:
            self.save_all()

    def post_ui_action(self, action) -> None:
        action_log(f"queue-action {getattr(action, '__name__', repr(action))}")
        self.ui_actions.put(action)

    def heartbeat(self) -> None:
        action_log("heartbeat")
        self.root.after(1000, self.heartbeat)

    def process_ui_actions(self) -> None:
        while True:
            try:
                action = self.ui_actions.get_nowait()
            except queue.Empty:
                break
            try:
                action_log(f"run-action {getattr(action, '__name__', repr(action))}")
                action()
            except Exception as exc:
                self.last_action = f"Erro na acao da UI: {exc}"
        self.root.after(200, self.process_ui_actions)

    def profiles(self) -> list[dict]:
        return [p for p in self.config.get("profiles", []) if p.get("enabled", True)]

    def configured_profiles(self) -> list[dict]:
        return [p for p in self.profiles() if profile_configured(p)]

    def starter_profile(self) -> dict | None:
        if self.configured_profiles():
            return None
        for profile in self.profiles():
            if profile_is_starter(profile):
                return profile
        return None

    def display_profiles(self) -> list[dict]:
        starter = self.starter_profile()
        return [p for p in self.config.get("profiles", []) if p.get("enabled", True) and p is not starter]

    def state_for(self, slug: str) -> dict:
        profiles_state = self.state.setdefault("profiles", {})
        item = profiles_state.setdefault(slug, {})
        item.setdefault("paused", False)
        return item

    def save_all(self) -> None:
        save_profiles_config(self.config)
        save_state(self.state)

    def cleanup_pending_deletes(self) -> None:
        pending = list(self.state.get("pending_deletes", []))
        if not pending:
            return
        kept = []
        cleaned = 0
        for item in pending:
            path = Path(str(item.get("path", "")))
            if not path:
                continue
            if not path_is_inside(path, PROFILES_DIR) or path.resolve(strict=False) == PROFILES_DIR.resolve(strict=False):
                item["last_error"] = "caminho fora da pasta geral; limpeza ignorada"
                kept.append(item)
                continue
            if not path.exists():
                cleaned += 1
                continue
            try:
                shutil.rmtree(path)
                cleaned += 1
            except OSError as exc:
                item["last_error"] = str(exc)
                item["updated_at"] = now_iso()
                kept.append(item)
        self.state["pending_deletes"] = kept
        if cleaned:
            self.last_action = f"Limpeza pendente concluida para {cleaned} pasta(s)."

    def reload_data(self, select_slug: str | None = None) -> None:
        self.config = ensure_profiles_config()
        self.state = load_state()
        self.cleanup_pending_deletes()
        if select_slug:
            self.selected_slug = select_slug
        elif not self.selected_slug:
            starter = self.starter_profile()
            if starter:
                self.selected_slug = starter["slug"]
            elif self.config.get("profiles"):
                self.selected_slug = self.config["profiles"][0]["slug"]
        self.refresh()

    def selected_profile(self) -> dict | None:
        if not self.selected_slug:
            return None
        for profile in self.config.get("profiles", []):
            if profile.get("slug") == self.selected_slug:
                return profile
        return None

    def on_select(self, _event=None) -> None:
        if self.refreshing:
            return
        selected = self.tree.selection()
        if selected:
            if self.selected_slug == selected[0]:
                return
            self.selected_slug = selected[0]
            self.refresh()

    def on_tree_activate(self, event=None) -> None:
        if event is not None and hasattr(event, "y"):
            row_id = self.tree.identify_row(event.y)
            if row_id:
                self.tree.selection_set(row_id)
                self.selected_slug = row_id
        self.primary_selected_action()

    def configure_button(self, button: tk.Widget, text: str | None = None, color: str | None = None, command=None, enabled: bool = True) -> None:
        changes = {"state": tk.NORMAL if enabled else tk.DISABLED}
        if text is not None:
            changes["text"] = text
        if color is not None:
            changes["bg"] = color
        if command is not None:
            changes["command"] = command
        button.configure(**changes)

    def selected_action_plan(self, profile: dict | None, session: bool = False, running: bool = False, detail: str = "") -> tuple[str, str, str, str, object, bool]:
        if not profile:
            return (
                "Nenhum numero selecionado",
                "Cadastre um perfil e conecte o QR para criar a base local.",
                "Cadastrar primeiro perfil",
                PURPLE,
                self.new_profile,
                True,
            )
        if not profile_configured(profile):
            if profile_is_starter(profile):
                return (
                    "Comece pelo primeiro numero",
                    "Depois de salvar os dados, o painel libera o QR deste WhatsApp.",
                    "Cadastrar primeiro perfil",
                    PURPLE,
                    self.edit_selected,
                    True,
                )
            return (
                "1. Complete os dados do numero",
                "Preencha nome, projeto e descricao. O numero pode ser informado agora ou preenchido depois do QR.",
                "Editar dados",
                PURPLE,
                self.edit_selected,
                True,
            )
        state = self.state_for(profile["slug"])
        if not session:
            return (
                "2. Conecte o WhatsApp pelo QR",
                "Abra o QR deste perfil e escaneie em Aparelhos conectados no celular. Os outros perfis continuam como estao.",
                "Conectar QR agora",
                BLUE,
                self.open_qr_for_selected,
                True,
            )
        if state.get("paused"):
            return (
                "Perfil pausado",
                "A base local nao atualiza enquanto este perfil estiver pausado.",
                "Retomar perfil",
                GREEN,
                self.resume_selected,
                True,
            )
        initial_until = parse_iso(state.get("initial_sync_until"))
        if initial_until and not state.get("initial_sync_completed_at"):
            if running:
                return (
                    "3. Primeira sync inteligente em andamento",
                    f"{detail}. Pode ocultar o painel; a sincronizacao continua em background e fecha sozinha quando estabilizar.",
                    "Ocultar na bandeja",
                    GRAY,
                    self.hide,
                    True,
                )
            return (
                "Retomar primeira sync inteligente",
                "Este perfil ja tem QR. Retome para continuar capturando ate a base estabilizar.",
                "Retomar sync",
                GREEN,
                self.sync_selected,
                True,
            )
        if running:
            return (
                "Sincronizando agora",
                "A porta local esta aberta apenas durante esta janela random. Ela fecha quando a base para de crescer ou bate o limite.",
                "Ocultar na bandeja",
                GRAY,
                self.hide,
                True,
            )
        return (
            "4. Pronto para sync random",
            "O perfil fica aguardando a proxima janela automatica. Cada janela abre, sincroniza e fecha quando estabilizar.",
            "Sincronizar agora",
            GREEN,
            self.sync_selected,
            True,
        )

    def update_selected_controls(self, profile: dict | None, status: str = "", key: str = "waiting", detail: str = "", session: bool = False, running: bool = False) -> None:
        title, body, primary_text, primary_color, primary_command, primary_enabled = self.selected_action_plan(profile, session, running, detail)
        self.next_title.configure(text=title, fg=GREEN if key == "running" else (RED if key == "stopped" else TEXT))
        self.next_detail.configure(text=body)
        self.configure_button(self.primary_button, primary_text, primary_color, primary_command, primary_enabled)

        has_profile = bool(profile)
        configured = bool(profile and profile_configured(profile))
        first_use = bool(profile and profile_is_starter(profile) and not self.configured_profiles())
        if first_use or not profile:
            if self.actions.winfo_manager():
                self.actions.pack_forget()
        elif not self.actions.winfo_manager():
            self.actions.pack(fill=tk.X, before=self.info)
        paused = bool(profile and self.state_for(profile["slug"]).get("paused"))
        self.configure_button(self.edit_button, enabled=has_profile)
        self.configure_button(self.qr_button, enabled=configured)
        self.configure_button(self.sync_button, enabled=configured and session, color=GREEN)
        self.configure_button(self.pause_button, "Retomar" if paused else "Pausar", GREEN if paused else RED, self.toggle_pause_selected, configured and (session or running or paused))
        self.configure_button(self.folder_button, enabled=has_profile)
        self.configure_button(self.copy_button, enabled=has_profile)
        self.configure_button(self.remove_button, enabled=has_profile and not first_use)

    def open_base_setup(self, first_time: bool = False, after=None) -> None:
        if self.base_setup_window and self.base_setup_window.winfo_exists():
            self.base_setup_window.lift()
            self.base_setup_window.focus_force()
            return

        win = tk.Toplevel(self.root)
        self.base_setup_window = win
        win.withdraw()
        apply_window_icon(win)
        win.title("Primeira configuracao" if first_time else "Pasta geral da base")
        win.configure(bg=BG)
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", win.destroy)

        frame = tk.Frame(win, bg=BG, padx=18, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)
        title = "Escolha onde salvar as bases" if first_time else "Pasta geral da base"
        tk.Label(frame, text=title, bg=BG, fg=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        tk.Label(
            frame,
            text="Esta pasta vale para o sistema inteiro. Dentro dela o painel organiza tudo por projeto e, dentro de cada projeto, por perfil/numero.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=560,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(6, 14))

        path_var = tk.StringVar(value=str(PROFILES_DIR))
        row = tk.Frame(frame, bg=BG)
        row.pack(fill=tk.X)
        entry = tk.Entry(row, textvariable=path_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def pick() -> None:
            chosen = filedialog.askdirectory(parent=win, title="Escolha a pasta geral da base", initialdir=str(PROFILES_DIR))
            if chosen:
                path_var.set(chosen)

        self._button(row, "Escolher", BLUE, pick, width=10).pack(side=tk.RIGHT, padx=(8, 0))

        preview = tk.Label(frame, text="", bg=BG, fg=MUTED, font=("Segoe UI", 8), justify=tk.LEFT, wraplength=560)
        preview.pack(anchor="w", pady=(10, 0))

        def refresh_preview(*_args) -> None:
            base = Path(path_var.get().strip() or str(PROFILES_DIR))
            preview.configure(text=f"Estrutura: {base} > projetos > Nome do Projeto > nome-do-perfil > whatsapp-bridge > store")

        path_var.trace_add("write", refresh_preview)
        refresh_preview()

        buttons = tk.Frame(frame, bg=BG)
        buttons.pack(fill=tk.X, pady=(18, 0))
        self._button(buttons, "Cancelar", GRAY, win.destroy, width=10).pack(side=tk.RIGHT, padx=4)

        def save() -> None:
            selected = path_var.get().strip()
            if not selected:
                mb.showwarning("Pasta geral", "Escolha uma pasta para salvar as bases.", parent=win)
                return
            if not first_time and self.configured_profiles() and Path(selected) != PROFILES_DIR:
                msg = (
                    "Trocar a pasta geral cria uma nova base a partir de agora.\n\n"
                    "As bases antigas nao sao movidas automaticamente. Use essa opcao quando quiser separar um novo ambiente."
                )
                if not mb.askyesno("Trocar pasta da base", msg, parent=win):
                    return
            if Path(selected) != PROFILES_DIR:
                set_profiles_base_dir(selected)
            else:
                PROFILES_DIR.mkdir(parents=True, exist_ok=True)
                (PROFILES_DIR / "projetos").mkdir(parents=True, exist_ok=True)
                CONFIG["profiles_base_confirmed"] = True
                save_panel_config(CONFIG)
            self.config = ensure_profiles_config()
            self.state = load_state()
            save_profiles_config(self.config)
            self.last_action = f"Pasta geral da base definida: {PROFILES_DIR}"
            win.destroy()
            self.reload_data()
            if after:
                self.root.after(100, after)

        label = "Continuar" if first_time else "Salvar"
        self._button(buttons, label, GREEN, save, width=10).pack(side=tk.RIGHT, padx=4)
        center_child_window(win, self.root, 640, 300)
        win.deiconify()
        win.lift(self.root)
        win.grab_set()
        win.focus_force()

    def ensure_base_folder_confirmed(self) -> None:
        if not mark_base_confirmed_if_existing():
            self.open_base_setup(first_time=True)

    def open_base_folder(self) -> None:
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(str(PROFILES_DIR))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(PROFILES_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(PROFILES_DIR)])
            self.last_action = f"Pasta geral aberta: {PROFILES_DIR}"
        except Exception as exc:
            self.last_action = f"Erro ao abrir pasta geral: {exc}"
        self.refresh()

    def copy_base_folder(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(str(PROFILES_DIR))
        self.root.update()
        self.last_action = f"Caminho da pasta geral copiado: {PROFILES_DIR}"
        self.refresh()

    def open_settings(self) -> None:
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return
        win = tk.Toplevel(self.root)
        self.settings_window = win
        win.withdraw()
        apply_window_icon(win)
        win.title("Configuracoes do WhatsApp MCP")
        win.configure(bg=BG)
        win.transient(self.root)

        frame = tk.Frame(win, bg=BG, padx=18, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="Configuracoes", bg=BG, fg=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        tk.Label(frame, text="Base geral", bg=BG, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(14, 2))
        tk.Label(frame, text=str(PROFILES_DIR), bg=BG, fg=TEXT, font=("Segoe UI", 9), wraplength=520, justify=tk.LEFT).pack(anchor="w")

        grid = tk.Frame(frame, bg=BG)
        grid.pack(fill=tk.X, pady=(14, 0))

        def close_then(action) -> None:
            win.destroy()
            action()

        self._button(grid, "Abrir pasta da base", GRAY, self.open_base_folder, width=24).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=4)
        self._button(grid, "Copiar caminho da base", GRAY, self.copy_base_folder, width=24).grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=4)
        self._button(grid, "Trocar pasta da base", BLUE, lambda: close_then(lambda: self.open_base_setup(first_time=False)), width=24).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=4)
        self._button(grid, "Auto-start", PURPLE, self.toggle_autostart, width=24).grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=4)
        self._button(grid, "Ocultar na bandeja", GRAY, lambda: close_then(self.hide), width=24).grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=4)
        self._button(grid, "Fechar sistema completo", RED, lambda: close_then(self.shutdown_system), width=24).grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=4)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self._button(frame, "Fechar configuracoes", GRAY, win.destroy, width=18).pack(anchor="e", pady=(14, 0))
        center_child_window(win, self.root, 600, 330)
        win.deiconify()
        win.lift(self.root)
        win.focus_force()

    def new_profile(self) -> None:
        if not CONFIG.get("profiles_base_confirmed"):
            self.open_base_setup(first_time=True, after=self.new_profile)
            return
        starter = self.starter_profile()
        if starter:
            self.selected_slug = starter["slug"]
            ProfileDialog(self, starter)
            return
        ProfileDialog(self)

    def edit_selected(self) -> None:
        profile = self.selected_profile()
        if not profile:
            mb.showinfo("Perfis", "Selecione um perfil.")
            return
        ProfileDialog(self, profile)

    def open_qr_for_selected(self) -> None:
        profile = self.selected_profile()
        if not profile:
            mb.showinfo("QR", "Selecione um perfil.")
            return
        if not profile_configured(profile):
            mb.showinfo("Configurar perfil", "Cadastre nome, projeto e descricao antes de abrir QR.")
            return
        state = self.state_for(profile["slug"])
        if self.session_ready(profile, state):
            if profile_running(profile):
                self.last_action = f"{profile.get('name')} ja esta autenticado e ja esta sincronizando."
                mb.showinfo(
                    "QR ja conectado",
                    (
                        f"{profile.get('name')} ja esta autenticado e a bridge deste perfil esta aberta.\n\n"
                        "Nao precisa reconectar QR. Para trocar ou invalidar a sessao, remova este aparelho em Aparelhos conectados no WhatsApp do celular."
                    ),
                )
            else:
                self.last_action = f"{profile.get('name')} ja esta autenticado; sync manual iniciada."
                mb.showinfo(
                    "QR ja conectado",
                    (
                        f"{profile.get('name')} ja esta autenticado.\n\n"
                        "Nao precisa reconectar QR. Vou iniciar uma sincronizacao agora. Para trocar ou invalidar a sessao, remova este aparelho em Aparelhos conectados no WhatsApp do celular."
                    ),
                )
                self.start_sync(profile, manual=True)
            self.refresh()
            return
        state.pop("authenticated_at", None)
        state["initial_sync_started_at"] = None
        state["initial_sync_until"] = None
        state["initial_sync_completed_at"] = None
        state["sync_mode"] = "qr_pending"
        self.save_all()
        if profile_running(profile):
            stop_profile(profile)
            time.sleep(0.5)
        self.open_qr_window(profile)
        self.refresh()

    def open_qr_window(self, profile: dict) -> None:
        slug = profile["slug"]
        if slug in self.qr_windows and self.qr_windows[slug].winfo_exists():
            existing = self.qr_windows[slug]
            existing.deiconify()
            existing.state("normal")
            existing.lift(self.root)
            try:
                existing.focus_force()
            except tk.TclError:
                pass
            return
        ensure_profile_dirs(profile)
        if not BRIDGE_BINARY.exists():
            mb.showerror("QR", f"Bridge nao encontrada: {BRIDGE_BINARY}")
            return

        state = self.state_for(slug)
        state["qr_requested_at"] = now_iso()
        state["paused"] = False
        self.save_all()

        win = tk.Toplevel(self.root)
        win.withdraw()
        apply_window_icon(win)
        self.qr_windows[slug] = win
        display_name = normalize_profile_name(str(profile.get("name", slug)))
        win.title(f"Conectar QR - {display_name}")
        win.configure(bg=BG)
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", win.withdraw)

        frame = tk.Frame(win, bg=BG, padx=16, pady=14)
        frame.pack(fill=tk.BOTH, expand=True)
        title_label = tk.Label(frame, text=f"Conectar {display_name}", bg=BG, fg=TEXT, font=("Segoe UI", 15, "bold"))
        title_label.pack(anchor="w")
        status = tk.Label(frame, text="Abrindo bridge e aguardando QR...", bg=BG, fg=YELLOW, font=("Segoe UI", 10, "bold"))
        status.pack(anchor="w", pady=(4, 6))
        guidance = tk.Label(
            frame,
            text="Escaneie o QR pelo WhatsApp do celular. Depois que autenticar, voce pode ocultar esta janela e continuar usando o painel.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=560,
            justify=tk.LEFT,
        )
        guidance.pack(anchor="w", fill=tk.X, pady=(0, 10))

        qr_area = tk.Frame(frame, bg=BG)
        qr_area.pack(fill=tk.BOTH, expand=True)
        qr_label = tk.Label(qr_area, bg=BG)
        qr_label.pack(pady=(6, 8))
        qr_fallback = tk.Label(
            qr_area,
            text="",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 8),
            wraplength=560,
            justify=tk.LEFT,
        )

        details_visible = {"value": False}
        details_frame = tk.Frame(frame, bg=PANEL_2, padx=8, pady=8)
        tk.Label(details_frame, text="Detalhes tecnicos", bg=PANEL_2, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        qr_text = tk.Text(details_frame, height=3, bg=PANEL_2, fg=TEXT, relief=tk.FLAT, wrap=tk.WORD, font=("Consolas", 8))
        qr_text.pack(fill=tk.X, pady=(4, 8))
        log_box = tk.Text(details_frame, height=7, bg=PANEL_2, fg=TEXT, relief=tk.FLAT, font=("Consolas", 8))
        log_box.pack(fill=tk.BOTH, expand=True)

        buttons = tk.Frame(frame, bg=BG)
        buttons.pack(fill=tk.X, pady=(10, 0))
        def return_to_panel() -> None:
            try:
                win.withdraw()
            except tk.TclError:
                return
            self.show()

        primary_return = self._button(buttons, "Voltar ao painel", GREEN, return_to_panel, width=24)
        primary_return.pack(side=tk.TOP, pady=(0, 12), ipadx=42, ipady=8)
        secondary_buttons = tk.Frame(buttons, bg=BG)
        secondary_buttons.pack(fill=tk.X)
        self._button(secondary_buttons, "Ocultar", GRAY, win.withdraw, width=10).pack(side=tk.LEFT, padx=(0, 6))
        self._button(secondary_buttons, "Cadastrar outro perfil", PURPLE, lambda: (win.withdraw(), self.show(), self.new_profile()), width=20).pack(side=tk.LEFT, padx=6)
        details_button = self._button(buttons, "Detalhes tecnicos", GRAY, None, width=16)
        details_button.pack(in_=secondary_buttons, side=tk.LEFT, padx=6)
        self._button(secondary_buttons, "Pausar sync", RED, lambda: self.stop_qr_profile(profile, win, confirm=True), width=12).pack(side=tk.RIGHT, padx=(6, 0))

        def toggle_details() -> None:
            details_visible["value"] = not details_visible["value"]
            if details_visible["value"]:
                details_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0), before=buttons)
                details_button.configure(text="Ocultar detalhes")
            else:
                details_frame.pack_forget()
                details_button.configure(text="Detalhes tecnicos")

        details_button.configure(command=toggle_details)
        qr_done = {"value": False}
        center_child_window(win, self.root, 660, 660)
        win.deiconify()
        win.lift(self.root)
        win.focus_force()

        def show_authenticated() -> None:
            qr_done["value"] = True
            try:
                qr_label.configure(image="")
                qr_label.image = None
                qr_label.pack_forget()
                qr_fallback.pack_forget()
                details_frame.pack_forget()
                details_button.configure(text="Detalhes tecnicos")
                details_visible["value"] = False
            except tk.TclError:
                pass
            display_name = normalize_profile_name(str(profile.get("name", slug)))
            win.title(f"Sincronizando - {display_name}")
            title_label.configure(text=f"{display_name} conectado")
            status.configure(text="Autenticado. Sync inteligente em andamento.", fg=GREEN)
            until = fmt_dt(state.get("initial_sync_until"))
            if until == "-":
                until = f"no maximo {INITIAL_SYNC_HOURS}h a partir de agora"
            guidance.configure(
                text=(
                    f"Voltando ao painel automaticamente. Este perfil segue sincronizando em background ate estabilizar, com limite maximo em {until}. "
                    "A bridge fecha sozinha quando a ultima mensagem estiver perto do agora e o ritmo de importacao cair por tempo suficiente."
                ),
                fg=GREEN,
            )
            primary_return.configure(text="Voltar ao painel agora", bg=GREEN, font=("Segoe UI", 12, "bold"))
            win.after(QR_AUTH_AUTO_RETURN_MS, return_to_panel)

        def append_line(line: str) -> None:
            clean = strip_ansi(line.rstrip())
            if not clean:
                return
            log_box.insert(tk.END, clean + "\n")
            log_box.see(tk.END)
            detected = detected_phone_from_log_line(clean)
            if detected:
                if apply_detected_profile_number(profile, detected):
                    self.save_all()
                    self.last_action = f"Numero identificado pelo QR: {detected}."
                    self.refresh()
            if "Successfully connected" in clean or "Connected to WhatsApp" in clean:
                state["authenticated_at"] = now_iso()
                if not state.get("initial_sync_started_at"):
                    started = datetime.now()
                    state["initial_sync_started_at"] = started.isoformat(timespec="seconds")
                    state["initial_sync_until"] = (started + timedelta(hours=INITIAL_SYNC_HOURS)).isoformat(timespec="seconds")
                    state["sync_mode"] = "initial_smart"
                    state["baseline_messages"] = cached_db_stats(profile, state).get("messages", 0)
                state["paused"] = False
                self.save_all()
                self.last_action = f"{profile.get('name')} autenticado; sync inteligente iniciando."
                show_authenticated()
                self.refresh()
            elif "Starting REST API server" in clean:
                show_authenticated()
                self.refresh()
            elif "Timeout waiting" in clean or "Failed to connect" in clean:
                status.configure(text=clean, fg=RED)

        def show_qr(data: str) -> None:
            if qr_done["value"]:
                return
            qr_text.configure(state=tk.NORMAL)
            qr_text.delete("1.0", tk.END)
            qr_text.insert(tk.END, data)
            qr_text.configure(state=tk.DISABLED)
            try:
                import qrcode
                from PIL import ImageTk

                img = qrcode.make(data).resize((340, 340))
                photo = ImageTk.PhotoImage(img)
                qr_label.configure(image=photo)
                qr_label.image = photo
                qr_fallback.pack_forget()
                status.configure(text="Escaneie este QR no WhatsApp do celular.", fg=YELLOW)
            except Exception:
                qr_fallback.configure(text="Nao consegui renderizar a imagem do QR. Abra Detalhes tecnicos e copie o codigo para outro leitor.")
                qr_fallback.pack(fill=tk.X, pady=(0, 8))
                status.configure(text="QR recebido, mas a imagem nao renderizou.", fg=YELLOW)

        paths = profile_paths(profile)
        env = os.environ.copy()
        env["WHATSAPP_MCP_PORT"] = str(profile.get("port"))
        proc = subprocess.Popen(
            [str(BRIDGE_BINARY)],
            cwd=str(paths["bridge_dir"]),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        paths["pid_path"].write_text(str(proc.pid), encoding="ascii")
        self.last_action = f"QR aberto no painel para {profile.get('name')}."

        def reader() -> None:
            with open(paths["out_log"], "a", encoding="utf-8", errors="replace") as log:
                if proc.stdout:
                    for line in proc.stdout:
                        log.write(line)
                        log.flush()
                        if line.startswith("QR_CODE_DATA:"):
                            data = line.split(":", 1)[1].strip()
                            self.root.after(0, lambda value=data: show_qr(value))
                        else:
                            self.root.after(0, lambda value=line: append_line(value))
            code = proc.wait()
            self.root.after(0, lambda: status.configure(text=f"Bridge encerrada (codigo {code}).", fg=RED if code else MUTED))

        threading.Thread(target=reader, daemon=True).start()

    def stop_qr_profile(self, profile: dict, win: tk.Toplevel, confirm: bool = True) -> None:
        if confirm and not mb.askyesno(
            "Pausar sync",
            f"Pausar a sincronizacao de {profile.get('name')}?\n\nIsso fecha a bridge deste perfil. Use apenas se nao quiser manter a janela de captura rodando.",
            parent=win,
        ):
            return
        stop_profile(profile)
        state = self.state_for(profile["slug"])
        state["paused"] = True
        state["paused_by_user_at"] = now_iso()
        state["current_sync_started_at"] = None
        self.save_all()
        self.last_action = f"Sync pausada para {profile.get('name')}."
        win.withdraw()
        self.refresh()

    def remove_selected_profile(self) -> None:
        profile = self.selected_profile()
        if not profile:
            mb.showinfo("Excluir perfil", "Selecione um perfil.")
            return
        if profile_is_starter(profile):
            mb.showinfo("Excluir perfil", "Cadastre ou edite o primeiro perfil antes de excluir.")
            return
        self.open_remove_profile_dialog(profile)

    def open_remove_profile_dialog(self, profile: dict) -> None:
        profile = dict(profile)
        paths = profile_paths(profile)
        profile_dir = paths["profile_dir"]
        messages_db = paths["messages_db"]

        win = tk.Toplevel(self.root)
        win.withdraw()
        apply_window_icon(win)
        win.title(f"Excluir perfil - {profile.get('name', profile.get('slug'))}")
        win.configure(bg=BG)
        win.transient(self.root)
        win.grab_set()
        win.protocol("WM_DELETE_WINDOW", win.destroy)

        frame = tk.Frame(win, bg=BG, padx=18, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="Excluir perfil", bg=BG, fg=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        tk.Label(
            frame,
            text=f"{project_name(self.config, profile)} / {profile.get('name')}",
            bg=BG,
            fg=GREEN,
            font=("Segoe UI", 10, "bold"),
            wraplength=560,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(4, 10))
        tk.Label(
            frame,
            text=(
                "Esta acao sempre para a sincronizacao e tira o perfil da lista do painel/MCP. "
                "Opcionalmente, voce tambem pode apagar os bancos, sessao, logs e arquivos locais."
            ),
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=560,
            justify=tk.LEFT,
        ).pack(anchor="w", fill=tk.X, pady=(0, 12))

        summary = tk.Frame(frame, bg=PANEL, padx=12, pady=10)
        summary.pack(fill=tk.X, pady=(0, 10))
        tk.Label(summary, text="O que vai acontecer", bg=PANEL, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(
            summary,
            text=(
                "1. Fechar a bridge deste perfil.\n"
                "2. Excluir o perfil do painel e do MCP.\n"
                "3. Manter os dados locais, a menos que voce marque a opcao abaixo."
            ),
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=530,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(3, 8))

        delete_data = tk.BooleanVar(value=False)
        option_delete = tk.Checkbutton(
            frame,
            text="Apagar tambem os dados locais deste perfil",
            variable=delete_data,
            bg=BG,
            fg=RED,
            selectcolor=PANEL_2,
            activebackground=BG,
            activeforeground=RED,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        option_delete.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            frame,
            text=(
                "Se marcado, apaga definitivamente sessao, mensagens, logs e arquivos baixados. "
                "Antes de apagar, o painel vai pedir que voce digite o nome exato do perfil.\n"
                f"Pasta: {profile_dir}\nDB: {messages_db}"
            ),
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=530,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(0, 12))

        buttons = tk.Frame(frame, bg=BG)
        buttons.pack(fill=tk.X, pady=(4, 0))
        progress = tk.Label(
            frame,
            text="",
            bg=BG,
            fg=YELLOW,
            font=("Segoe UI", 9, "bold"),
            wraplength=560,
            justify=tk.LEFT,
        )
        progress.pack(anchor="w", fill=tk.X, pady=(2, 0))

        cancel_button = self._button(buttons, "Cancelar", GRAY, win.destroy, width=10)
        cancel_button.pack(side=tk.RIGHT, padx=(8, 0))
        delete_button = self._button(
            buttons,
            "Excluir perfil",
            RED,
            lambda: self.confirm_remove_profile(
                profile,
                win,
                delete_data=bool(delete_data.get()),
                progress=progress,
                controls=[cancel_button, delete_button, option_delete],
            ),
            width=14,
        )
        delete_button.pack(side=tk.RIGHT, padx=8)

        center_child_window(win, self.root, 660, 420)
        win.deiconify()
        win.lift(self.root)
        win.focus_force()

    def confirm_remove_profile(
        self,
        profile: dict,
        win: tk.Toplevel,
        delete_data: bool,
        progress: tk.Label | None = None,
        controls: list[tk.Widget] | None = None,
    ) -> None:
        name = profile.get("name") or profile.get("slug")
        paths = profile_paths(profile)
        profile_dir = paths["profile_dir"]
        if delete_data:
            if not path_is_inside(profile_dir, PROFILES_DIR) or profile_dir.resolve(strict=False) == PROFILES_DIR.resolve(strict=False):
                mb.showerror(
                    "Excluir perfil",
                    f"Por seguranca, o painel so apaga pastas dentro da pasta geral do sistema.\n\nPasta do perfil:\n{profile_dir}",
                    parent=win,
                )
                return
            ok = mb.askyesno(
                "Excluir perfil e apagar dados",
                (
                    f"Excluir {name} do painel/MCP e apagar definitivamente todos os dados locais?\n\n"
                    f"Isto remove:\n{profile_dir}\n\n"
                    "Nao tem desfazer. Para preservar o historico, volte e desmarque a opcao de apagar dados locais."
                ),
                parent=win,
            )
            if not ok:
                return
            typed_name = simpledialog.askstring(
                "Confirmar exclusao definitiva",
                (
                    "Para apagar os dados locais, digite exatamente o nome do perfil:\n\n"
                    f"{name}"
                ),
                parent=win,
            )
            if typed_name != name:
                mb.showinfo(
                    "Apagar dados locais",
                    "Exclusao cancelada. O nome digitado nao bate com o nome do perfil.",
                    parent=win,
                )
                return
        else:
            ok = mb.askyesno(
                "Excluir perfil",
                (
                    f"Excluir {name} da lista do painel e do MCP?\n\n"
                    "A sincronizacao sera parada. Os arquivos locais continuam preservados na pasta do perfil."
                ),
                parent=win,
            )
            if not ok:
                return

        if progress:
            wait_message = (
                "Excluindo... fechando a bridge e liberando arquivos locais. Pode levar alguns segundos."
                if delete_data
                else "Excluindo... fechando a bridge deste perfil."
            )
            progress.configure(text=wait_message, fg=YELLOW)
        for control in controls or []:
            try:
                control.configure(state=tk.DISABLED)
            except tk.TclError:
                pass
        try:
            win.configure(cursor="watch")
            self.root.configure(cursor="watch")
            win.update_idletasks()
            self.root.update_idletasks()
        except tk.TclError:
            pass

        try:
            self.remove_profile(profile, delete_data=delete_data)
        except OSError as exc:
            for control in controls or []:
                try:
                    control.configure(state=tk.NORMAL)
                except tk.TclError:
                    pass
            try:
                win.configure(cursor="")
                self.root.configure(cursor="")
            except tk.TclError:
                pass
            if progress:
                progress.configure(text="Nao consegui concluir. Veja o erro abaixo.", fg=RED)
            mb.showerror("Excluir perfil", f"Nao consegui excluir o perfil.\n\n{exc}", parent=win)
            return
        try:
            self.root.configure(cursor="")
        except tk.TclError:
            pass
        win.destroy()
        self.refresh()

    def remove_profile(self, profile: dict, delete_data: bool = False) -> None:
        slug = profile.get("slug")
        if not slug:
            return
        name = profile.get("name") or slug
        paths = profile_paths(profile)
        profile_dir = paths["profile_dir"]

        stop_profile(profile, wait_seconds=3.0 if delete_data else 2.0)
        qr_window = self.qr_windows.pop(slug, None)
        if qr_window and qr_window.winfo_exists():
            try:
                qr_window.withdraw()
            except tk.TclError:
                pass

        deleted_now = not delete_data or not profile_dir.exists()
        if delete_data and profile_dir.exists():
            for attempt in range(2):
                deleted_now, last_error = try_delete_profile_dir(profile_dir, self.state, name)
                if deleted_now:
                    break
                stop_profile(profile, wait_seconds=1.0)
                if attempt == 0:
                    time.sleep(0.4)

        self.config["profiles"] = [item for item in self.config.get("profiles", []) if item.get("slug") != slug]
        self.state.setdefault("profiles", {}).pop(slug, None)
        remaining = self.display_profiles()
        self.selected_slug = remaining[0]["slug"] if remaining else None
        if delete_data and not deleted_now:
            self.last_action = f"Perfil excluido do painel; dados ficaram em limpeza pendente porque o Windows bloqueou o arquivo: {name}."
        else:
            self.last_action = (
                f"Perfil excluido e dados apagados: {name}."
                if delete_data
                else f"Perfil excluido do painel, dados preservados: {name}."
            )
        self.save_all()

    def sync_selected(self) -> None:
        profile = self.selected_profile()
        if not profile:
            mb.showinfo("Sync", "Selecione um perfil.")
            return
        self.start_sync(profile, manual=True)
        self.refresh()

    def resume_selected(self) -> None:
        profile = self.selected_profile()
        if not profile:
            mb.showinfo("Retomar", "Selecione um perfil.")
            return
        state = self.state_for(profile["slug"])
        state["paused"] = False
        state.pop("paused_by_user_at", None)
        if not profile_configured(profile):
            self.last_action = "Preencha os dados do perfil antes de retomar."
        elif self.session_ready(profile, state):
            self.start_sync(profile, manual=True)
        else:
            self.open_qr_for_selected()
        self.save_all()
        self.refresh()

    def sync_all(self) -> None:
        for profile in self.profiles():
            self.start_sync(profile, manual=True, quiet=True)
        self.last_action = "Sync manual solicitada para todos os perfis com sessao."
        self.refresh()

    def pause_selected(self) -> None:
        profile = self.selected_profile()
        if not profile:
            mb.showinfo("Pausar", "Selecione um perfil.")
            return
        if mb.askyesno("Pausar perfil", f"Pausar e fechar a bridge de {profile.get('name')}?"):
            self.pause_profile(profile)
            self.refresh()

    def toggle_pause_selected(self) -> None:
        profile = self.selected_profile()
        if not profile:
            mb.showinfo("Pausar", "Selecione um perfil.")
            return
        state = self.state_for(profile["slug"])
        if state.get("paused"):
            self.resume_selected()
            return
        self.pause_selected()

    def pause_all(self) -> None:
        if mb.askyesno("Pausar todos", "Pausar e fechar todos os perfis?"):
            for profile in self.profiles():
                self.pause_profile(profile, user_requested=True)
            self.last_action = "Todos os perfis foram pausados."
            self.refresh()

    def pause_all_without_confirm(self) -> None:
        for profile in self.profiles():
            self.stop_profile_for_shutdown(profile)
        self.last_action = "Sincronizacoes paradas para fechamento do sistema; serao retomadas no proximo startup."

    def toggle_autostart(self) -> None:
        state, message = autostart_state()
        system_name = "Windows" if IS_WINDOWS else "macOS" if IS_MAC else "sistema"
        if state == "on":
            if not mb.askyesno("Auto-start", f"Desativar inicializacao automatica do painel com o {system_name}?"):
                return
            ok, result = set_autostart_enabled(False)
        else:
            detail = message
            if state == "review":
                detail += "\n\nVou tentar substituir atalhos antigos pelo atalho correto."
            if not mb.askyesno("Auto-start", f"Ativar inicializacao automatica do painel com o {system_name}?\n\n{detail}"):
                return
            ok, result = set_autostart_enabled(True)
        self.last_action = result
        if ok:
            mb.showinfo("Auto-start", result)
        else:
            mb.showwarning("Auto-start", result)
        self.refresh()

    def pause_profile(self, profile: dict, user_requested: bool = True) -> None:
        state = self.state_for(profile["slug"])
        state["paused"] = True
        if user_requested:
            state["paused_by_user_at"] = now_iso()
        state["current_sync_started_at"] = None
        state["next_sync_at"] = None
        stop_profile(profile)
        self.save_all()
        self.last_action = f"Perfil pausado: {profile.get('name')}."

    def stop_profile_for_shutdown(self, profile: dict) -> None:
        state = self.state_for(profile["slug"])
        state["current_sync_started_at"] = None
        stop_profile(profile)

    def start_sync(self, profile: dict, manual: bool = False, quiet: bool = False) -> None:
        if not profile_configured(profile):
            if not quiet:
                mb.showinfo("Configurar perfil", "Cadastre nome e projeto antes de sincronizar.")
            return
        state = self.state_for(profile["slug"])
        if not self.session_ready(profile, state):
            if not quiet:
                mb.showinfo("QR necessario", "Este perfil ainda nao tem sessao. Clique em Conectar QR primeiro.")
            return
        state["paused"] = False
        if not state.get("initial_sync_started_at"):
            started = datetime.now()
            state["initial_sync_started_at"] = started.isoformat(timespec="seconds")
            state["initial_sync_until"] = (started + timedelta(hours=INITIAL_SYNC_HOURS)).isoformat(timespec="seconds")
            state["sync_mode"] = "initial_smart"
        if not state.get("current_sync_started_at"):
            state["current_sync_started_at"] = now_iso()
            state["last_activity_at"] = now_iso()
            state["current_sync_max_until"] = (datetime.now() + timedelta(seconds=SYNC_MAX_SECONDS)).isoformat(timespec="seconds")
            stats = cached_db_stats(profile, state)
            state["baseline_messages"] = stats.get("messages", 0)
            state["last_signature"] = self.signature(stats)
        ok, message = start_profile(profile, visible=False)
        self.last_action = f"{profile.get('name')}: {message}"
        self.save_all()

    def open_selected_folder(self) -> None:
        profile = self.selected_profile()
        if not profile:
            return
        profile_dir = profile_paths(profile)["profile_dir"]
        folder = profile_dir.parent
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
            self.last_action = f"Pasta do projeto aberta: {folder}"
        except Exception as exc:
            self.last_action = f"Erro ao abrir pasta: {exc}"
        self.refresh()

    def copy_selected_db(self) -> None:
        profile = self.selected_profile()
        if not profile:
            return
        db = profile_paths(profile)["messages_db"]
        self.root.clipboard_clear()
        self.root.clipboard_append(str(db))
        self.root.update()
        self.last_action = f"Caminho da base copiado: {db}"
        self.refresh()

    def safe_db_stats(self, profile: dict) -> dict:
        try:
            return db_stats(profile)
        except Exception as exc:
            return {"exists": False, "messages": 0, "chats": 0, "last": None, "error": str(exc)}

    def session_device_row(self, profile: dict):
        session_db = profile_paths(profile)["session_db"]
        if not session_db.exists():
            return None
        try:
            with sqlite3.connect(f"file:{session_db}?mode=ro", uri=True, timeout=0.5) as conn:
                row = conn.execute("select jid, push_name, business_name from whatsmeow_device limit 1").fetchone()
        except sqlite3.Error:
            return None
        if not row or not row[0]:
            return None
        return row

    def sync_profile_identity_from_session(self, profile: dict) -> bool:
        row = self.session_device_row(profile)
        if not row:
            return False
        detected = jid_to_phone(str(row[0]))
        if not detected:
            return False
        changed = False
        if apply_detected_profile_number(profile, detected):
            changed = True
        if row[1] and not profile.get("whatsapp_push_name"):
            profile["whatsapp_push_name"] = row[1]
            changed = True
        if row[2] and not profile.get("whatsapp_business_name"):
            profile["whatsapp_business_name"] = row[2]
            changed = True
        if changed:
            profile["updated_at"] = now_iso()
            save_profiles_config(self.config)
        return True

    def session_ready(self, profile: dict, state: dict) -> bool:
        if not profile_configured(profile):
            return False
        if state.get("authenticated_at"):
            session_db = profile_paths(profile)["session_db"]
            if not session_db.exists():
                return False
            missing_identity = not profile.get("number") or not profile.get("whatsapp_push_name")
            current_digits = phone_digits(str(profile.get("number") or ""))
            number_looks_too_long = current_digits.startswith("55") and len(current_digits) > 13
            last_identity_sync = parse_iso(state.get("last_identity_sync_at"))
            should_sync_identity = number_looks_too_long or (
                missing_identity and (
                    not last_identity_sync or (datetime.now() - last_identity_sync).total_seconds() > 600
                )
            )
            if should_sync_identity and self.sync_profile_identity_from_session(profile):
                state["last_identity_sync_at"] = now_iso()
            return True
        if self.sync_profile_identity_from_session(profile):
            state["authenticated_at"] = now_iso()
            state["last_identity_sync_at"] = now_iso()
            return True
        return False

    def signature(self, stats: dict) -> str:
        return f"{stats.get('messages')}|{stats.get('last')}|{stats.get('mtime')}"

    def observe_activity(self, profile: dict, state: dict, stats: dict) -> None:
        messages = int(stats.get("messages") or 0)
        previous_messages = state.get("last_observed_messages")
        previous_at = parse_iso(state.get("last_observed_at"))
        rate = 0.0
        if previous_messages is not None and previous_at:
            elapsed = max(1.0, (datetime.now() - previous_at).total_seconds())
            delta = max(0, messages - int(previous_messages or 0))
            rate = delta * 60.0 / elapsed
        previous_ema = state.get("message_rate_ema")
        ema = rate if previous_ema is None else (float(previous_ema) * 0.65 + rate * 0.35)
        state["messages_per_minute"] = round(rate, 2)
        state["message_rate_ema"] = round(ema, 2)
        state["last_observed_messages"] = messages
        state["last_observed_at"] = now_iso()
        lag = message_lag_seconds(stats.get("last"))
        if lag is not None:
            state["latest_message_lag_seconds"] = int(lag)
        sig = self.signature(stats)
        if sig != state.get("last_signature"):
            state["last_signature"] = sig
            state["last_activity_at"] = now_iso()
        if stats.get("messages") is not None:
            state["current_messages"] = messages
        if stats.get("chats") is not None:
            state["current_chats"] = int(stats.get("chats") or 0)
        if stats.get("last"):
            state["current_last_message"] = stats.get("last")
        if stats.get("mtime"):
            state["current_db_mtime"] = stats.get("mtime")

    def schedule_next(self, state: dict) -> None:
        delay = random.randint(RANDOM_SYNC_MIN_SECONDS, RANDOM_SYNC_MAX_SECONDS)
        state["next_sync_at"] = (datetime.now() + timedelta(seconds=delay)).isoformat(timespec="seconds")

    def tick_profile(self, profile: dict) -> None:
        if not profile_configured(profile):
            return
        ensure_profile_dirs(profile)
        state = self.state_for(profile["slug"])
        if state.get("paused"):
            return
        session_exists = self.session_ready(profile, state)
        running = profile_running(profile)

        if not session_exists:
            return

        now = datetime.now()
        initial_until = parse_iso(state.get("initial_sync_until"))
        initial_done = bool(state.get("initial_sync_completed_at"))
        next_sync = parse_iso(state.get("next_sync_at"))
        initial_pending = bool(initial_until and not initial_done)
        sync_due = bool(next_sync and now >= next_sync)
        needs_fresh_stats = running or initial_pending or not state.get("initial_sync_started_at") or sync_due
        stats = self.safe_db_stats(profile) if needs_fresh_stats else cached_db_stats(profile, state)
        if needs_fresh_stats:
            self.observe_activity(profile, state, stats)

        if not state.get("initial_sync_started_at"):
            state["initial_sync_started_at"] = now.isoformat(timespec="seconds")
            state["initial_sync_until"] = (now + timedelta(hours=INITIAL_SYNC_HOURS)).isoformat(timespec="seconds")
            state["sync_mode"] = "initial_smart"
            state["baseline_messages"] = stats.get("messages", 0)
            state["last_action"] = "Primeira sync inteligente iniciada automaticamente."
            initial_until = parse_iso(state.get("initial_sync_until"))
            initial_done = False

        if initial_until and not initial_done:
            if now < initial_until:
                if not running:
                    start_profile(profile, visible=False)
                state["next_sync_at"] = None
                state["sync_mode"] = "initial_smart"
                started = parse_iso(state.get("initial_sync_started_at")) or now
                last_activity = parse_iso(state.get("last_activity_at")) or started
                elapsed = (now - started).total_seconds()
                idle = (now - last_activity).total_seconds()
                state["initial_idle_seconds"] = int(max(0, idle))
                state["initial_elapsed_seconds"] = int(max(0, elapsed))
                lag = state.get("latest_message_lag_seconds")
                rate = max(float(state.get("message_rate_ema") or 0), float(state.get("messages_per_minute") or 0))
                caught_up_by_time = lag is not None and float(lag) <= INITIAL_SYNC_LIVE_LAG_SECONDS
                live_rate_ok = rate <= INITIAL_SYNC_LIVE_RATE_PER_MINUTE
                empty_quiet = int(stats.get("messages") or 0) == 0 and idle >= INITIAL_SYNC_IDLE_SECONDS
                live_like = (caught_up_by_time and live_rate_ok) or empty_quiet
                state["initial_close_candidate"] = bool(live_like)
                state["initial_close_candidate_reason"] = (
                    "conta sem mensagens"
                    if empty_quiet
                    else f"lag={human_duration(lag) if lag is not None else '-'}; ritmo={rate:.1f}/min; limite={INITIAL_SYNC_LIVE_RATE_PER_MINUTE:.1f}/min"
                )
                if live_like:
                    state.setdefault("initial_live_like_since", now.isoformat(timespec="seconds"))
                else:
                    state.pop("initial_live_like_since", None)
                live_like_since = parse_iso(state.get("initial_live_like_since"))
                live_like_for = (now - live_like_since).total_seconds() if live_like_since else 0
                state["initial_live_like_seconds"] = int(max(0, live_like_for))
                min_elapsed = elapsed >= INITIAL_SYNC_MIN_SECONDS
                stable_enough = bool(idle >= INITIAL_SYNC_IDLE_SECONDS and live_like_for >= INITIAL_SYNC_STABLE_SECONDS)
                safely_caught_up = bool(live_like and min_elapsed and stable_enough)
                state["initial_min_elapsed"] = bool(min_elapsed)
                state["initial_stable_enough"] = bool(stable_enough)
                state["initial_safely_caught_up"] = bool(safely_caught_up)
                if safely_caught_up:
                    state["initial_sync_completed_at"] = now.isoformat(timespec="seconds")
                    state["last_sync_at"] = now.isoformat(timespec="seconds")
                    state["current_sync_started_at"] = None
                    state["sync_mode"] = "random"
                    reason = "sem mensagens na conta" if empty_quiet else (
                        f"ultima msg a {human_duration(lag)} do agora; ritmo {rate:.1f}/min; sem crescimento por {human_duration(idle)}; estavel por {human_duration(live_like_for)}"
                    )
                    state["initial_sync_completed_reason"] = reason
                    stop_profile(profile)
                    self.schedule_next(state)
                return
            state["initial_sync_completed_at"] = now.isoformat(timespec="seconds")
            state["last_sync_at"] = now.isoformat(timespec="seconds")
            state["current_sync_started_at"] = None
            state["sync_mode"] = "random"
            state["initial_sync_completed_reason"] = f"limite maximo de {INITIAL_SYNC_HOURS}h atingido"
            stop_profile(profile)
            self.schedule_next(state)
            return

        if running:
            if not state.get("current_sync_started_at"):
                state["current_sync_started_at"] = now.isoformat(timespec="seconds")
                state["current_sync_max_until"] = (now + timedelta(seconds=SYNC_MAX_SECONDS)).isoformat(timespec="seconds")
                state["last_activity_at"] = now.isoformat(timespec="seconds")
                state["baseline_messages"] = stats.get("messages", 0)
            started = parse_iso(state.get("current_sync_started_at")) or now
            max_until = parse_iso(state.get("current_sync_max_until")) or now
            last_activity = parse_iso(state.get("last_activity_at")) or now
            min_ok = (now - started).total_seconds() >= SYNC_MIN_SECONDS
            idle_ok = (now - last_activity).total_seconds() >= SYNC_IDLE_SECONDS
            if now >= max_until or (min_ok and idle_ok):
                stop_profile(profile)
                state["last_sync_at"] = now.isoformat(timespec="seconds")
                state["current_sync_started_at"] = None
                state["current_sync_max_until"] = None
                state["last_sync_completed_reason"] = "limite da janela atingido" if now >= max_until else f"sem crescimento por {human_duration((now - last_activity).total_seconds())}"
                self.schedule_next(state)
            return

        state["current_sync_started_at"] = None
        if not next_sync:
            self.schedule_next(state)
        elif now >= next_sync:
            self.start_sync(profile, manual=False, quiet=True)

    def tick(self) -> None:
        action_log("tick-start")
        self.cleanup_pending_deletes()
        for profile in self.profiles():
            try:
                self.tick_profile(profile)
            except Exception as exc:
                self.state_for(profile["slug"])["last_error"] = str(exc)
        self.save_all()
        self.refresh()
        action_log("tick-end")
        self.root.after(POLL_MS, self.tick)

    def profile_status(self, profile: dict) -> tuple[str, str, str]:
        paths = profile_paths(profile)
        state = self.state_for(profile["slug"])
        if not profile_configured(profile):
            return "Configurar perfil", "waiting", "Cadastre nome e projeto antes de QR/sync"
        running = profile_running(profile)
        session = self.session_ready(profile, state)
        if state.get("paused"):
            return "Pausado", "stopped", "Perfil pausado pelo usuario"
        if not session:
            return "Aguardando QR", "waiting", "Clique Conectar QR para este perfil"
        initial_until = parse_iso(state.get("initial_sync_until"))
        if initial_until and not state.get("initial_sync_completed_at"):
            idle = human_duration(state.get("initial_idle_seconds", 0))
            elapsed = human_duration(state.get("initial_elapsed_seconds", 0))
            max_remain = human_duration((initial_until - datetime.now()).total_seconds())
            lag_value = state.get("latest_message_lag_seconds")
            lag = human_duration(lag_value) if lag_value is not None else "-"
            rate = float(state.get("message_rate_ema") or 0)
            live_for = human_duration(state.get("initial_live_like_seconds", 0))
            return (
                "Primeira sync inteligente",
                "running" if running else "waiting",
                f"{elapsed}; ultima msg a {lag}; ritmo {rate:.1f}/min; live {live_for}; max {max_remain}",
            )
        if running:
            state_running = self.state_for(profile["slug"])
            last_activity = parse_iso(state_running.get("last_activity_at")) or datetime.now()
            idle = human_duration((datetime.now() - last_activity).total_seconds())
            return "Sincronizando random", "running", f"janela ativa; sem crescimento ha {idle}"
        next_sync = fmt_dt(state.get("next_sync_at"))
        return "Aguardando random", "waiting", f"proxima sync: {next_sync}"

    def aggregate_status(self) -> tuple[str, str]:
        profiles = self.configured_profiles()
        if not profiles:
            return "waiting", "Primeiro uso"
        statuses = [self.profile_status(p)[1] for p in profiles]
        if "running" in statuses:
            return "running", "Sincronizando"
        if all(status == "stopped" for status in statuses):
            return "stopped", "Pausado"
        return "waiting", "Aguardando"

    def set_info_rows(self, rows: list[tuple[str, str, str | None]]) -> None:
        self.info.configure(state=tk.NORMAL)
        self.info.delete("1.0", tk.END)
        for key, value, tag in rows:
            self.info.insert(tk.END, f"{key}: ", ("key",))
            self.info.insert(tk.END, value, (tag,) if tag else ())
            self.info.insert(tk.END, "\n")
        self.info.configure(state=tk.DISABLED)

    def refresh(self) -> None:
        if self.refreshing:
            return
        self.refreshing = True
        try:
            self.root.attributes("-topmost", False)
        except tk.TclError:
            pass
        for item in self.tree.get_children():
            self.tree.delete(item)
        display_profiles = self.display_profiles()
        configured_profiles = self.configured_profiles()
        if display_profiles:
            if self.empty_state.winfo_manager():
                self.empty_state.pack_forget()
            if not self.tree.winfo_manager():
                self.tree.pack(fill=tk.BOTH, expand=True)
        else:
            if self.tree.winfo_manager():
                self.tree.pack_forget()
            if not self.empty_state.winfo_manager():
                self.empty_state.pack(fill=tk.BOTH, expand=True)
        self.add_button.configure(text="Adicionar outro perfil" if configured_profiles else "Cadastrar primeiro perfil")
        self.configure_button(self.sync_all_button, enabled=bool(configured_profiles))
        self.configure_button(self.pause_all_button, enabled=bool(configured_profiles))
        if hasattr(self, "empty_base_label"):
            self.empty_base_label.configure(text=f"Pasta geral atual: {PROFILES_DIR}")

        used_projects = {p.get("project_slug") or p.get("project") for p in configured_profiles}
        summary = {"profiles": len(configured_profiles), "projects": len([p for p in used_projects if p]), "running": 0, "waiting": 0, "paused": 0, "messages": 0}
        for profile in display_profiles:
            configured = profile_configured(profile)
            if configured:
                ensure_profile_dirs(profile)
            state = self.state_for(profile["slug"])
            stats = cached_db_stats(profile, state) if configured else empty_db_stats()
            status, key, detail = self.profile_status(profile)
            summary["messages"] += int(stats.get("messages") or 0)
            if key == "running":
                summary["running"] += 1
            elif key == "stopped":
                summary["paused"] += 1
            else:
                summary["waiting"] += 1
            next_text = detail
            if key == "waiting" and state.get("next_sync_at"):
                next_text = fmt_dt(state.get("next_sync_at"))
            self.tree.insert(
                "",
                tk.END,
                iid=profile["slug"],
                values=(
                    project_name(self.config, profile),
                    profile.get("name", profile["slug"]),
                    profile.get("number") or "via QR",
                    status,
                    stats.get("messages", 0),
                    stats.get("last") or "-",
                    next_text,
                ),
            )
        if self.selected_slug and self.selected_slug in self.tree.get_children():
            self.tree.selection_set(self.selected_slug)
        for key, value in summary.items():
            if key in self.summary_labels:
                self.summary_labels[key].configure(text=f"{value:,}".replace(",", "."))

        agg_key, agg_label = self.aggregate_status()
        self.status.configure(text=agg_label, fg=GREEN if agg_key == "running" else (RED if agg_key == "stopped" else YELLOW))
        self.set_tray(agg_key, agg_label)
        auto_key, auto_message = autostart_state()
        if hasattr(self, "autostart_button"):
            if auto_key == "on":
                self.autostart_button.configure(text="Auto-start: ON", bg=GREEN)
            elif auto_key == "off":
                self.autostart_button.configure(text="Auto-start: OFF", bg=GRAY)
            else:
                self.autostart_button.configure(text="Auto-start: revisar", bg=YELLOW)

        profile = self.selected_profile()
        if not profile:
            self.update_selected_controls(None)
            self.set_info_rows([
                ("Perfis", "nenhum perfil cadastrado" if not self.config.get("profiles") else "selecione um perfil", "warn"),
                ("Primeiro uso", "cadastre o perfil e depois Conectar QR", "muted"),
                ("Pasta geral", str(PROFILES_DIR), "muted"),
                ("Auto-start", auto_message, "good" if auto_key == "on" else ("warn" if auto_key == "review" else "muted")),
                ("Ultima acao", self.last_action, "muted"),
            ])
            self.log.delete("1.0", tk.END)
            self.refreshing = False
            return

        paths = profile_paths(profile)
        configured = profile_configured(profile)
        if configured:
            ensure_profile_dirs(profile)
        state = self.state_for(profile["slug"])
        stats = cached_db_stats(profile, state) if configured else empty_db_stats()
        status, key, detail = self.profile_status(profile)
        session = self.session_ready(profile, state) if configured else False
        running = profile_running(profile) if configured else False
        self.update_selected_controls(profile, status, key, detail, session, running)
        if profile_is_starter(profile) and not configured_profiles:
            self.set_info_rows([
                ("Status", "nenhum numero cadastrado ainda", "warn"),
                ("Proximo passo", "Cadastrar primeiro perfil", "good"),
                ("Depois", "Conectar QR e deixar a sync inteligente fechar quando estabilizar", "muted"),
                ("Pasta base", str(PROFILES_DIR), "muted"),
                ("Auto-start", auto_message, "good" if auto_key == "on" else ("warn" if auto_key == "review" else "muted")),
                ("Ultima acao", self.last_action, "muted"),
            ])
            self.log.delete("1.0", tk.END)
            self.log.insert(tk.END, "Nenhum numero cadastrado ainda.")
            self.refreshing = False
            return
        db_line = "base local ainda nao criada"
        if configured:
            db_line = "messages.db ainda nao criado"
        if stats.get("exists"):
            chat_count = stats.get("chats")
            if chat_count is None:
                db_line = f"{stats.get('messages', 0):,} mensagens".replace(",", ".")
            else:
                db_line = f"{stats.get('messages', 0):,} mensagens em {chat_count:,} chats".replace(",", ".")
        initial_until = state.get("initial_sync_until")
        initial_line = "pendente de QR" if not session else "concluida"
        if initial_until and not state.get("initial_sync_completed_at"):
            initial_line = f"{detail}; limite max {fmt_dt(initial_until)}"
        self.set_info_rows([
            ("Perfil", f"{profile.get('name')} [{profile.get('slug')}]", "good"),
            ("Projeto", project_name(self.config, profile), "good"),
            ("Numero", profile.get("number") or "sera identificado pelo QR", "muted"),
            ("Status", status, "good" if key == "running" else ("bad" if key == "stopped" else "warn")),
            ("Sessao WhatsApp", "autenticada" if session else "sem QR/login", "good" if session else "warn"),
            ("Bridge/porta", f"{'rodando' if running else 'fechada'} | porta {profile.get('port')}", "good" if running else "muted"),
            ("Primeira sync", initial_line, "warn" if session and not state.get("initial_sync_completed_at") else "muted"),
            ("Atraso ultima msg", human_duration(state.get("latest_message_lag_seconds")) if state.get("latest_message_lag_seconds") is not None else "-", "muted"),
            ("Ritmo atual", f"{max(float(state.get('message_rate_ema') or 0), float(state.get('messages_per_minute') or 0)):.1f} msgs/min", "muted"),
            ("Candidato a fechar", state.get("initial_close_candidate_reason") or "-", "muted"),
            ("Ultima sync concluida", fmt_dt(state.get("last_sync_at")), "good"),
            ("Proxima sync random", fmt_dt(state.get("next_sync_at")), "warn"),
            ("Ultimo fechamento", state.get("last_sync_completed_reason") or state.get("initial_sync_completed_reason") or "-", "muted"),
            ("Base local", db_line, "good" if stats.get("exists") else "warn"),
            ("Arquivo mensagens", str(paths["messages_db"]), "muted"),
            ("Pasta do perfil", str(paths["profile_dir"]), "muted"),
            ("Auto-start", auto_message, "good" if auto_key == "on" else ("warn" if auto_key == "review" else "muted")),
            ("Ultima acao", self.last_action, "muted"),
        ])
        self.log.delete("1.0", tk.END)
        if configured:
            self.log.insert(tk.END, "\n".join(read_profile_log(profile)))
        else:
            self.log.insert(tk.END, "Configure o perfil para iniciar QR, sincronizacao e logs.")
        self.refreshing = False

    def hide(self) -> None:
        action_log("hide")
        self.root.withdraw()

    def shutdown_system(self, confirm: bool = True) -> None:
        if self.shutting_down:
            return
        if confirm and not mb.askyesno("Fechar sistema", "Fechar todo o sistema WhatsApp MCP?\n\nIsso vai parar as sincronizacoes, fechar bridges, bandeja e painel."):
            return
        self.shutting_down = True
        action_log("shutdown-start")
        try:
            self.pause_all_without_confirm()
            self.save_all()
        except Exception as exc:
            action_log(f"shutdown-pause-error {exc}")
        self.root.after(100, self.quit)

    def force_show_window(self, source: str) -> None:
        if os.name != "nt" or not self.root_hwnd:
            return
        try:
            action_log(f"force-show-start source={source} hwnd={self.root_hwnd}")
            user32 = ctypes.windll.user32
            hwnd = ctypes.c_void_p(self.root_hwnd)
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.ShowWindow(hwnd, 5)  # SW_SHOW
            action_log(f"force-show-end source={source} hwnd={self.root_hwnd}")
        except Exception as exc:
            action_log(f"force-show-error source={source} error={exc}")

    def show(self) -> None:
        action_log("show-start")
        self.root.deiconify()
        self.root.state("normal")
        activate_macos_app()
        try:
            self.root.attributes("-topmost", True)
        except tk.TclError:
            pass
        self.root.lift()
        self.force_show_window("show")
        try:
            self.root.focus_force()
        except tk.TclError:
            pass
        try:
            self.root.after(500, lambda: self.root.attributes("-topmost", False))
        except tk.TclError:
            pass
        if IS_MAC:
            self.root.after(100, activate_macos_app)
            self.root.after(150, self.root.lift)
        self.root.after(300, self.ensure_base_folder_confirmed)
        action_log(f"show-end state={self.root.state()}")

    def quit(self) -> None:
        action_log("quit-start")
        try:
            for profile in self.profiles():
                stop_profile(profile)
        except Exception as exc:
            action_log(f"quit-stop-profiles-error {exc}")
        tray_proc = self.tray_process
        self.tray_process = None
        if tray_proc and tray_proc.poll() is None:
            try:
                tray_proc.terminate()
                tray_proc.wait(timeout=2)
            except Exception:
                try:
                    tray_proc.kill()
                except Exception:
                    pass
        if self.control_server:
            try:
                self.control_server.shutdown()
                self.control_server.server_close()
            except Exception:
                pass
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
        action_log("quit-end")

    def run(self) -> None:
        action_log("mainloop-start")
        self.root.mainloop()
        action_log("mainloop-end")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimized", action="store_true")
    args = parser.parse_args()
    ProfilesApp(minimized=args.minimized).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
