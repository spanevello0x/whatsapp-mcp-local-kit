param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp",
  [string]$PanelDir = "$env:USERPROFILE\Documents\WhatsApp MCP Panel",
  [switch]$PatchLocalhost,
  [switch]$SkipBuild,
  [switch]$SkipPanel
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$bridgeParent = Split-Path -Parent $BridgeRoot

function Test-Tool {
  param(
    [string]$Name,
    [string[]]$Args
  )

  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if (-not $cmd) {
    Write-Host "[FALTA] $Name" -ForegroundColor Yellow
    return $false
  }

  Write-Host "[OK] $Name -> $($cmd.Source)"
  & $cmd.Source @Args
  return $true
}

Write-Host "== WhatsApp MCP Local Kit bootstrap ==" -ForegroundColor Cyan
Write-Host "BridgeRoot: $BridgeRoot"
Write-Host "PanelDir:   $PanelDir"

$requiredOk = $true
$requiredOk = (Test-Tool "git" @("--version")) -and $requiredOk
$requiredOk = (Test-Tool "go" @("version")) -and $requiredOk
$requiredOk = (Test-Tool "python" @("--version")) -and $requiredOk
$requiredOk = (Test-Tool "uv" @("--version")) -and $requiredOk

$gccOk = Test-Tool "gcc" @("--version")
if (-not $gccOk) {
  Write-Host "GCC/MSYS2 nao encontrado. O build pode falhar por causa do SQLite CGO." -ForegroundColor Yellow
}

if (-not $requiredOk) {
  Write-Host "`nInstale as dependencias faltantes e rode novamente." -ForegroundColor Red
  Write-Host "Veja docs/01-preparacao-windows.md"
  exit 2
}

if (-not (Test-Path $BridgeRoot)) {
  New-Item -ItemType Directory -Path $bridgeParent -Force | Out-Null
  Write-Host "`nClonando lharries/whatsapp-mcp..."
  git clone https://github.com/lharries/whatsapp-mcp.git $BridgeRoot
} else {
  Write-Host "`nBridge ja existe. Nao vou substituir: $BridgeRoot"
}

if (-not $SkipBuild) {
  $buildArgs = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $repoRoot "scripts\build-bridge.ps1"), "-BridgeRoot", $BridgeRoot)
  if ($PatchLocalhost) { $buildArgs += "-PatchLocalhost" }
  Write-Host "`nCompilando bridge..."
  powershell @buildArgs
}

if (-not $SkipPanel) {
  Write-Host "`nInstalando painel..."
  powershell -ExecutionPolicy Bypass -File (Join-Path $repoRoot "scripts\install-panel.ps1") -BridgeRoot $BridgeRoot -PanelDir $PanelDir
}

$sessionDb = Join-Path $BridgeRoot "whatsapp-bridge\store\whatsapp.db"
Write-Host "`n== Proximos passos ==" -ForegroundColor Cyan
if (-not (Test-Path $sessionDb)) {
  Write-Host "Sessao do WhatsApp ainda nao encontrada." -ForegroundColor Yellow
  Write-Host "Rode para escanear QR:"
  Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\first-login.ps1"
} else {
  Write-Host "Sessao local encontrada: $sessionDb"
}
Write-Host "Abra o atalho 'WhatsApp MCP Tray' na area de trabalho."
Write-Host "Para MCP, veja docs/03-mcp-codex-claude.md"

