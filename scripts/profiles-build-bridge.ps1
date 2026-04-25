param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "profile-lib.ps1")

$repoRoot = Split-Path -Parent $PSScriptRoot
$bridgeSource = Join-Path $repoRoot "vendor\lharries-whatsapp-mcp\whatsapp-bridge"
$binary = Get-ProfilesBridgeBinary $ProfilesDir
$binDir = Split-Path -Parent $binary

if (-not (Test-Path $bridgeSource)) {
  throw "Bridge source nao encontrado: $bridgeSource"
}

New-Item -ItemType Directory -Path $binDir -Force | Out-Null

$msysUcrtBin = "C:\msys64\ucrt64\bin"
if (Test-Path (Join-Path $msysUcrtBin "gcc.exe")) {
  $env:Path = "$msysUcrtBin;$env:Path"
}

if (-not (Get-Command gcc -ErrorAction SilentlyContinue)) {
  Write-Host "GCC nao encontrado no PATH. O build pode falhar por causa do SQLite CGO." -ForegroundColor Yellow
}

Push-Location $bridgeSource
try {
  $env:CGO_ENABLED = "1"
  go mod download
  go build -ldflags="-s -w" -o $binary .
}
finally {
  Pop-Location
}

Get-Item $binary | Select-Object FullName,Length,LastWriteTime
