# 03 - Codex E Claude Desktop

O modo principal do kit registra o MCP:

```text
whatsapp-profiles
```

Ele consulta varios perfis/numeros a partir dos bancos locais em `WhatsApp MCP Profiles`.

## Configuracao Automatica

Durante o bootstrap:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp
```

Ou manualmente:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-profiles-mcp.ps1 -All
```

Escolha apenas um cliente:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-profiles-mcp.ps1 -Codex
powershell -ExecutionPolicy Bypass -File .\scripts\configure-profiles-mcp.ps1 -Claude
```

## Claude Desktop

Arquivo no Windows:

```text
%APPDATA%\Claude\claude_desktop_config.json
```

Exemplo:

```json
{
  "mcpServers": {
    "whatsapp-profiles": {
      "command": "C:\\Users\\SEU_USUARIO\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\Users\\SEU_USUARIO\\Documents\\whatsapp-mcp-local-kit\\profiles-mcp-server",
        "run",
        "main.py"
      ],
      "env": {
        "WHATSAPP_MCP_PROFILES_CONFIG": "C:\\Users\\SEU_USUARIO\\Documents\\WhatsApp MCP Profiles\\profiles.json"
      }
    }
  }
}
```

O script faz merge e preserva outros MCPs existentes.

## Codex

Depois da configuracao automatica:

```powershell
codex mcp list
```

O servidor deve aparecer como `whatsapp-profiles`.

## Tools Principais

```text
list_profiles
search_profile_messages
search_all_profile_messages
list_profile_assets
list_all_profile_assets
download_profile_media
```

## Exemplos De Uso

```text
Liste os perfis de WhatsApp disponiveis e diga quais tem base local.
```

```text
Pesquise "orcamento" em todos os perfis, agrupe por projeto e destaque telefones envolvidos.
```

```text
No perfil vendedor-joao, liste fotos, videos, audios, PDFs, documentos e links do telefone +55 (11) 91234-5678.
```

## Porta Fechada

Pesquisas em mensagens e inventario de links/arquivos funcionam com a porta fechada, porque o MCP le `messages.db` direto.

Baixar uma midia fisica com `download_profile_media` exige a bridge do perfil aberta, porque o arquivo precisa ser recuperado pelo WhatsApp Web.

## macOS

O modo perfis com painel de bandeja e auto-start esta focado em Windows. Para macOS, veja `docs/10-macos.md`, que descreve o fluxo legado de um numero e notas de adaptacao.
