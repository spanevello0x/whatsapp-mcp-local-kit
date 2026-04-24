# 03 - Codex e Claude Desktop

## Claude Desktop

Arquivo:

```text
%APPDATA%\Claude\claude_desktop_config.json
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

Preserve outros MCPs existentes.

## Codex

```powershell
codex mcp add whatsapp -- "C:\Users\SEU_USUARIO\.local\bin\uv.exe" --directory "C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp\whatsapp-mcp\whatsapp-mcp-server" run main.py
codex mcp list
```

Comece com consultas read-only antes de usar envio de mensagens.
