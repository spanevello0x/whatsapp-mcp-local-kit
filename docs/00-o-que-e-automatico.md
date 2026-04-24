# 00 - O que e automatico

Este kit tenta deixar a instalacao o mais proxima possivel de copia/cola, mas algumas partes dependem do computador e da conta de WhatsApp da pessoa.

## O que o bootstrap pode fazer

- Verificar se Go, Python, uv, Git e GCC existem.
- Tentar instalar dependencias faltantes via `winget`, se voce usar `-InstallMissingDependencies`.
- Clonar `lharries/whatsapp-mcp`, se ainda nao existir.
- Compilar a bridge para `build-tmp/whatsapp-bridge.exe`.
- Instalar o painel em `Documents\WhatsApp MCP Panel`.
- Criar atalho na area de trabalho.
- Criar auto-start para abrir o painel minimizado na bandeja.
- Registrar o MCP no Codex e/ou Claude Desktop, se voce usar `-ConfigureCodexMcp`, `-ConfigureClaudeMcp` ou `-ConfigureAllMcp`.

## O que nao pode vir pronto no GitHub

- Sessao do WhatsApp.
- QR Code autenticado.
- Historico de mensagens.
- `whatsapp.db`.
- `messages.db`.
- Excecoes de antivirus aplicadas automaticamente.
- Permissao para enviar mensagens.

Cada usuario precisa escanear o QR no proprio WhatsApp e decidir quais pastas liberar no proprio antivirus.

## Resultado esperado

Depois do bootstrap e do primeiro login:

- O painel abre sem janela preta.
- O painel minimiza para a bandeja.
- A bridge sincroniza em rajadas ou sob demanda.
- A base local fica no proprio PC.
- Codex/Claude Desktop podem consultar a base via MCP depois de configurados.
