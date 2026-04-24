param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp",
  [string]$PanelDir = "$env:USERPROFILE\Documents\WhatsApp MCP Panel"
)

$ErrorActionPreference = "Continue"

Write-Host "== WhatsApp MCP Local Verify ==" -ForegroundColor Cyan
Write-Host "BridgeRoot: $BridgeRoot"
Write-Host "PanelDir:   $PanelDir"

$env:Path = (@(
  [Environment]::GetEnvironmentVariable("Path", "Machine"),
  [Environment]::GetEnvironmentVariable("Path", "User"),
  "$env:USERPROFILE\.local\bin",
  "C:\Program Files\Go\bin",
  "C:\msys64\ucrt64\bin"
) | Where-Object { $_ }) -join ";"

$paths = @(
  $BridgeRoot,
  (Join-Path $BridgeRoot "whatsapp-bridge"),
  (Join-Path $BridgeRoot "whatsapp-mcp-server"),
  (Join-Path $BridgeRoot "whatsapp-bridge\store\messages.db"),
  (Join-Path $BridgeRoot "whatsapp-bridge\store\whatsapp.db"),
  (Join-Path $BridgeRoot "build-tmp\whatsapp-bridge.exe"),
  $PanelDir,
  (Join-Path $PanelDir "whatsapp_mcp_panel.py"),
  (Join-Path $PanelDir "whatsapp-mcp-icon.ico"),
  (Join-Path $PanelDir ".venv\Scripts\pythonw.exe"),
  (Join-Path ([Environment]::GetFolderPath("Desktop")) "WhatsApp MCP Tray.lnk"),
  (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\WhatsApp MCP Tray.lnk")
)

foreach ($p in $paths) {
  "{0,-85} {1}" -f $p, (Test-Path $p)
}

Write-Host "`n-- Runtimes --"
function Join-ProcessArguments {
  param(
    [string[]]$Items = @()
  )

  return ($Items | ForEach-Object {
    if ($_ -match '[\s"]') {
      '"' + ($_ -replace '"', '\"') + '"'
    } else {
      $_
    }
  }) -join " "
}

function Run-Tool {
  param(
    [string]$Exe,
    [string[]]$ToolArgs = @(),
    [int]$TimeoutSeconds = 8
  )

  Write-Host "`n> $Exe $($ToolArgs -join ' ')"
  $cmd = Get-Command $Exe -ErrorAction SilentlyContinue
  if (-not $cmd) {
    Write-Host "NAO ENCONTRADO OU BLOQUEADO" -ForegroundColor Yellow
    return
  }

  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $cmd.Source
  $psi.Arguments = Join-ProcessArguments $ToolArgs
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $psi.CreateNoWindow = $true

  $proc = [System.Diagnostics.Process]::Start($psi)
  if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
    try { $proc.Kill() } catch {}
    Write-Host "TIMEOUT apos $TimeoutSeconds segundos" -ForegroundColor Yellow
    return
  }

  $stdout = $proc.StandardOutput.ReadToEnd().Trim()
  $stderr = $proc.StandardError.ReadToEnd().Trim()
  if ($stdout) { Write-Host $stdout }
  if ($stderr) { Write-Host $stderr -ForegroundColor Yellow }
}

Run-Tool "uv" @("--version")
Run-Tool "go" @("version")
Run-Tool "python" @("--version")
Run-Tool "git" @("--version")
Run-Tool "gcc" @("--version")

Write-Host "`n-- Porta local 8080 --"
try {
  $client = New-Object Net.Sockets.TcpClient
  $async = $client.BeginConnect("127.0.0.1", 8080, $null, $null)
  $open = $async.AsyncWaitHandle.WaitOne(500, $false)
  if ($open) {
    $client.EndConnect($async)
    Write-Host "127.0.0.1:8080 aberta"
  } else {
    Write-Host "127.0.0.1:8080 fechada"
  }
  $client.Close()
} catch {
  Write-Host "127.0.0.1:8080 fechada"
}

$db = Join-Path $BridgeRoot "whatsapp-bridge\store\messages.db"
if (Test-Path $db) {
  Write-Host "`n-- SQLite stats --"
  $py = "import sqlite3; p=r'$db'; c=sqlite3.connect('file:'+p+'?mode=ro', uri=True, timeout=1); print('messages', c.execute('select count(*) from messages').fetchone()[0]); print('chats', c.execute('select count(*) from chats').fetchone()[0]); print('range', c.execute('select min(timestamp), max(timestamp) from messages').fetchone())"
  Run-Tool "python" @("-c", $py) 15
}

Write-Host "`n== Done =="
