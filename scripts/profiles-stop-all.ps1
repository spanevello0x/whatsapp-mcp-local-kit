param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles",
  [string]$Slug = ""
)

$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "profile-lib.ps1")

$config = Read-ProfilesConfig $ProfilesDir
$profiles = @($config.profiles)
if ($Slug) {
  $profiles = @($profiles | Where-Object { $_.slug -eq $Slug })
}

foreach ($profile in $profiles) {
  $paths = Ensure-ProfileDirs -ProfilesDir $ProfilesDir -Slug $profile.slug -Config $config -Profile $profile
  if (-not (Test-Path $paths.PidPath)) {
    Write-Host "$($profile.slug): sem pid"
    continue
  }

  try {
    $pidValue = [int](Get-Content -LiteralPath $paths.PidPath -Raw).Trim()
    $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($proc) {
      Stop-Process -Id $pidValue -Force
      Write-Host "$($profile.slug): parado pid $pidValue"
    } else {
      Write-Host "$($profile.slug): pid $pidValue nao esta rodando"
    }
  } catch {
    Write-Host "$($profile.slug): erro ao parar: $($_.Exception.Message)" -ForegroundColor Yellow
  }
  Remove-Item -LiteralPath $paths.PidPath -Force -ErrorAction SilentlyContinue
}
