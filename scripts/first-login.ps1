param(
  [string]$BridgeRoot = "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp"
)

$ErrorActionPreference = "Stop"

$bridgeDir = Join-Path $BridgeRoot "whatsapp-bridge"
if (-not (Test-Path $bridgeDir)) {
  throw "Pasta da bridge nao encontrada: $bridgeDir"
}

Write-Host "Este terminal ficara aberto para mostrar o QR Code, se o WhatsApp ainda nao estiver autenticado." -ForegroundColor Cyan
Write-Host "No celular: WhatsApp > Dispositivos conectados > Conectar um dispositivo."
Write-Host "Depois que conectar e comecar a sincronizar, voce pode fechar com Ctrl+C."

Push-Location $bridgeDir
try {
  go run main.go
}
finally {
  Pop-Location
}
