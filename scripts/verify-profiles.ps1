param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles",
  [string]$PanelDir = "$env:USERPROFILE\Documents\WhatsApp MCP Panel"
)

$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "profile-lib.ps1")

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath("Desktop")
$startup = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$profilesConfig = Get-ProfilesConfigPath $ProfilesDir
$bridgeBinary = Get-ProfilesBridgeBinary $ProfilesDir
$panelConfig = Join-Path $PanelDir "panel_config.json"

Write-Host "== WhatsApp MCP Profiles Verify ==" -ForegroundColor Cyan
Write-Host "ProfilesDir: $ProfilesDir"
Write-Host "PanelDir:    $PanelDir"

function Show-PathStatus {
  param([string]$Path)
  "{0,-100} {1}" -f $Path, (Test-Path $Path)
}

Write-Host "`n-- Arquivos principais --"
@(
  $ProfilesDir,
  $profilesConfig,
  $bridgeBinary,
  $PanelDir,
  (Join-Path $PanelDir "launch_panel.py"),
  (Join-Path $PanelDir "whatsapp_profiles_panel.py"),
  (Join-Path $PanelDir ".venv-user\Scripts\pythonw.exe"),
  (Join-Path $PanelDir ".venv\Scripts\pythonw.exe"),
  (Join-Path $desktop "WhatsApp MCP Tray.lnk"),
  (Join-Path $startup "WhatsApp MCP Tray.lnk"),
  (Join-Path $repoRoot "profiles-mcp-server\main.py"),
  (Join-Path $repoRoot "profiles-mcp-server\pyproject.toml")
) | ForEach-Object { Show-PathStatus $_ }

Write-Host "`n-- Atalhos --"
$wsh = New-Object -ComObject WScript.Shell
$runtimeVenv = Join-Path $PanelDir ".venv"
if (Test-Path (Join-Path $PanelDir ".venv-user\Scripts\pythonw.exe")) {
  $runtimeVenv = Join-Path $PanelDir ".venv-user"
}
$expectedPythonw = Join-Path $runtimeVenv "Scripts\pythonw.exe"
$pyvenvCfg = Join-Path $runtimeVenv "pyvenv.cfg"
if (Test-Path $pyvenvCfg) {
  $homeLine = Get-Content -LiteralPath $pyvenvCfg | Where-Object { $_ -match '^home\s*=' } | Select-Object -First 1
  if ($homeLine) {
    $pythonHome = ($homeLine -replace '^home\s*=\s*', '').Trim()
    $basePythonw = Join-Path $pythonHome "pythonw.exe"
    if ((Test-Path $basePythonw) -and ($basePythonw -notlike "*CodexSandboxOffline*")) {
      $expectedPythonw = $basePythonw
    }
  }
}
$expectedLauncher = Join-Path $PanelDir "launch_panel.py"
foreach ($shortcutPath in @(
  (Join-Path $desktop "WhatsApp MCP Tray.lnk"),
  (Join-Path $desktop "WhatsApp MCP Painel.lnk"),
  (Join-Path $startup "WhatsApp MCP Tray.lnk"),
  (Join-Path $startup "WhatsApp MCP Painel.lnk")
)) {
  if (-not (Test-Path $shortcutPath)) {
    Write-Host "$shortcutPath -> ausente" -ForegroundColor Yellow
    continue
  }
  try {
    $shortcut = $wsh.CreateShortcut($shortcutPath)
    $targetOk = ($shortcut.TargetPath -eq $expectedPythonw)
    $argsOk = ($shortcut.Arguments -like "*$expectedLauncher*")
    $status = if ($targetOk -and $argsOk) { "OK" } else { "REVISAR" }
    $color = if ($status -eq "OK") { "Green" } else { "Yellow" }
    Write-Host "$shortcutPath -> $status" -ForegroundColor $color
    Write-Host "  Target: $($shortcut.TargetPath)"
    Write-Host "  Args:   $($shortcut.Arguments)"
  } catch {
    Write-Host "$shortcutPath -> erro lendo atalho: $($_.Exception.Message)" -ForegroundColor Yellow
  }
}

$legacyStartupVbs = Join-Path $startup "WhatsApp MCP Bridge.vbs"
if (Test-Path $legacyStartupVbs) {
  Write-Host "$legacyStartupVbs -> REVISAR" -ForegroundColor Yellow
  Write-Host "  Auto-start legado detectado. Remova/desative este VBS; o correto e WhatsApp MCP Tray.lnk."
}

Write-Host "`n-- Config do painel --"
if (Test-Path $panelConfig) {
  try {
    $panelRaw = Get-Content -Raw -LiteralPath $panelConfig
    $panel = $panelRaw | ConvertFrom-Json
    [pscustomobject]@{
      profiles_mode = $panel.profiles_mode
      profiles_dir = $panel.profiles_dir
      profiles_config = $panel.profiles_config
      initial_sync_hours = $panel.initial_sync_hours
    } | Format-List
  } catch {
    Write-Host "Erro lendo panel_config.json: $($_.Exception.Message)" -ForegroundColor Yellow
  }
} else {
  Write-Host "panel_config.json nao encontrado" -ForegroundColor Yellow
}

Write-Host "`n-- Perfis --"
$config = Read-ProfilesConfig $ProfilesDir
if (-not @($config.profiles).Count) {
  Write-Host "Nenhum perfil cadastrado ainda. Isso e normal antes do primeiro uso da UI." -ForegroundColor Yellow
} else {
  @($config.profiles | Sort-Object port) | ForEach-Object {
    $paths = Ensure-ProfileDirs -ProfilesDir $ProfilesDir -Slug $_.slug -Config $config -Profile $_
    $messagesDb = Join-Path $paths.StoreDir "messages.db"
    $sessionDb = Join-Path $paths.StoreDir "whatsapp.db"
    $stats = [pscustomobject]@{ Messages = 0; Chats = 0; Last = "" }
    if (Test-Path $messagesDb) {
      $py = "import sqlite3,json; p=r'$messagesDb'; c=sqlite3.connect('file:'+p+'?mode=ro', uri=True, timeout=1); print(json.dumps({'messages': c.execute('select count(*) from messages').fetchone()[0], 'chats': c.execute('select count(*) from chats').fetchone()[0], 'last': c.execute('select max(timestamp) from messages').fetchone()[0]}))"
      $json = python -c $py 2>$null
      if ($json) {
        $data = $json | ConvertFrom-Json
        $stats = [pscustomobject]@{ Messages = $data.messages; Chats = $data.chats; Last = $data.last }
      } else {
        $stats = [pscustomobject]@{ Messages = "?"; Chats = "?"; Last = "erro sqlite" }
      }
    }
    [pscustomobject]@{
      Slug = $_.slug
      Name = $_.name
      Number = $_.number
      Port = $_.port
      Enabled = $_.enabled
      PortOpen = Test-ProfilePortOpen ([int]$_.port)
      PidAlive = Test-ProfilePidAlive $paths.PidPath
      SessionDb = Test-Path $sessionDb
      MessagesDb = Test-Path $messagesDb
      Messages = $stats.Messages
      Chats = $stats.Chats
      Last = $stats.Last
    }
  } | Format-Table -AutoSize
}

Write-Host "`n-- MCP local --"
$serverDir = Join-Path $repoRoot "profiles-mcp-server"
$venvPython = Join-Path $serverDir ".venv\Scripts\python.exe"
$uvCacheDir = Join-Path $serverDir ".uv-cache"
New-Item -ItemType Directory -Path $uvCacheDir -Force | Out-Null
$oldUvCache = $env:UV_CACHE_DIR
$env:UV_CACHE_DIR = $uvCacheDir
if (Test-Path $venvPython) {
  Push-Location $serverDir
  try {
    $output = & $venvPython -c "import main; print(len(main.list_profiles()))" 2>$null
    if ($LASTEXITCODE -eq 0 -and $output) {
      Write-Host "Perfis carregados pelo MCP: $output"
    } else {
      throw "venv python falhou"
    }
  } catch {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
      $output = & $uv.Source --directory $serverDir run python -c "import main; print(len(main.list_profiles()))" 2>$null
      if ($LASTEXITCODE -eq 0 -and $output) {
        Write-Host "Perfis carregados pelo MCP via uv: $output"
      } else {
        Write-Host "MCP local nao carregou. Rode uv --directory profiles-mcp-server sync e tente novamente." -ForegroundColor Yellow
      }
    } else {
      Write-Host "uv nao encontrado para fallback do MCP local." -ForegroundColor Yellow
    }
  } finally {
    Pop-Location
    $env:UV_CACHE_DIR = $oldUvCache
  }
} else {
  Write-Host "Ambiente Python do MCP ainda nao criado. Rode uv --directory profiles-mcp-server sync ou configure o MCP." -ForegroundColor Yellow
  $env:UV_CACHE_DIR = $oldUvCache
}

Write-Host "`n== Done =="
