# 09 - Arquitetura e operacao

Este kit instala um conjunto local de componentes para WhatsApp + MCP no Windows.

## Componentes

```text
whatsapp-mcp-local-kit/
  scripts/                         instalacao, build, verificacao e MCP
  panel/                           painel de bandeja em Python/Tkinter
  vendor/lharries-whatsapp-mcp/    bridge Go + servidor MCP Python
  docs/                            guias de instalacao, seguranca e operacao
```

Depois da instalacao, os arquivos operacionais ficam em:

```text
C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp\whatsapp-mcp
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
```

## Como funciona

1. A bridge Go conecta ao WhatsApp Web pelo aparelho vinculado.
2. A bridge grava sessao e mensagens em SQLite local.
3. O painel de bandeja inicia e para a bridge em janelas de sincronizacao.
4. O servidor MCP Python consulta a base local e expoe ferramentas para Codex/Claude Desktop.
5. Codex/Claude so recebe conteudo quando uma consulta MCP pede dados.

## Dados locais

```text
whatsapp-bridge\store\whatsapp.db   sessao do WhatsApp
whatsapp-bridge\store\messages.db   mensagens sincronizadas
```

Esses arquivos nunca devem ser publicados.

## Bandeja e auto-start

O instalador cria:

```text
Desktop\WhatsApp MCP Tray.lnk
AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\WhatsApp MCP Tray.lnk
```

O atalho usa `pythonw.exe`, entao o painel abre sem terminal preto. Quando minimizado, ele fica na bandeja.

## Sincronizacao

O painel usa modo rajadas por padrao:

```text
sync_window_minutes: 8
random_sync_min_minutes: 10
random_sync_max_minutes: 50
```

Tambem existe botao de sincronizacao manual.

## Verificacao

Depois de instalar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-local.ps1
```

O script checa runtimes, bridge, painel, atalhos, auto-start, porta local e banco SQLite.

