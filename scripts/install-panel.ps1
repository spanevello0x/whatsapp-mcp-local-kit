param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp",
  [string]$PanelDir = "$env:USERPROFILE\Documents\WhatsApp MCP Panel"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$panelSource = Join-Path $repoRoot "panel\whatsapp_mcp_panel.py"
$startup = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$desktop = [Environment]::GetFolderPath("Desktop")

New-Item -ItemType Directory -Path $PanelDir -Force | Out-Null
Copy-Item -LiteralPath $panelSource -Destination (Join-Path $PanelDir "whatsapp_mcp_panel.py") -Force

$config = @{
  bridge_root = $BridgeRoot
  sync_window_minutes = 8
  random_sync_min_minutes = 10
  random_sync_max_minutes = 50
} | ConvertTo-Json -Depth 3
$config | Set-Content -LiteralPath (Join-Path $PanelDir "panel_config.json") -Encoding UTF8

$uv = "$env:USERPROFILE\.local\bin\uv.exe"
if (-not (Test-Path $uv)) { $uv = "uv" }
$env:UV_CACHE_DIR = Join-Path $PanelDir ".uv-cache"
$venv = Join-Path $PanelDir ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
$venvPythonw = Join-Path $venv "Scripts\pythonw.exe"

if (-not (Test-Path $venvPythonw)) {
  & $uv venv $venv
  & $uv pip install --python $venvPython pystray Pillow "qrcode[pil]"
}

$scriptPath = Join-Path $PanelDir "whatsapp_mcp_panel.py"
$wsh = New-Object -ComObject WScript.Shell

$desktopShortcut = $wsh.CreateShortcut((Join-Path $desktop "WhatsApp MCP Tray.lnk"))
$desktopShortcut.TargetPath = $venvPythonw
$desktopShortcut.Arguments = '"' + $scriptPath + '"'
$desktopShortcut.WorkingDirectory = $PanelDir
$desktopShortcut.Description = "WhatsApp MCP local panel"
$desktopShortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$desktopShortcut.WindowStyle = 7
$desktopShortcut.Save()

New-Item -ItemType Directory -Path $startup -Force | Out-Null
$startupShortcut = $wsh.CreateShortcut((Join-Path $startup "WhatsApp MCP Tray.lnk"))
$startupShortcut.TargetPath = $venvPythonw
$startupShortcut.Arguments = '"' + $scriptPath + '" --minimized'
$startupShortcut.WorkingDirectory = $PanelDir
$startupShortcut.Description = "WhatsApp MCP local panel minimized"
$startupShortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$startupShortcut.WindowStyle = 7
$startupShortcut.Save()

Write-Host "Painel instalado em: $PanelDir"
Write-Host "Atalho criado: WhatsApp MCP Tray.lnk"
Write-Host "Auto-start criado: WhatsApp MCP Tray.lnk"
