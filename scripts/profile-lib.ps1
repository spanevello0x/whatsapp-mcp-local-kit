function Get-DefaultProfilesDir {
  return (Join-Path $env:USERPROFILE "Documents\WhatsApp MCP Profiles")
}

function ConvertTo-ProfileSlug {
  param([string]$Value)

  $slug = $Value.ToLowerInvariant()
  $slug = $slug -replace '[^a-z0-9]+', '-'
  $slug = $slug.Trim('-')
  if (-not $slug) {
    $slug = "profile-$(Get-Date -Format 'yyyyMMddHHmmss')"
  }
  return $slug
}

function Get-ProfilesConfigPath {
  param([string]$ProfilesDir)
  return (Join-Path $ProfilesDir "profiles.json")
}

function Read-ProfilesConfig {
  param([string]$ProfilesDir)

  $configPath = Get-ProfilesConfigPath $ProfilesDir
  if (Test-Path $configPath) {
    $raw = Get-Content -Raw -LiteralPath $configPath
    if ($raw.Trim()) {
      $config = $raw | ConvertFrom-Json
    } else {
      $config = [pscustomobject]@{}
    }
  } else {
    $config = [pscustomobject]@{}
  }

  if (-not ($config.PSObject.Properties.Name -contains "version")) {
    $config | Add-Member -MemberType NoteProperty -Name "version" -Value 1
  }
  if (-not ($config.PSObject.Properties.Name -contains "profiles_dir")) {
    $config | Add-Member -MemberType NoteProperty -Name "profiles_dir" -Value $ProfilesDir
  }
  if (-not ($config.PSObject.Properties.Name -contains "next_port")) {
    $config | Add-Member -MemberType NoteProperty -Name "next_port" -Value 8101
  }
  if (-not ($config.PSObject.Properties.Name -contains "profiles")) {
    $config | Add-Member -MemberType NoteProperty -Name "profiles" -Value @()
  }

  return $config
}

function Write-ProfilesConfig {
  param(
    [string]$ProfilesDir,
    [object]$Config
  )

  New-Item -ItemType Directory -Path $ProfilesDir -Force | Out-Null
  $configPath = Get-ProfilesConfigPath $ProfilesDir
  $Config | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $configPath -Encoding UTF8
  return $configPath
}

function Get-ProfileDir {
  param(
    [string]$ProfilesDir,
    [string]$Slug
  )
  return (Join-Path (Join-Path $ProfilesDir "profiles") $Slug)
}

function Ensure-ProfileDirs {
  param(
    [string]$ProfilesDir,
    [string]$Slug
  )

  $profileDir = Get-ProfileDir $ProfilesDir $Slug
  $bridgeDir = Join-Path $profileDir "whatsapp-bridge"
  $storeDir = Join-Path $bridgeDir "store"
  New-Item -ItemType Directory -Path $storeDir -Force | Out-Null
  return [pscustomobject]@{
    ProfileDir = $profileDir
    BridgeDir = $bridgeDir
    StoreDir = $storeDir
    LogPath = Join-Path $profileDir "bridge.log"
    PidPath = Join-Path $profileDir ".bridge.pid"
  }
}

function Get-Profile {
  param(
    [object]$Config,
    [string]$Slug
  )

  foreach ($profile in @($Config.profiles)) {
    if ($profile.slug -eq $Slug) {
      return $profile
    }
  }
  return $null
}

function Get-NextProfilePort {
  param([object]$Config)

  $ports = @($Config.profiles | ForEach-Object { [int]$_.port })
  $port = [int]$Config.next_port
  if ($ports.Count -gt 0) {
    $port = [Math]::Max($port, (($ports | Measure-Object -Maximum).Maximum + 1))
  }
  while ($ports -contains $port) {
    $port += 1
  }
  return $port
}

function Test-ProfilePortOpen {
  param([int]$Port)

  try {
    $client = New-Object Net.Sockets.TcpClient
    $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
    $open = $async.AsyncWaitHandle.WaitOne(500, $false)
    if ($open) {
      $client.EndConnect($async)
      $client.Close()
      return $true
    }
    $client.Close()
    return $false
  } catch {
    return $false
  }
}

function Test-ProfilePidAlive {
  param([string]$PidPath)

  if (-not (Test-Path $PidPath)) {
    return $false
  }
  try {
    $pidValue = [int](Get-Content -LiteralPath $PidPath -Raw).Trim()
    return [bool](Get-Process -Id $pidValue -ErrorAction SilentlyContinue)
  } catch {
    return $false
  }
}

function Get-ProfilesBridgeBinary {
  param([string]$ProfilesDir)

  if ($IsWindows -or $env:OS -eq "Windows_NT") {
    return (Join-Path (Join-Path $ProfilesDir "bin") "whatsapp-bridge.exe")
  }
  return (Join-Path (Join-Path $ProfilesDir "bin") "whatsapp-bridge")
}
