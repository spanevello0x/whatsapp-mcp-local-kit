param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles",
  [string]$BridgeBinary = "",
  [switch]$IncludeUnauthenticated
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "profile-lib.ps1")

$config = Read-ProfilesConfig $ProfilesDir
if (-not $BridgeBinary) {
  $BridgeBinary = Get-ProfilesBridgeBinary $ProfilesDir
}
if (-not (Test-Path $BridgeBinary)) {
  throw "Bridge binaria nao encontrada: $BridgeBinary. Rode scripts/profiles-build-bridge.ps1 primeiro."
}

$started = @()
$skipped = @()

foreach ($profile in @($config.profiles | Sort-Object port)) {
  if ($profile.enabled -eq $false) {
    $skipped += "$($profile.slug): desabilitado"
    continue
  }

  $paths = Ensure-ProfileDirs $ProfilesDir $profile.slug
  $sessionDb = Join-Path $paths.StoreDir "whatsapp.db"
  if (-not $IncludeUnauthenticated -and -not (Test-Path $sessionDb)) {
    $skipped += "$($profile.slug): sem sessao; rode profiles-login.ps1"
    continue
  }

  if (Test-ProfilePortOpen ([int]$profile.port)) {
    $skipped += "$($profile.slug): porta $($profile.port) ja aberta"
    continue
  }

  $outLog = Join-Path $paths.ProfileDir "bridge.out.log"
  $errLog = Join-Path $paths.ProfileDir "bridge.err.log"
  $oldPort = $env:WHATSAPP_MCP_PORT
  $env:WHATSAPP_MCP_PORT = [string]$profile.port
  try {
    $proc = Start-Process -FilePath $BridgeBinary -WorkingDirectory $paths.BridgeDir -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
    $proc.Id | Set-Content -LiteralPath $paths.PidPath -Encoding ASCII
    $started += "$($profile.slug): pid $($proc.Id), porta $($profile.port)"
  }
  finally {
    $env:WHATSAPP_MCP_PORT = $oldPort
  }
}

Write-Host "== Iniciados =="
if ($started.Count) { $started | ForEach-Object { Write-Host $_ } } else { Write-Host "nenhum" }

Write-Host "`n== Ignorados =="
if ($skipped.Count) { $skipped | ForEach-Object { Write-Host $_ -ForegroundColor Yellow } } else { Write-Host "nenhum" }
