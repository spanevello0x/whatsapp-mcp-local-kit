# 09 - Arquitetura e operacao

Este kit instala um conjunto local de componentes para WhatsApp + MCP no Windows e no macOS.

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

No macOS:

```text
~/WhatsApp-MCP/whatsapp-mcp
~/Documents/WhatsApp MCP Panel
```

## Como funciona

1. A bridge Go conecta ao WhatsApp Web pelo aparelho vinculado.
2. A bridge grava sessao e mensagens em SQLite local.
3. O painel de bandeja inicia e para a bridge em janelas de sincronizacao.
4. O servidor MCP Python consulta a base local e expoe ferramentas para Codex/Claude Desktop.
5. Codex/Claude so recebe conteudo quando uma consulta MCP pede dados.

Com a porta fechada, as consultas de pesquisa continuam funcionando porque leem o SQLite local. A bridge/porta 8080 so precisa estar aberta para atualizar a base, enviar mensagens ou baixar midias.

## Dados locais

```text
whatsapp-bridge\store\whatsapp.db   sessao do WhatsApp
whatsapp-bridge\store\messages.db   mensagens sincronizadas
```

Esses arquivos nunca devem ser publicados.

## Bandeja/menu bar e auto-start

No Windows, o instalador cria:

```text
Desktop\WhatsApp MCP Tray.lnk
AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\WhatsApp MCP Tray.lnk
```

O atalho usa `pythonw.exe`, entao o painel abre sem terminal preto. Quando minimizado, ele fica na bandeja.
O icone do Desktop usa `whatsapp-mcp-icon.ico`, gerado durante a instalacao.

No macOS, o instalador cria:

```text
~/Desktop/WhatsApp MCP Tray.command
~/Library/LaunchAgents/com.whatsapp-mcp.tray.plist
```

O LaunchAgent abre o painel no login. O menu bar substitui a ideia de bandeja do Windows.

## Status visual

O icone da bandeja/menu bar muda de cor:

```text
Verde   rodando/sincronizando
Amarelo aguardando proximo sync
Cinza   stopado/pausado
```

O tooltip do icone tambem mostra o status atual.

## Sincronizacao

O painel usa modo rajadas por padrao:

```text
sync_min_minutes: 5
sync_idle_minutes: 3
sync_max_minutes: 25
sync_extend_minutes: 10
random_sync_min_minutes: 10
random_sync_max_minutes: 50
```

Tambem existe botao de sincronizacao manual. Se o WhatsApp nao para de receber mensagens, a sync fecha por timeout maximo; se a base fica quieta, fecha por inatividade.

## Verificacao

Depois de instalar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-local.ps1
```

O script checa runtimes, bridge, painel, atalhos, auto-start, porta local e banco SQLite.
