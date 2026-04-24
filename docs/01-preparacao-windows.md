# 01 - Preparacao no Windows

Verifique os runtimes:

```powershell
go version
python --version
uv --version
git --version
gcc --version
```

Requisitos usuais:

- Go 1.21+
- Python 3.11+
- uv
- Git
- GCC/MSYS2 para `github.com/mattn/go-sqlite3`

Clone a bridge upstream:

```powershell
mkdir "$env:USERPROFILE\CLAUDE COWORK\Whatsapp" -Force
cd "$env:USERPROFILE\CLAUDE COWORK\Whatsapp"
git clone https://github.com/lharries/whatsapp-mcp.git whatsapp-mcp
```

Caminho padrao usado pelos scripts:

```text
C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp\whatsapp-mcp
```

Primeiro login:

```powershell
cd "$env:USERPROFILE\CLAUDE COWORK\Whatsapp\whatsapp-mcp\whatsapp-bridge"
go run main.go
```

Escaneie o QR pelo WhatsApp do celular em `Dispositivos conectados`.

Depois do primeiro login, compile o executavel usado pelo painel:

```powershell
cd CAMINHO_DO_WHATSAPP_MCP_LOCAL_KIT
powershell -ExecutionPolicy Bypass -File .\scripts\build-bridge.ps1 -PatchLocalhost
```

O executavel esperado fica em:

```text
C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp\whatsapp-mcp\build-tmp\whatsapp-bridge.exe
```
