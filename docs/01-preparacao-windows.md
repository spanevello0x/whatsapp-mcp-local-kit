# 01 - Preparacao No Windows

Antes de instalar, verifique os runtimes:

```powershell
git --version
go version
python --version
uv --version
gcc --version
```

Requisitos usuais:

- Git
- Go 1.21+
- Python 3.11+
- uv
- GCC/MSYS2 para `github.com/mattn/go-sqlite3`

Se quiser que o kit tente instalar dependencias faltantes via `winget`, use `-InstallMissingDependencies` no bootstrap. Em maquinas com antivirus sensivel, leia `docs/02-antivirus.md` antes.

## Instalacao Recomendada

```powershell
git clone https://github.com/spanevello0x/whatsapp-mcp-local-kit.git
cd whatsapp-mcp-local-kit
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp
```

Com tentativa de instalar dependencias:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp -InstallMissingDependencies
```

Validacao:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
```

## Caminhos Padrao

Painel:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
```

Bases/perfis:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles
```

Bridge compartilhada:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles\bin\whatsapp-bridge.exe
```

Atalho:

```text
Desktop\WhatsApp MCP Tray.lnk
```

Auto-start:

```text
AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\WhatsApp MCP Tray.lnk
```

## Primeiro Login

O primeiro login deve ser feito pelo painel:

1. Abra **WhatsApp MCP Tray**.
2. Cadastre um perfil.
3. Clique em **Conectar QR**.
4. Escaneie o QR pelo WhatsApp do celular em **Aparelhos conectados**.

Depois disso, o painel gerencia a primeira sync inteligente e as sincronizacoes random.
