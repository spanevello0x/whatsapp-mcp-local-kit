# 06 - Modo Rajadas E Sync Inteligente

O painel usa dois tipos de sincronizacao:

- **primeira sync inteligente** para um perfil recem autenticado;
- **rajadas random** depois que a base inicial estabiliza;
- **sync de retomada** quando o painel abre depois de boot ou depois de ficar encerrado.

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
minimo aberta: 10 minutos
ultima mensagem perto do agora: ate 45 minutos de atraso
ritmo baixo: ate 20 mensagens/minuto
tempo estavel: 5 minutos
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

## Sync De Retomada Ao Abrir

Quando o Windows/macOS inicia o painel, ou quando o usuario abre o painel depois de fechar o sistema completo, o painel agenda uma sync curta para perfis que:

- estao cadastrados;
- ja possuem sessao WhatsApp autenticada.

Para evitar sobrecarga, ele nao abre todas as bridges ao mesmo tempo. Por padrao:

```text
primeiro perfil: cerca de 30s apos abrir
perfis seguintes: espacados em 2 minutos
jitter: ate 45s para nao ficar mecanico
anti-duplicacao: nao reagenda se o painel reiniciar varias vezes em menos de 5 minutos
```

Perfis ainda em primeira sync inteligente continuam pela regra da primeira sync. Perfis sem QR/login continuam aguardando QR.

Pausa manual para a sync daquele momento continua funcionando enquanto o painel esta aberto. No proximo boot, login ou abertura depois de ficar encerrado, o padrao de producao e limpar a pausa anterior e retomar os perfis autenticados. Isso evita que uma pausa feita em outro dia deixe o sistema parado sem o usuario perceber.

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
  "initial_sync_min_minutes": 10,
  "initial_sync_live_lag_minutes": 45,
  "initial_sync_live_rate_per_minute": 20,
  "initial_sync_stable_minutes": 5,
  "sync_min_minutes": 5,
  "sync_idle_minutes": 3,
  "sync_max_minutes": 25,
  "random_sync_min_minutes": 10,
  "random_sync_max_minutes": 50,
  "startup_resume_sync": true,
  "startup_resume_clear_paused": true,
  "startup_resume_initial_delay_seconds": 30,
  "startup_resume_stagger_seconds": 120,
  "startup_resume_jitter_seconds": 45,
  "startup_resume_min_interval_minutes": 5
}
```

Normalmente nao precisa editar manualmente. Use o painel.
