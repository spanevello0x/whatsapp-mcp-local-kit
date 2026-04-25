param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp",
  [string]$PanelDir = "$env:USERPROFILE\Documents\WhatsApp MCP Panel"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$panelSource = Join-Path $repoRoot "panel\whatsapp_mcp_panel.py"
$launcherSource = Join-Path $repoRoot "panel\launch_panel.py"
$legacyBatchSource = Join-Path $repoRoot "panel\ABRIR_WHATSAPP_MCP.bat"
$iconGenerator = Join-Path $repoRoot "scripts\generate-icons.py"
$startup = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$desktop = [Environment]::GetFolderPath("Desktop")

New-Item -ItemType Directory -Path $PanelDir -Force | Out-Null
Copy-Item -LiteralPath $panelSource -Destination (Join-Path $PanelDir "whatsapp_mcp_panel.py") -Force
Copy-Item -LiteralPath $launcherSource -Destination (Join-Path $PanelDir "launch_panel.py") -Force
if (Test-Path $legacyBatchSource) {
  try {
    Copy-Item -LiteralPath $legacyBatchSource -Destination (Join-Path $PanelDir "ABRIR_WHATSAPP_MCP.bat") -Force
  } catch {
    Write-Warning "Launcher legado .bat nao atualizado. O Windows/antivirus bloqueou escrita: $($_.Exception.Message)"
  }
}

$config = @{
  bridge_root = $BridgeRoot
  sync_min_minutes = 5
  sync_idle_minutes = 3
  sync_max_minutes = 25
  sync_extend_minutes = 10
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

if (Test-Path $iconGenerator) {
  & $venvPython $iconGenerator --out-dir $PanelDir
}

$scriptPath = Join-Path $PanelDir "whatsapp_mcp_panel.py"
$launcherPath = Join-Path $PanelDir "launch_panel.py"
$shortcutPythonw = $venvPythonw
$pyvenvCfg = Join-Path $venv "pyvenv.cfg"
if (Test-Path $pyvenvCfg) {
  $homeLine = Get-Content -LiteralPath $pyvenvCfg | Where-Object { $_ -match '^home\s*=' } | Select-Object -First 1
  if ($homeLine) {
    $pythonHome = ($homeLine -replace '^home\s*=\s*', '').Trim()
    $basePythonw = Join-Path $pythonHome "pythonw.exe"
    if (Test-Path $basePythonw) {
      $shortcutPythonw = $basePythonw
    }
  }
}
$iconPath = Join-Path $PanelDir "whatsapp-mcp-icon.ico"
if (-not (Test-Path $iconPath)) {
  $iconPath = "$env:SystemRoot\System32\shell32.dll,220"
}
$wsh = New-Object -ComObject WScript.Shell

function New-PanelShortcut {
  param(
    [string]$Path,
    [string]$Arguments,
    [string]$Description
  )
  $shortcut = $wsh.CreateShortcut($Path)
  $shortcut.TargetPath = $shortcutPythonw
  $shortcut.Arguments = $Arguments
  $shortcut.WorkingDirectory = $PanelDir
  $shortcut.Description = $Description
  $shortcut.IconLocation = $iconPath
  $shortcut.WindowStyle = 7
  $shortcut.Save()
}

$desktopShortcutPath = Join-Path $desktop "WhatsApp MCP Tray.lnk"
if (Test-Path $desktopShortcutPath) { Remove-Item -LiteralPath $desktopShortcutPath -Force }
New-PanelShortcut -Path $desktopShortcutPath -Arguments ('"' + $launcherPath + '"') -Description "WhatsApp MCP local panel"

New-Item -ItemType Directory -Path $startup -Force | Out-Null
$startupShortcutPath = Join-Path $startup "WhatsApp MCP Tray.lnk"
$startupTempShortcutPath = Join-Path $PanelDir "WhatsApp MCP Tray Startup.lnk"
$autoStartCreated = $false
try {
  if (Test-Path $startupTempShortcutPath) { Remove-Item -LiteralPath $startupTempShortcutPath -Force }
  New-PanelShortcut -Path $startupTempShortcutPath -Arguments ('"' + $launcherPath + '" --minimized') -Description "WhatsApp MCP local panel minimized"
  Copy-Item -LiteralPath $startupTempShortcutPath -Destination $startupShortcutPath -Force
  $autoStartCreated = Test-Path $startupShortcutPath
} catch {
  Write-Warning "Auto-start nao criado. O Windows/antivirus bloqueou escrita em Startup: $($_.Exception.Message)"
  Write-Warning "Crie manualmente um atalho para $launcherPath com argumento --minimized em: $startup"
}

Write-Host "Painel instalado em: $PanelDir"
Write-Host "Icone criado: $iconPath"
Write-Host "Atalho criado: WhatsApp MCP Tray.lnk"
if ($autoStartCreated) {
  Write-Host "Auto-start criado: WhatsApp MCP Tray.lnk"
} else {
  Write-Host "Auto-start pendente: ver aviso acima"
}
