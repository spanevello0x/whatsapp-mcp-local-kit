param(
  [switch]$UseWinget,
  [switch]$InstallMsys2,
  [switch]$InstallFfmpeg
)

$ErrorActionPreference = "Stop"

function Test-Tool {
  param(
    [string]$Name,
    [string[]]$Args = @("--version")
  )

  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if (-not $cmd) {
    Write-Host "[FALTA] $Name" -ForegroundColor Yellow
    return $false
  }

  Write-Host "[OK] $Name -> $($cmd.Source)"
  & $cmd.Source @Args
  return $true
}

function Install-WingetPackage {
  param(
    [string]$Name,
    [string]$Id
  )

  if (Test-Tool $Name) { return }

  if (-not $UseWinget) {
    Write-Host "Para instalar automaticamente: winget install --id=$Id -e" -ForegroundColor Yellow
    return
  }

  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if (-not $winget) {
    throw "winget nao encontrado. Instale as dependencias manualmente ou atualize o App Installer da Microsoft Store."
  }

  Write-Host "Instalando $Name via winget..."
  & $winget.Source install --id $Id -e --accept-package-agreements --accept-source-agreements
}

Write-Host "== Dependencias WhatsApp MCP Local Kit ==" -ForegroundColor Cyan

Install-WingetPackage "git" "Git.Git"
Install-WingetPackage "go" "GoLang.Go"
Install-WingetPackage "python" "Python.Python.3.12"
Install-WingetPackage "uv" "astral-sh.uv"

if ($InstallMsys2) {
  Install-WingetPackage "gcc" "MSYS2.MSYS2"
  $ucrtGcc = "C:\msys64\ucrt64\bin\gcc.exe"
  if (-not (Test-Path $ucrtGcc)) {
    Write-Host "`nMSYS2 instalado, mas GCC UCRT64 ainda pode faltar." -ForegroundColor Yellow
    Write-Host "Abra MSYS2 UCRT64 e rode:"
    Write-Host "pacman -S --needed mingw-w64-ucrt-x86_64-gcc"
    Write-Host "Depois adicione ao PATH: C:\msys64\ucrt64\bin"
  }
}

if ($InstallFfmpeg) {
  Install-WingetPackage "ffmpeg" "Gyan.FFmpeg"
}

Write-Host "`nVerificacao final:"
Test-Tool "git" @("--version") | Out-Null
Test-Tool "go" @("version") | Out-Null
Test-Tool "python" @("--version") | Out-Null
Test-Tool "uv" @("--version") | Out-Null
Test-Tool "gcc" @("--version") | Out-Null

Write-Host "`nSe alguma ferramenta acabou de ser instalada e ainda aparece como FALTA, feche e reabra o terminal." -ForegroundColor Cyan

