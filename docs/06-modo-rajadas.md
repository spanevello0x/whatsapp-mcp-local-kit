# 06 - Modo Rajadas E Sync Inteligente

O painel usa dois tipos de sincronizacao:

- **primeira sync inteligente** para um perfil recem autenticado;
- **rajadas random** depois que a base inicial estabiliza.

Quando a porta esta fechada, Codex e Claude ainda conseguem pesquisar a base local via MCP. A porta so precisa abrir para atualizar mensagens novas, enviar mensagens em uma feature futura ou baixar midias pelo WhatsApp.

## Primeira Sync Inteligente

Nao existe um evento confiavel de "WhatsApp terminou de sincronizar".

Por isso, o painel combina:

- tempo minimo de sync;
- horario da ultima mensagem sincronizada;
- velocidade de crescimento da base;
- tempo em estado estavel;
- limite maximo.

Padrao:

```text
minimo aberta: 60 minutos
ultima mensagem perto do agora: ate 45 minutos de atraso
ritmo baixo: ate 20 mensagens/minuto
tempo estavel: 30 minutos
limite maximo: 24 horas
```

Isso evita fechar cedo em importacao pesada, mas tambem evita deixar a porta aberta 24h quando a base claramente chegou perto do presente.

## Rajadas Random

Depois da primeira sync:

```text
tempo minimo aberta: 5 minutos
fecha por inatividade: 3 minutos sem crescimento da base
timeout maximo: 25 minutos
intervalo random: entre 10 e 50 minutos
```

O botao **Sync agora** abre uma janela sob demanda para o perfil selecionado.

## Configuracao

Arquivo:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\panel_config.json
```

Exemplo:

```json
{
  "profiles_mode": true,
  "profiles_dir": "C:\\Users\\SEU_USUARIO\\Documents\\WhatsApp MCP Profiles",
  "initial_sync_hours": 24,
  "initial_sync_min_minutes": 60,
  "initial_sync_live_lag_minutes": 45,
  "initial_sync_live_rate_per_minute": 20,
  "initial_sync_stable_minutes": 30,
  "sync_min_minutes": 5,
  "sync_idle_minutes": 3,
  "sync_max_minutes": 25,
  "random_sync_min_minutes": 10,
  "random_sync_max_minutes": 50
}
```

Normalmente nao precisa editar manualmente. Use o painel.
