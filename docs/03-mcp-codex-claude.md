# 03 - Codex e Claude Desktop

Configuracao automatica opcional:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-mcp.ps1 -All
```

No macOS:

```bash
./scripts/configure-mcp-macos.sh --all
```

Ou escolha apenas um:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-mcp.ps1 -Codex
powershell -ExecutionPolicy Bypass -File .\scripts\configure-mcp.ps1 -Claude
```

## Claude Desktop

Arquivo no Windows:

```text
%APPDATA%\Claude\claude_desktop_config.json
```

Arquivo no macOS:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

Exemplo:

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "C:\\Users\\SEU_USUARIO\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\Users\\SEU_USUARIO\\CLAUDE COWORK\\Whatsapp\\whatsapp-mcp\\whatsapp-mcp-server",
        "run",
        "main.py"
      ]
    }
  }
}
```

Exemplo macOS:

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "--directory",
        "/Users/SEU_USUARIO/WhatsApp-MCP/whatsapp-mcp/whatsapp-mcp-server",
        "run",
        "main.py"
      ]
    }
  }
}
```

Preserve outros MCPs existentes.

## Codex

Windows:

```powershell
codex mcp add whatsapp -- "C:\Users\SEU_USUARIO\.local\bin\uv.exe" --directory "C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp\whatsapp-mcp\whatsapp-mcp-server" run main.py
codex mcp list
```

macOS:

```bash
codex mcp add whatsapp -- "$(command -v uv)" --directory "$HOME/WhatsApp-MCP/whatsapp-mcp/whatsapp-mcp-server" run main.py
codex mcp list
```

Comece com consultas read-only antes de usar envio de mensagens.
