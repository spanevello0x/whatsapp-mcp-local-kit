# 06 - Modo rajadas

O modo rajadas abre a bridge por uma janela curta, sincroniza mensagens novas no `messages.db` e fecha de novo.

Quando a porta esta fechada, Codex e Claude ainda conseguem pesquisar a base local via MCP. A porta so precisa abrir para atualizar mensagens novas, enviar mensagens ou baixar midias pelo WhatsApp.

Padrao do painel:

```text
Tempo minimo aberta: 5 minutos
Fecha por inatividade: 3 minutos sem mudanca no messages.db
Timeout maximo: 25 minutos
Intervalo random: entre 10 e 50 minutos
```

Nao existe um evento confiavel de "WhatsApp terminou de sincronizar". Por isso, o painel considera a sync concluida quando a base local fica alguns minutos sem novas alteracoes, respeitando um tempo minimo e um timeout maximo. Isso reduz o tempo em que a porta local fica aberta e tambem reduz a chance de antivirus reclamar de um processo sempre ativo.

Edite:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\panel_config.json
```

Exemplo:

```json
{
  "bridge_root": "C:\\Users\\SEU_USUARIO\\CLAUDE COWORK\\Whatsapp\\whatsapp-mcp",
  "sync_min_minutes": 5,
  "sync_idle_minutes": 3,
  "sync_max_minutes": 25,
  "sync_extend_minutes": 10,
  "random_sync_min_minutes": 10,
  "random_sync_max_minutes": 50
}
```

Use o botao `Sincronizar agora` quando quiser atualizar sob demanda. Se uma sync ja estiver ativa, o botao estende a janela atual e mostra a acao no painel.
