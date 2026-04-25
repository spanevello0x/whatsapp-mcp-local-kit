param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp",
  [string]$PanelDir = "$env:USERPROFILE\Documents\WhatsApp MCP Panel",
  [switch]$ProfilesMode,
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles",
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
    [string[]]$ToolArgs
  )

  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if (-not $cmd) {
    Write-Host "[FALTA] $Name" -ForegroundColor Yellow
    return $false
  }

  Write-Host "[OK] $Name -> $($cmd.Source)"
  & $cmd.Source @ToolArgs
  return $true
}

Write-Host "== WhatsApp MCP Local Kit bootstrap ==" -ForegroundColor Cyan
Write-Host "BridgeRoot: $BridgeRoot"
Write-Host "PanelDir:   $PanelDir"
if ($ProfilesMode) {
  Write-Host "Profiles:   $ProfilesDir"
}

if ($InstallMissingDependencies) {
  Write-Host "`nInstalando dependencias faltantes via winget quando possivel..."
  & (Join-Path $repoRoot "scripts\install-dependencies.ps1") -UseWinget -InstallMsys2
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

if (-not $ProfilesMode -and -not (Test-Path $BridgeRoot)) {
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
} elseif (-not $ProfilesMode) {
  Write-Host "`nBridge ja existe. Nao vou substituir: $BridgeRoot"
}

if (-not $SkipBuild) {
  Write-Host "`nCompilando bridge..."
  if ($ProfilesMode) {
    & (Join-Path $repoRoot "scripts\profiles-build-bridge.ps1") -ProfilesDir $ProfilesDir
  } elseif ($PatchLocalhost) {
    & (Join-Path $repoRoot "scripts\build-bridge.ps1") -BridgeRoot $BridgeRoot -PatchLocalhost
  } else {
    & (Join-Path $repoRoot "scripts\build-bridge.ps1") -BridgeRoot $BridgeRoot
  }
}

if (-not $SkipPanel) {
  Write-Host "`nInstalando painel..."
  if ($ProfilesMode) {
    & (Join-Path $repoRoot "scripts\install-panel.ps1") -BridgeRoot $BridgeRoot -PanelDir $PanelDir -ProfilesMode -ProfilesDir $ProfilesDir
  } else {
    & (Join-Path $repoRoot "scripts\install-panel.ps1") -BridgeRoot $BridgeRoot -PanelDir $PanelDir
  }
}

if ($ConfigureAllMcp -or $ConfigureCodexMcp -or $ConfigureClaudeMcp) {
  $mcpScript = Join-Path $repoRoot "scripts\configure-mcp.ps1"
  if ($ProfilesMode) {
    $mcpScript = Join-Path $repoRoot "scripts\configure-profiles-mcp.ps1"
  }
  if ($ConfigureAllMcp) {
    Write-Host "`nConfigurando MCP..."
    if ($ProfilesMode) {
      & $mcpScript -ProfilesDir $ProfilesDir -All
    } else {
      & $mcpScript -BridgeRoot $BridgeRoot -All
    }
  } else {
    Write-Host "`nConfigurando MCP..."
    if ($ProfilesMode) {
      if ($ConfigureCodexMcp) { & $mcpScript -ProfilesDir $ProfilesDir -Codex }
      if ($ConfigureClaudeMcp) { & $mcpScript -ProfilesDir $ProfilesDir -Claude }
    } else {
      if ($ConfigureCodexMcp) { & $mcpScript -BridgeRoot $BridgeRoot -Codex }
      if ($ConfigureClaudeMcp) { & $mcpScript -BridgeRoot $BridgeRoot -Claude }
    }
  }
}

Write-Host "`n== Proximos passos ==" -ForegroundColor Cyan
if ($ProfilesMode) {
  Write-Host "Abra o atalho 'WhatsApp MCP Tray' na area de trabalho."
  Write-Host "Na primeira abertura, escolha a pasta geral das bases."
  Write-Host "No painel, cadastre cada perfil por projeto e use 'Conectar QR' somente quando for autenticar aquele perfil."
  Write-Host "Depois do QR, a primeira sincronizacao usa modo inteligente; depois entra em rajadas aleatorias."
  Write-Host "Para remover um numero, selecione o perfil e use 'Remover perfil' para preservar ou apagar os dados locais."
  Write-Host "Para MCP, use o servidor 'whatsapp-profiles'."
  Write-Host "Para validar: powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1"
} else {
  $sessionDb = Join-Path $BridgeRoot "whatsapp-bridge\store\whatsapp.db"
  if (-not (Test-Path $sessionDb)) {
    Write-Host "Sessao do WhatsApp ainda nao encontrada." -ForegroundColor Yellow
    Write-Host "Rode para escanear QR:"
    Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\first-login.ps1"
  } else {
    Write-Host "Sessao local encontrada: $sessionDb"
  }
  Write-Host "Abra o atalho 'WhatsApp MCP Tray' na area de trabalho."
  Write-Host "Para MCP, veja docs/03-mcp-codex-claude.md ou rode scripts/configure-mcp.ps1"
}
