param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles",
  [switch]$Codex,
  [switch]$Claude,
  [switch]$All
)

$ErrorActionPreference = "Stop"

if ($All) {
  $Codex = $true
  $Claude = $true
}

if (-not $Codex -and -not $Claude) {
  Write-Host "Use -Codex, -Claude ou -All."
  exit 0
}

function Get-UvPath {
  $localUv = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
  if (Test-Path $localUv) { return $localUv }

  $cmd = Get-Command uv -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }

  throw "uv nao encontrado. Rode scripts/install-dependencies.ps1 ou instale uv manualmente."
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$serverDir = Join-Path $repoRoot "profiles-mcp-server"
if (-not (Test-Path $serverDir)) {
  throw "Servidor MCP de perfis nao encontrado: $serverDir"
}

New-Item -ItemType Directory -Path $ProfilesDir -Force | Out-Null
$profilesConfig = Join-Path $ProfilesDir "profiles.json"
if (-not (Test-Path $profilesConfig)) {
  @{
    version = 1
    profiles_dir = $ProfilesDir
    next_port = 8101
    profiles = @()
  } | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $profilesConfig -Encoding UTF8
}

$uv = Get-UvPath
$mcpArgs = @("--directory", $serverDir, "run", "main.py")

if ($Codex) {
  $codexCmd = Get-Command codex -ErrorAction SilentlyContinue
  if (-not $codexCmd) {
    Write-Host "Codex CLI nao encontrado. Configure manualmente com:" -ForegroundColor Yellow
    Write-Host "codex mcp add whatsapp-profiles -- `"$uv`" --directory `"$serverDir`" run main.py"
  } else {
    Write-Host "Configurando MCP whatsapp-profiles no Codex..."
    & $codexCmd.Source mcp add whatsapp-profiles -- $uv @mcpArgs
    & $codexCmd.Source mcp list
  }
}

if ($Claude) {
  $claudeDir = Join-Path $env:APPDATA "Claude"
  $configPath = Join-Path $claudeDir "claude_desktop_config.json"
  New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null

  if (Test-Path $configPath) {
    $backup = "$configPath.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item -LiteralPath $configPath -Destination $backup -Force
    $raw = Get-Content -Raw -LiteralPath $configPath
    if ($raw.Trim()) {
      $config = $raw | ConvertFrom-Json
    } else {
      $config = [pscustomobject]@{}
    }
    Write-Host "Backup Claude config: $backup"
  } else {
    $config = [pscustomobject]@{}
  }

  if (-not ($config.PSObject.Properties.Name -contains "mcpServers")) {
    $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value ([pscustomobject]@{})
  }

  $servers = $config.mcpServers
  if ($servers.PSObject.Properties.Name -contains "whatsapp-profiles") {
    $servers.PSObject.Properties.Remove("whatsapp-profiles")
  }

  $serverConfig = [ordered]@{
    command = $uv
    args = $mcpArgs
    env = @{
      WHATSAPP_MCP_PROFILES_CONFIG = $profilesConfig
    }
  }

  $servers | Add-Member -MemberType NoteProperty -Name "whatsapp-profiles" -Value $serverConfig
  $config | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $configPath -Encoding UTF8

  Write-Host "Claude Desktop config atualizado: $configPath"
  Write-Host "Feche o Claude Desktop completamente e abra de novo."
}

Write-Host "Profiles config: $profilesConfig"
