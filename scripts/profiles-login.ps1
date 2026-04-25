param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles",
  [Parameter(Mandatory = $true)][string]$Slug,
  [string]$BridgeBinary = ""
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "profile-lib.ps1")

$config = Read-ProfilesConfig $ProfilesDir
$profile = Get-Profile $config $Slug
if (-not $profile) {
  throw "Perfil nao encontrado: $Slug"
}

$paths = Ensure-ProfileDirs -ProfilesDir $ProfilesDir -Slug $profile.slug -Config $config -Profile $profile
if (-not $BridgeBinary) {
  $BridgeBinary = Get-ProfilesBridgeBinary $ProfilesDir
}
if (-not (Test-Path $BridgeBinary)) {
  throw "Bridge binaria nao encontrada: $BridgeBinary. Rode scripts/profiles-build-bridge.ps1 primeiro."
}

if (Test-ProfilePortOpen ([int]$profile.port)) {
  throw "Porta $($profile.port) ja esta aberta. Pare o perfil antes de login."
}

Write-Host "== Login do perfil WhatsApp ==" -ForegroundColor Cyan
Write-Host "Perfil: $($profile.name) [$($profile.slug)]"
Write-Host "Numero: $($profile.number)"
Write-Host "Porta:  $($profile.port)"
Write-Host "Pasta:  $($paths.ProfileDir)"
Write-Host ""
Write-Host "Se aparecer QR Code, escaneie pelo WhatsApp > Dispositivos conectados > Conectar dispositivo."
Write-Host "Quando autenticar e comecar a sincronizar, use Ctrl+C para fechar esta janela."

$oldPort = $env:WHATSAPP_MCP_PORT
$env:WHATSAPP_MCP_PORT = [string]$profile.port
Push-Location $paths.BridgeDir
try {
  & $BridgeBinary
}
finally {
  Pop-Location
  $env:WHATSAPP_MCP_PORT = $oldPort
}
