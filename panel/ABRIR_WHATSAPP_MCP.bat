@echo off
setlocal

set "PANEL_DIR=%~dp0"
set "PYTHONW=%PANEL_DIR%.venv\Scripts\pythonw.exe"
set "LAUNCHER=%PANEL_DIR%launch_panel.py"

if not exist "%PYTHONW%" exit /b 1
if not exist "%LAUNCHER%" exit /b 1

start "" "%PYTHONW%" "%LAUNCHER%" %*
exit /b 0
