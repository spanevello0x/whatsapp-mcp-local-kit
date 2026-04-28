param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp",
  [string]$PanelDir = "$env:USERPROFILE\Documents\WhatsApp MCP Panel",
  [switch]$ProfilesMode,
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$panelSource = Join-Path $repoRoot "panel\whatsapp_mcp_panel.py"
$profilesPanelSource = Join-Path $repoRoot "panel\whatsapp_profiles_panel.py"
$trayAgentSource = Join-Path $repoRoot "panel\tray_agent.py"
$launcherSource = Join-Path $repoRoot "panel\launch_panel.py"
$legacyBatchSource = Join-Path $repoRoot "panel\ABRIR_WHATSAPP_MCP.bat"
$iconGenerator = Join-Path $repoRoot "scripts\generate-icons.py"
$startup = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$desktop = [Environment]::GetFolderPath("Desktop")
$panelConfigPath = Join-Path $PanelDir "panel_config.json"
$existingPanelConfig = $null

New-Item -ItemType Directory -Path $PanelDir -Force | Out-Null
if (Test-Path $panelConfigPath) {
  try {
    $rawPanelConfig = Get-Content -Raw -LiteralPath $panelConfigPath
    if ($rawPanelConfig.Trim()) {
      $existingPanelConfig = $rawPanelConfig | ConvertFrom-Json
    }
  } catch {
    Write-Warning "Nao consegui ler panel_config.json existente; vou recriar mantendo defaults: $($_.Exception.Message)"
  }
}
Copy-Item -LiteralPath $panelSource -Destination (Join-Path $PanelDir "whatsapp_mcp_panel.py") -Force
if (Test-Path $profilesPanelSource) {
  Copy-Item -LiteralPath $profilesPanelSource -Destination (Join-Path $PanelDir "whatsapp_profiles_panel.py") -Force
}
if (Test-Path $trayAgentSource) {
  Copy-Item -LiteralPath $trayAgentSource -Destination (Join-Path $PanelDir "tray_agent.py") -Force
}
Copy-Item -LiteralPath $launcherSource -Destination (Join-Path $PanelDir "launch_panel.py") -Force
if (Test-Path $legacyBatchSource) {
  try {
    Copy-Item -LiteralPath $legacyBatchSource -Destination (Join-Path $PanelDir "ABRIR_WHATSAPP_MCP.bat") -Force
  } catch {
    Write-Warning "Launcher legado .bat nao atualizado. O Windows/antivirus bloqueou escrita: $($_.Exception.Message)"
  }
}

$configMap = [ordered]@{
  bridge_root = $BridgeRoot
  sync_min_minutes = 5
  sync_idle_minutes = 3
  sync_max_minutes = 25
  sync_extend_minutes = 10
  random_sync_min_minutes = 10
  random_sync_max_minutes = 50
  startup_resume_sync = $true
  startup_resume_initial_delay_seconds = 30
  startup_resume_stagger_seconds = 120
  startup_resume_jitter_seconds = 45
  startup_resume_min_interval_minutes = 5
  startup_resume_clear_paused = $true
}
if ($ProfilesMode) {
  $profilesConfigPath = Join-Path $ProfilesDir "profiles.json"
  $baseConfirmed = $false
  if ($existingPanelConfig -and ($existingPanelConfig.PSObject.Properties.Name -contains "profiles_base_confirmed")) {
    $baseConfirmed = [bool]$existingPanelConfig.profiles_base_confirmed
  }
  if (-not $baseConfirmed -and (Test-Path $profilesConfigPath)) {
    try {
      $profilesRaw = Get-Content -Raw -LiteralPath $profilesConfigPath
      if ($profilesRaw.Trim()) {
        $profilesData = $profilesRaw | ConvertFrom-Json
        $baseConfirmed = (@($profilesData.profiles).Count -gt 0) -or (@($profilesData.projects).Count -gt 0)
      }
    } catch {
      $baseConfirmed = $false
    }
  }
  $configMap["profiles_mode"] = $true
  $configMap["profiles_dir"] = $ProfilesDir
  $configMap["profiles_config"] = $profilesConfigPath
  $configMap["initial_sync_hours"] = 24
  $configMap["initial_sync_min_minutes"] = 10
  $configMap["initial_sync_idle_minutes"] = 3
  $configMap["initial_sync_stable_minutes"] = 5
  $configMap["initial_sync_live_lag_minutes"] = 45
  $configMap["initial_sync_live_rate_per_minute"] = 20
  $configMap["control_port"] = 18763
  $configMap["profiles_base_confirmed"] = $baseConfirmed
}
$config = $configMap | ConvertTo-Json -Depth 3
$config | Set-Content -LiteralPath $panelConfigPath -Encoding UTF8

$uv = "$env:USERPROFILE\.local\bin\uv.exe"
if (-not (Test-Path $uv)) { $uv = "uv" }
$env:UV_CACHE_DIR = Join-Path $PanelDir ".uv-cache"
$systemPython = $null
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand -and $pythonCommand.Source -and ($pythonCommand.Source -notlike "*WindowsApps*") -and ($pythonCommand.Source -notlike "*CodexSandboxOffline*")) {
  $systemPython = $pythonCommand.Source
}
$venv = Join-Path $PanelDir ".venv"
if ($systemPython) {
  $venv = Join-Path $PanelDir ".venv-user"
}
$venvPython = Join-Path $venv "Scripts\python.exe"
$venvPythonw = Join-Path $venv "Scripts\pythonw.exe"
$panelPackages = @("pystray", "Pillow", "qrcode[pil]")
if ($env:OS -eq "Windows_NT") {
  $panelPackages += "pywin32"
}

if (-not (Test-Path $venvPythonw)) {
  if ($systemPython) {
    & $systemPython -m venv $venv
  } else {
    & $uv venv $venv
  }
}

$moduleProbe = "import importlib.util,sys; mods=['pystray','PIL','qrcode']; mods += ['win32com'] if sys.platform.startswith('win') else []; missing=[m for m in mods if importlib.util.find_spec(m) is None]; print(' '.join(missing))"
$missingModules = ""
if (Test-Path $venvPython) {
  $missingModules = ((& $venvPython -c $moduleProbe) -join " ").Trim()
}
if ($missingModules) {
  Write-Host "Instalando dependencias faltantes do painel: $missingModules"
  & $uv pip install --python $venvPython @panelPackages
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
    if ((Test-Path $basePythonw) -and ($basePythonw -notlike "*CodexSandboxOffline*")) {
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

function Set-PanelRegistryAutostart {
  $runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
  $command = '"' + $shortcutPythonw + '" "' + $launcherPath + '" --minimized'
  New-Item -Path $runKey -Force | Out-Null
  New-ItemProperty -Path $runKey -Name "WhatsApp MCP Tray" -Value $command -PropertyType String -Force | Out-Null
}

function Remove-PanelRegistryAutostart {
  $runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
  Remove-ItemProperty -Path $runKey -Name "WhatsApp MCP Tray" -ErrorAction SilentlyContinue
}

$desktopShortcutPath = Join-Path $desktop "WhatsApp MCP Tray.lnk"
if (Test-Path $desktopShortcutPath) { Remove-Item -LiteralPath $desktopShortcutPath -Force }
New-PanelShortcut -Path $desktopShortcutPath -Arguments ('"' + $launcherPath + '"') -Description "WhatsApp MCP local panel"

$legacyDesktopShortcutPath = Join-Path $desktop "WhatsApp MCP Painel.lnk"
if (Test-Path $legacyDesktopShortcutPath) {
  try {
    Remove-Item -LiteralPath $legacyDesktopShortcutPath -Force
  } catch {
    Write-Warning "Atalho antigo da area de trabalho nao removido. Vou reapontar para o launcher novo: $($_.Exception.Message)"
    try {
      New-PanelShortcut -Path $legacyDesktopShortcutPath -Arguments ('"' + $launcherPath + '"') -Description "WhatsApp MCP local panel"
    } catch {
      Write-Warning "Atalho antigo continua bloqueado. Use o atalho novo 'WhatsApp MCP Tray.lnk': $($_.Exception.Message)"
    }
  }
}

New-Item -ItemType Directory -Path $startup -Force | Out-Null
$startupShortcutPath = Join-Path $startup "WhatsApp MCP Tray.lnk"
$legacyStartupShortcutPath = Join-Path $startup "WhatsApp MCP Painel.lnk"
$legacyStartupVbsPath = Join-Path $startup "WhatsApp MCP Bridge.vbs"
foreach ($legacyStartupPath in @($startupShortcutPath, $legacyStartupShortcutPath, $legacyStartupVbsPath)) {
  if (-not (Test-Path $legacyStartupPath)) {
    continue
  }
  try {
    Remove-Item -LiteralPath $legacyStartupPath -Force
  } catch {
    Write-Warning "Atalho/VBS em Startup nao removido ($legacyStartupPath): $($_.Exception.Message)"
    Write-Warning "O auto-start padrao agora usa Registro do usuario. Remova esse item manualmente depois para evitar inicializacao duplicada."
  }
}
$startupTempShortcutPath = Join-Path $PanelDir "WhatsApp MCP Tray Startup.lnk"
$autoStartCreated = $false
$autoStartMethod = ""
try {
  if (Test-Path $startupTempShortcutPath) { Remove-Item -LiteralPath $startupTempShortcutPath -Force }
  Set-PanelRegistryAutostart
  $autoStartCreated = $true
  $autoStartMethod = "Registry Run (HKCU)"
} catch {
  Write-Warning "Auto-start por Registro nao criado: $($_.Exception.Message)"
  Write-Warning "Vou tentar o metodo alternativo por atalho na pasta Startup."
  try {
    New-PanelShortcut -Path $startupTempShortcutPath -Arguments ('"' + $launcherPath + '" --minimized') -Description "WhatsApp MCP local panel minimized"
    Copy-Item -LiteralPath $startupTempShortcutPath -Destination $startupShortcutPath -Force
    $autoStartCreated = Test-Path $startupShortcutPath
    if ($autoStartCreated) {
      $autoStartMethod = "Startup shortcut"
    }
  } catch {
    Write-Warning "Auto-start por Startup tambem falhou: $($_.Exception.Message)"
    Write-Warning "Crie manualmente o auto-start pelo Explorer: abra shell:startup e copie o atalho 'WhatsApp MCP Tray.lnk' da Area de Trabalho para essa pasta."
    Write-Warning "Se o antivirus pedir excecao, libere apenas o arquivo '$startupShortcutPath', nao powershell.exe."
  }
}

Write-Host "Painel instalado em: $PanelDir"
Write-Host "Icone criado: $iconPath"
Write-Host "Atalho criado: WhatsApp MCP Tray.lnk"
if ($autoStartCreated) {
  Write-Host "Auto-start criado: $autoStartMethod"
} else {
  Write-Host "Auto-start pendente: ver aviso acima"
}
