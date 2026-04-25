# 10 - MacBook / macOS

O core da bridge funciona em macOS, mas o fluxo de producao com painel de **varios perfis**, projetos, bandeja e auto-start esta focado em Windows nesta versao.

No macOS, o kit ainda documenta o fluxo legado de um numero. Para varios perfis no Mac, trate como adaptacao futura ou rode o fluxo Windows em uma maquina Windows dedicada.

No macOS, a "bandeja" equivale ao menu bar. O auto-start e feito por LaunchAgent em:

```text
~/Library/LaunchAgents/com.whatsapp-mcp.tray.plist
```

## Instalacao rapida

```bash
git clone https://github.com/spanevello0x/whatsapp-mcp-local-kit.git
cd whatsapp-mcp-local-kit
chmod +x scripts/*.sh
./scripts/bootstrap-macos.sh --install-missing-dependencies --patch-localhost --configure-all-mcp
```

Se ainda nao houver sessao autenticada:

```bash
./scripts/first-login-macos.sh
```

Escaneie o QR no WhatsApp do celular em `Dispositivos conectados`.

## Dependencias

O script usa:

- Xcode Command Line Tools
- Homebrew
- Git
- Go
- Python 3
- uv
- clang

Se o Homebrew nao estiver instalado, instale por https://brew.sh/ e rode novamente.

## Caminhos padrao

```text
~/WhatsApp-MCP/whatsapp-mcp
~/Documents/WhatsApp MCP Panel
~/Desktop/WhatsApp MCP Tray.command
~/Library/LaunchAgents/com.whatsapp-mcp.tray.plist
```

O painel gera icones em:

```text
~/Documents/WhatsApp MCP Panel/whatsapp-mcp-icon.png
~/Documents/WhatsApp MCP Panel/whatsapp-mcp-tray-running.png
~/Documents/WhatsApp MCP Panel/whatsapp-mcp-tray-waiting.png
~/Documents/WhatsApp MCP Panel/whatsapp-mcp-tray-stopped.png
```

## Claude Desktop no macOS

Arquivo:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

O script `scripts/configure-mcp-macos.sh --claude` faz backup e adiciona o servidor `whatsapp`.

## Codex no macOS

```bash
./scripts/configure-mcp-macos.sh --codex
codex mcp list
```

## Antiviruses e seguranca no macOS

Nao desative Gatekeeper, XProtect, Defender for Endpoint, CrowdStrike, SentinelOne ou outro EDR globalmente.

Se precisar liberar excecoes, prefira estes caminhos:

```text
~/WhatsApp-MCP/whatsapp-mcp
~/Documents/WhatsApp MCP Panel
```

Em ambientes corporativos, a liberacao pode depender do admin de TI.

## Verificacao

```bash
./scripts/verify-local-macos.sh
```

O verificador checa runtimes, bridge, bancos, binario, painel, LaunchAgent, porta local e estatisticas SQLite.
