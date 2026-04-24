# 06 - Modo rajadas

O modo rajadas abre a bridge por uma janela curta, sincroniza mensagens novas e fecha de novo.

Padrao do painel:

```text
Janela de sync: 8 minutos
Intervalo random: entre 10 e 50 minutos
```

Isso reduz o tempo em que a porta local fica aberta. Tambem pode reduzir a chance de antivirus reclamar de um processo sempre ativo.

Edite:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\panel_config.json
```

Exemplo:

```json
{
  "bridge_root": "C:\\Users\\SEU_USUARIO\\CLAUDE COWORK\\Whatsapp\\whatsapp-mcp",
  "sync_window_minutes": 8,
  "random_sync_min_minutes": 10,
  "random_sync_max_minutes": 50
}
```

Use o botao `Sincronizar agora` quando quiser atualizar sob demanda.

