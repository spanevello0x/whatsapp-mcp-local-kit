param(
  [switch]$UseWinget,
  [switch]$InstallMsys2,
  [switch]$InstallFfmpeg
)

$ErrorActionPreference = "Stop"

function Update-CurrentPath {
  $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
  $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
  $extraPaths = @(
    "$env:USERPROFILE\.local\bin",
    "$env:LOCALAPPDATA\Microsoft\WindowsApps",
    "C:\Program Files\Go\bin",
    "C:\msys64\ucrt64\bin"
  )

  $env:Path = (@($machinePath, $userPath) + $extraPaths | Where-Object { $_ }) -join ";"
}

function Test-Tool {
  param(
    [string]$Name,
    [string[]]$ToolArgs = @("--version")
  )

  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if (-not $cmd) {
    Write-Host "[FALTA] $Name" -ForegroundColor Yellow
    return $false
  }

  Write-Host "[OK] $Name -> $($cmd.Source)"
  & $cmd.Source @ToolArgs
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
  Update-CurrentPath
}

Write-Host "== Dependencias WhatsApp MCP Local Kit ==" -ForegroundColor Cyan

Install-WingetPackage "git" "Git.Git"
Install-WingetPackage "go" "GoLang.Go"
Install-WingetPackage "python" "Python.Python.3.12"
Install-WingetPackage "uv" "astral-sh.uv"

if ($InstallMsys2) {
  $msysBash = "C:\msys64\usr\bin\bash.exe"
  if (-not (Test-Path $msysBash)) {
    if (-not $UseWinget) {
      Write-Host "Para instalar automaticamente: winget install --id=MSYS2.MSYS2 -e" -ForegroundColor Yellow
    } else {
      $winget = Get-Command winget -ErrorAction SilentlyContinue
      if (-not $winget) {
        throw "winget nao encontrado para instalar MSYS2."
      }
      Write-Host "Instalando MSYS2 via winget..."
      & $winget.Source install --id MSYS2.MSYS2 -e --accept-package-agreements --accept-source-agreements
    }
  }

  $ucrtGcc = "C:\msys64\ucrt64\bin\gcc.exe"
  if ((Test-Path $msysBash) -and -not (Test-Path $ucrtGcc)) {
    if ($UseWinget) {
      Write-Host "Instalando GCC UCRT64 dentro do MSYS2..."
      & $msysBash -lc "pacman -Sy --noconfirm --needed mingw-w64-ucrt-x86_64-gcc"
    } else {
      Write-Host "`nMSYS2 instalado, mas GCC UCRT64 ainda pode faltar." -ForegroundColor Yellow
      Write-Host "Abra MSYS2 UCRT64 e rode:"
      Write-Host "pacman -S --needed mingw-w64-ucrt-x86_64-gcc"
    }
  }

  Update-CurrentPath
  if (Test-Path $ucrtGcc) {
    Write-Host "[OK] gcc UCRT64 -> $ucrtGcc"
  } else {
    Write-Host "[FALTA] gcc UCRT64. O build da bridge pode falhar." -ForegroundColor Yellow
  }
}

if ($InstallFfmpeg) {
  Install-WingetPackage "ffmpeg" "Gyan.FFmpeg"
}

Write-Host "`nVerificacao final:"
Update-CurrentPath
Test-Tool "git" @("--version") | Out-Null
Test-Tool "go" @("version") | Out-Null
Test-Tool "python" @("--version") | Out-Null
Test-Tool "uv" @("--version") | Out-Null
Test-Tool "gcc" @("--version") | Out-Null

Write-Host "`nSe alguma ferramenta acabou de ser instalada e ainda aparece como FALTA, feche e reabra o terminal." -ForegroundColor Cyan
