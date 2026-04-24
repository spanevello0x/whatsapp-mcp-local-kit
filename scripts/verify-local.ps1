param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp"
)

$ErrorActionPreference = "Continue"

Write-Host "== WhatsApp MCP Local Verify ==" -ForegroundColor Cyan
Write-Host "BridgeRoot: $BridgeRoot"

$paths = @(
  $BridgeRoot,
  (Join-Path $BridgeRoot "whatsapp-bridge"),
  (Join-Path $BridgeRoot "whatsapp-mcp-server"),
  (Join-Path $BridgeRoot "whatsapp-bridge\store\messages.db"),
  (Join-Path $BridgeRoot "whatsapp-bridge\store\whatsapp.db"),
  (Join-Path $BridgeRoot "build-tmp\whatsapp-bridge.exe")
)

foreach ($p in $paths) {
  "{0,-85} {1}" -f $p, (Test-Path $p)
}

Write-Host "`n-- Runtimes --"
function Run-Tool {
  param(
    [string]$Exe,
    [string[]]$Args = @()
  )

  Write-Host "`n> $Exe $($Args -join ' ')"
  $cmd = Get-Command $Exe -ErrorAction SilentlyContinue
  if (-not $cmd) {
    Write-Host "NAO ENCONTRADO OU BLOQUEADO" -ForegroundColor Yellow
    return
  }
  & $cmd.Source @Args
}

Run-Tool "uv" @("--version")
Run-Tool "go" @("version")
Run-Tool "python" @("--version")
Run-Tool "git" @("--version")
Run-Tool "gcc" @("--version")

$db = Join-Path $BridgeRoot "whatsapp-bridge\store\messages.db"
if (Test-Path $db) {
  Write-Host "`n-- SQLite stats --"
  python -c "import sqlite3; p=r'$db'; c=sqlite3.connect(p); print('messages', c.execute('select count(*) from messages').fetchone()[0]); print('chats', c.execute('select count(*) from chats').fetchone()[0]); print('range', c.execute('select min(timestamp), max(timestamp) from messages').fetchone())"
}

Write-Host "`n== Done =="
