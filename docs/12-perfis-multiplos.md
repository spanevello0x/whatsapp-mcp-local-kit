# 12 - Perfis multiplos de WhatsApp

Este fluxo e experimental e vive em branch separada. Ele nao altera a instalacao estavel de um unico WhatsApp.

Objetivo: manter varios numeros de WhatsApp autenticados na mesma maquina, cada um com pasta, porta, sessao e banco SQLite proprios.

## Estrutura local

Por padrao:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles\
  profiles.json
  bin\
    whatsapp-bridge.exe
  profiles\
    vendedor-joao\
      whatsapp-bridge\
        store\
          whatsapp.db
          messages.db
      bridge.out.log
      bridge.err.log
      .bridge.pid
    vendedora-maria\
      whatsapp-bridge\
        store\
          whatsapp.db
          messages.db
```

Cada perfil tem:

- `slug`: identificador tecnico.
- `name`: nome visivel.
- `description`: descricao livre.
- `number`: numero esperado.
- `port`: porta local exclusiva, como `8101`, `8102`, `8103`.
- `whatsapp.db`: sessao autenticada daquele numero.
- `messages.db`: mensagens sincronizadas daquele numero.

## 1. Compilar bridge compartilhada

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-build-bridge.ps1
```

Isso cria:

```text
Documents\WhatsApp MCP Profiles\bin\whatsapp-bridge.exe
```

## 2. Cadastrar perfis

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-create.ps1 -Name "Vendedor Joao" -Number "TELEFONE_COM_DDI" -Description "Vendedor SP"
```

Exemplo com slug manual:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-create.ps1 -Slug vendedor-joao -Name "Vendedor Joao" -Number "TELEFONE_COM_DDI" -Description "Vendedor SP"
```

Listar perfis:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-list.ps1
```

## 3. Login por QR Code

Rode um perfil por vez para escanear o QR:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-login.ps1 -Slug vendedor-joao
```

Quando aparecer o QR, escaneie no WhatsApp do numero correspondente.

Depois que autenticar e sincronizar, use `Ctrl+C` para fechar. A sessao fica salva em:

```text
Documents\WhatsApp MCP Profiles\profiles\vendedor-joao\whatsapp-bridge\store\whatsapp.db
```

Repita para cada vendedor.

## 4. Sincronizar todos

Depois que todos tiverem sessao (`whatsapp.db`), rode:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-start-all.ps1
```

Status:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-status.ps1
```

Parar todos:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-stop-all.ps1
```

Parar um:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-stop-all.ps1 -Slug vendedor-joao
```

## 5. MCP de perfis

Configurar no Codex e/ou Claude Desktop:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-profiles-mcp.ps1 -All
```

Nome do MCP:

```text
whatsapp-profiles
```

Tools principais:

```text
list_profiles
search_profile_messages
search_all_profile_messages
list_profile_assets
list_all_profile_assets
download_profile_media
```

Exemplos de pedido:

```text
Liste os perfis de WhatsApp disponiveis e diga quais estao com base sincronizada.
```

```text
Pesquise "orcamento" em todos os perfis e agrupe por vendedor.
```

```text
No perfil vendedor-joao, liste PDFs, imagens, audios e links do telefone TELEFONE_COM_DDI.
```

## O que fica isolado

Cada perfil usa:

- porta propria;
- `whatsapp.db` proprio;
- `messages.db` proprio;
- logs proprios;
- pasta propria.

Assim, sincronizar o numero de um vendedor nao mistura base com outro.

## Limites desta primeira versao

- Ainda nao tem painel visual para cadastrar perfis.
- Ainda nao cria auto-start para todos os perfis.
- Envio de mensagem por perfil nao foi exposto no MCP de perfis.
- Download de midia exige que a bridge daquele perfil esteja rodando.
- Se uma porta estiver ocupada, altere o campo `port` em `profiles.json`.
