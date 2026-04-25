param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles",
  [Parameter(Mandatory = $true)][string]$Name,
  [string]$Number = "",
  [string]$Description = "",
  [string]$Slug = "",
  [int]$Port = 0,
  [switch]$Disabled,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "profile-lib.ps1")

if (-not $Slug) {
  $seed = if ($Number) { "$Name-$Number" } else { $Name }
  $Slug = ConvertTo-ProfileSlug $seed
} else {
  $Slug = ConvertTo-ProfileSlug $Slug
}

$config = Read-ProfilesConfig $ProfilesDir
$existing = Get-Profile $config $Slug
if ($existing -and -not $Force) {
  throw "Perfil ja existe: $Slug. Use -Force para atualizar metadados."
}

if ($Port -le 0) {
  $Port = Get-NextProfilePort $config
}

$paths = Ensure-ProfileDirs $ProfilesDir $Slug
$profileRecord = [ordered]@{
  slug = $Slug
  name = $Name
  description = $Description
  number = $Number
  port = $Port
  enabled = (-not $Disabled)
  created_at = (Get-Date).ToString("s")
  updated_at = (Get-Date).ToString("s")
}

$profiles = @($config.profiles | Where-Object { $_.slug -ne $Slug })
if ($existing -and $existing.PSObject.Properties.Name -contains "created_at") {
  $profileRecord.created_at = $existing.created_at
}
$config.profiles = @($profiles + ([pscustomobject]$profileRecord))
$config.next_port = [Math]::Max(([int]$config.next_port), ($Port + 1))
$configPath = Write-ProfilesConfig $ProfilesDir $config

([pscustomobject]@{
  Config = $configPath
  Slug = $Slug
  Name = $Name
  Number = $Number
  Description = $Description
  Port = $Port
  Enabled = (-not $Disabled)
  ProfileDir = $paths.ProfileDir
  MessagesDb = Join-Path $paths.StoreDir "messages.db"
  SessionDb = Join-Path $paths.StoreDir "whatsapp.db"
}) | Format-List
