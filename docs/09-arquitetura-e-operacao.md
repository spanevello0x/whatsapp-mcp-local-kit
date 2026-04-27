# 09 - Arquitetura E Operacao

Este kit instala um conjunto local de componentes para WhatsApp + MCP.

O fluxo principal e Windows em modo perfis. O macOS ainda tem guia separado em `docs/10-macos.md`.

## Componentes Do Repositorio

```text
whatsapp-mcp-local-kit/
  scripts/                         instalacao, build, verificacao e MCP
  panel/                           painel de bandeja em Python/Tkinter
  profiles-mcp-server/             servidor MCP para multiplos perfis
  vendor/lharries-whatsapp-mcp/    bridge Go + codigo upstream
  docs/                            guias de instalacao, seguranca e operacao
```

## Componentes Instalados

Painel:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
```

Bases:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles
```

Bridge compartilhada:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles\bin\whatsapp-bridge.exe
```

Atalhos:

```text
Desktop\WhatsApp MCP Tray.lnk
AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\WhatsApp MCP Tray.lnk
```

## Como Funciona

1. O painel carrega `profiles.json`.
2. O usuario cadastra projetos e perfis.
3. Cada perfil recebe uma porta local propria.
4. Ao clicar em **Conectar QR**, o painel inicia a bridge daquele perfil.
5. A bridge conecta ao WhatsApp Web pelo aparelho vinculado.
6. A bridge grava sessao e mensagens em SQLite local.
7. O painel monitora crescimento da base, horario da ultima mensagem e status da porta.
8. O servidor MCP `whatsapp-profiles` consulta os bancos locais.
9. Codex/Claude so recebem conteudo quando uma consulta MCP pede dados.

O componente WhatsApp e baseado em **whatsmeow** em Go. Nao e Baileys.

Com a porta fechada, pesquisas continuam funcionando porque leem `messages.db` direto. A bridge precisa abrir para QR, sincronizacao e download de midia fisica.

## Dados Locais

Por perfil:

```text
whatsapp-bridge\store\whatsapp.db   sessao do WhatsApp
whatsapp-bridge\store\messages.db   mensagens sincronizadas
bridge.out.log                      log principal
bridge.err.log                      log de erro
.bridge.pid                         pid da bridge quando rodando
```

Esses arquivos nunca devem ser publicados.

## Bandeja E Auto-start

O atalho usa `pythonw.exe`, entao o painel abre sem terminal preto. Quando oculto, ele fica na bandeja.

O icone muda de status:

```text
Verde   sincronizando
Amarelo aguardando
Cinza   pausado/parado
```

## Sincronizacao

Primeira sync inteligente:

```text
initial_sync_min_minutes: 60
initial_sync_live_lag_minutes: 45
initial_sync_live_rate_per_minute: 20
initial_sync_stable_minutes: 30
initial_sync_hours: 24
```

Sync random:

```text
sync_min_minutes: 5
sync_idle_minutes: 3
sync_max_minutes: 25
random_sync_min_minutes: 10
random_sync_max_minutes: 50
```

## Verificacao

Depois de instalar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
```

O script checa painel, atalhos, auto-start, bridge, config MCP e bases locais.
