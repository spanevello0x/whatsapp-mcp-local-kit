param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles"
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "profile-lib.ps1")

$config = Read-ProfilesConfig $ProfilesDir
if (-not @($config.profiles).Count) {
  Write-Host "Nenhum perfil cadastrado em: $(Get-ProfilesConfigPath $ProfilesDir)"
  exit 0
}

@($config.profiles) | Sort-Object port | ForEach-Object {
  $paths = Ensure-ProfileDirs -ProfilesDir $ProfilesDir -Slug $_.slug -Config $config -Profile $_
  [pscustomobject]@{
    Slug = $_.slug
    Project = $_.project
    Name = $_.name
    Number = $_.number
    Port = $_.port
    Enabled = $_.enabled
    Session = Test-Path (Join-Path $paths.StoreDir "whatsapp.db")
    Messages = Test-Path (Join-Path $paths.StoreDir "messages.db")
    ProfileDir = $paths.ProfileDir
  }
} | Format-Table -AutoSize
