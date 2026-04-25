param(
  [string]$ProfilesDir = "$env:USERPROFILE\Documents\WhatsApp MCP Profiles"
)

$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "profile-lib.ps1")

function Get-SqliteStats {
  param([string]$MessagesDb)

  if (-not (Test-Path $MessagesDb)) {
    return [pscustomobject]@{ Messages = 0; Chats = 0; Last = "" }
  }

  $py = "import sqlite3, json; p=r'$MessagesDb'; c=sqlite3.connect('file:'+p+'?mode=ro', uri=True, timeout=1); print(json.dumps({'messages': c.execute('select count(*) from messages').fetchone()[0], 'chats': c.execute('select count(*) from chats').fetchone()[0], 'last': c.execute('select max(timestamp) from messages').fetchone()[0]}))"
  $json = python -c $py 2>$null
  if (-not $json) {
    return [pscustomobject]@{ Messages = "?"; Chats = "?"; Last = "erro sqlite" }
  }
  $data = $json | ConvertFrom-Json
  return [pscustomobject]@{ Messages = $data.messages; Chats = $data.chats; Last = $data.last }
}

$config = Read-ProfilesConfig $ProfilesDir
if (-not @($config.profiles).Count) {
  Write-Host "Nenhum perfil cadastrado em: $(Get-ProfilesConfigPath $ProfilesDir)"
  exit 0
}

@($config.profiles | Sort-Object port) | ForEach-Object {
  $paths = Ensure-ProfileDirs -ProfilesDir $ProfilesDir -Slug $_.slug -Config $config -Profile $_
  $messagesDb = Join-Path $paths.StoreDir "messages.db"
  $stats = Get-SqliteStats $messagesDb
  [pscustomobject]@{
    Slug = $_.slug
    Name = $_.name
    Number = $_.number
    Port = $_.port
    Enabled = $_.enabled
    PortOpen = Test-ProfilePortOpen ([int]$_.port)
    PidAlive = Test-ProfilePidAlive $paths.PidPath
    Session = Test-Path (Join-Path $paths.StoreDir "whatsapp.db")
    Messages = $stats.Messages
    Chats = $stats.Chats
    Last = $stats.Last
  }
} | Format-Table -AutoSize
