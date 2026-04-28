from __future__ import annotations

import argparse
from pathlib import Path
import winreg


def default_panel_dir() -> Path:
    return Path.home() / "Documents" / "WhatsApp MCP Panel"


def resolve_pythonw(panel_dir: Path) -> Path:
    venv = panel_dir / ".venv-user"
    if not venv.exists():
        venv = panel_dir / ".venv"
    pyvenv = venv / "pyvenv.cfg"
    if pyvenv.exists():
        for line in pyvenv.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            if line.lower().startswith("home"):
                home = Path(line.split("=", 1)[1].strip())
                candidate = home / "pythonw.exe"
                if candidate.exists() and "CodexSandboxOffline" not in str(candidate):
                    return candidate
    candidate = venv / "Scripts" / "pythonw.exe"
    if candidate.exists():
        return candidate
    fallback = Path("C:/Python313/pythonw.exe")
    if fallback.exists():
        return fallback
    raise FileNotFoundError("pythonw.exe do painel nao encontrado")


def create_shortcut(shell, path: Path, target: Path, args: str, workdir: Path, icon: Path) -> None:
    shortcut = shell.CreateShortcut(str(path))
    shortcut.TargetPath = str(target)
    shortcut.Arguments = args
    shortcut.WorkingDirectory = str(workdir)
    shortcut.Description = "WhatsApp MCP local panel"
    if icon.exists():
        shortcut.IconLocation = str(icon)
    shortcut.WindowStyle = 7
    shortcut.Save()


def set_registry_autostart(target: Path, launcher: Path) -> None:
    command = f'"{target}" "{launcher}" --minimized'
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(key, "WhatsApp MCP Tray", 0, winreg.REG_SZ, command)
    print("Registry Run: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\WhatsApp MCP Tray")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-dir", default=str(default_panel_dir()))
    parser.add_argument("--startup-only", action="store_true")
    parser.add_argument("--startup-shortcut", action="store_true")
    parser.add_argument("--desktop-only", action="store_true")
    parser.add_argument("--registry-only", action="store_true")
    args = parser.parse_args()

    panel_dir = Path(args.panel_dir)
    launcher = panel_dir / "launch_panel.py"
    icon = panel_dir / "whatsapp-mcp-icon.ico"
    if not launcher.exists():
        raise FileNotFoundError(f"Launcher nao encontrado: {launcher}")

    pythonw = resolve_pythonw(panel_dir)

    if args.registry_only:
        set_registry_autostart(pythonw, launcher)
        print(f"Target: {pythonw}")
        return 0

    import win32com.client

    shell = win32com.client.Dispatch("WScript.Shell")
    desktop = Path(shell.SpecialFolders("Desktop"))
    startup = Path(shell.SpecialFolders("Startup"))
    desktop_shortcut = desktop / "WhatsApp MCP Tray.lnk"
    startup_shortcut = startup / "WhatsApp MCP Tray.lnk"

    if args.startup_only:
        create_shortcut(shell, startup_shortcut, pythonw, f'"{launcher}" --minimized', panel_dir, icon)
        print(f"Startup: {startup_shortcut}")
        print(f"Target: {pythonw}")
        return 0

    if not args.desktop_only:
        create_shortcut(shell, desktop_shortcut, pythonw, f'"{launcher}"', panel_dir, icon)
        print(f"Desktop: {desktop_shortcut}")

    if not args.desktop_only:
        set_registry_autostart(pythonw, launcher)

    if args.startup_shortcut:
        create_shortcut(shell, startup_shortcut, pythonw, f'"{launcher}" --minimized', panel_dir, icon)
        print(f"Startup: {startup_shortcut}")

    print(f"Target: {pythonw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
