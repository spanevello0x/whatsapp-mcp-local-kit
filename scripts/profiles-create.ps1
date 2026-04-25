param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles",
  [Parameter(Mandatory = $true)][string]$Name,
  [string]$Project = "Geral",
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

$projectName = ($Project.Trim())
if (-not $projectName) { $projectName = "Geral" }
$projectSlug = ConvertTo-ProfileSlug $projectName
$projectFolder = ConvertTo-SafeFolderName $projectName
$projects = @($config.projects)
$projectRecord = $null
foreach ($item in $projects) {
  if ($item.slug -eq $projectSlug -or $item.name -eq $projectName) {
    $projectRecord = $item
    break
  }
}
if ($null -eq $projectRecord) {
  $projectRecord = [pscustomobject]@{
    slug = $projectSlug
    name = $projectName
    folder_name = $projectFolder
    created_at = (Get-Date).ToString("s")
  }
  $config.projects = @($projects + $projectRecord)
} else {
  if (-not (Get-ObjectProperty $projectRecord "folder_name" "")) {
    $projectRecord | Add-Member -MemberType NoteProperty -Name "folder_name" -Value $projectFolder -Force
  }
}

$profileRecord = [ordered]@{
  slug = $Slug
  project_slug = $projectRecord.slug
  project = $projectRecord.name
  project_folder = (Get-ObjectProperty $projectRecord "folder_name" $projectRecord.slug)
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
$profileObject = [pscustomobject]$profileRecord
$paths = Ensure-ProfileDirs -ProfilesDir $ProfilesDir -Slug $Slug -Config $config -Profile $profileObject
$config.profiles = @($profiles + $profileObject)
$config.next_port = [Math]::Max(([int]$config.next_port), ($Port + 1))
$configPath = Write-ProfilesConfig $ProfilesDir $config

([pscustomobject]@{
  Config = $configPath
  Slug = $Slug
  Project = $projectRecord.name
  Name = $Name
  Number = $Number
  Description = $Description
  Port = $Port
  Enabled = (-not $Disabled)
  ProfileDir = $paths.ProfileDir
  MessagesDb = Join-Path $paths.StoreDir "messages.db"
  SessionDb = Join-Path $paths.StoreDir "whatsapp.db"
}) | Format-List
