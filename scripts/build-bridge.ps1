param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp",
  [switch]$PatchLocalhost
)

$ErrorActionPreference = "Stop"

$bridgeDir = Join-Path $BridgeRoot "whatsapp-bridge"
$mainGo = Join-Path $bridgeDir "main.go"
$outDir = Join-Path $BridgeRoot "build-tmp"
$outExe = Join-Path $outDir "whatsapp-bridge.exe"

if (-not (Test-Path $bridgeDir)) {
  throw "Pasta da bridge nao encontrada: $bridgeDir"
}
if (-not (Test-Path $mainGo)) {
  throw "main.go nao encontrado: $mainGo"
}

if ($PatchLocalhost) {
  $source = Get-Content -Raw -LiteralPath $mainGo
  if ($source -match 'fmt\.Sprintf\(":%d", port\)') {
    $backup = "$mainGo.bak"
    Copy-Item -LiteralPath $mainGo -Destination $backup -Force
    $source = $source -replace 'fmt\.Sprintf\(":%d", port\)', 'fmt.Sprintf("127.0.0.1:%d", port)'
    Set-Content -LiteralPath $mainGo -Value $source -Encoding UTF8
    Write-Host "Patch localhost aplicado. Backup: $backup"
  } else {
    Write-Host "Patch localhost nao aplicado: padrao esperado nao encontrado ou ja alterado."
  }
}

New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$msysUcrtBin = "C:\msys64\ucrt64\bin"
if (Test-Path (Join-Path $msysUcrtBin "gcc.exe")) {
  $env:Path = "$msysUcrtBin;$env:Path"
}

if (-not (Get-Command gcc -ErrorAction SilentlyContinue)) {
  Write-Host "GCC nao encontrado no PATH. Se o build falhar, rode scripts/install-dependencies.ps1 -UseWinget -InstallMsys2." -ForegroundColor Yellow
}

Push-Location $bridgeDir
try {
  $env:CGO_ENABLED = "1"
  go mod download
  go build -ldflags="-s -w" -o $outExe .
}
finally {
  Pop-Location
}

Get-Item $outExe | Select-Object FullName,Length,LastWriteTime
