param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp",
  [string]$PanelDir = "$env:USERPROFILE\Documents\WhatsApp MCP Panel",
  [switch]$InstallMissingDependencies,
  [switch]$PatchLocalhost,
  [switch]$ConfigureCodexMcp,
  [switch]$ConfigureClaudeMcp,
  [switch]$ConfigureAllMcp,
  [switch]$SkipBuild,
  [switch]$SkipPanel
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$bridgeParent = Split-Path -Parent $BridgeRoot
$vendoredBridge = Join-Path $repoRoot "vendor\lharries-whatsapp-mcp"

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

if ($InstallMissingDependencies) {
  Write-Host "`nInstalando dependencias faltantes via winget quando possivel..."
  powershell -ExecutionPolicy Bypass -File (Join-Path $repoRoot "scripts\install-dependencies.ps1") -UseWinget -InstallMsys2
}

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
  if (-not (Test-Path $vendoredBridge)) {
    throw "Codigo da bridge vendorizada nao encontrado: $vendoredBridge"
  }
  New-Item -ItemType Directory -Path $bridgeParent -Force | Out-Null
  New-Item -ItemType Directory -Path $BridgeRoot -Force | Out-Null
  Write-Host "`nCopiando bridge incluida neste repositorio..."
  Copy-Item -LiteralPath (Join-Path $vendoredBridge "whatsapp-bridge") -Destination $BridgeRoot -Recurse -Force
  Copy-Item -LiteralPath (Join-Path $vendoredBridge "whatsapp-mcp-server") -Destination $BridgeRoot -Recurse -Force
  Copy-Item -LiteralPath (Join-Path $vendoredBridge "LICENSE") -Destination (Join-Path $BridgeRoot "LICENSE.upstream-lharries-whatsapp-mcp") -Force
  Copy-Item -LiteralPath (Join-Path $vendoredBridge "README-lharries-whatsapp-mcp.md") -Destination (Join-Path $BridgeRoot "README.upstream-lharries-whatsapp-mcp.md") -Force
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

if ($ConfigureAllMcp -or $ConfigureCodexMcp -or $ConfigureClaudeMcp) {
  $mcpScript = Join-Path $repoRoot "scripts\configure-mcp.ps1"
  $mcpArgs = @("-ExecutionPolicy", "Bypass", "-File", $mcpScript, "-BridgeRoot", $BridgeRoot)
  if ($ConfigureAllMcp) {
    $mcpArgs += "-All"
  } else {
    if ($ConfigureCodexMcp) { $mcpArgs += "-Codex" }
    if ($ConfigureClaudeMcp) { $mcpArgs += "-Claude" }
  }
  Write-Host "`nConfigurando MCP..."
  powershell @mcpArgs
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
Write-Host "Para MCP, veja docs/03-mcp-codex-claude.md ou rode scripts/configure-mcp.ps1"
