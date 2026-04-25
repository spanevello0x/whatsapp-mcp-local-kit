# 12 - Perfis Multiplos De WhatsApp

Este e o fluxo principal do kit.

Objetivo: manter varios numeros de WhatsApp autenticados na mesma maquina, cada um com pasta, porta, sessao e banco SQLite proprios, organizados por projeto.

## Estrutura Local

Por padrao:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles\
  profiles.json
  profiles_state.json
  bin\
    whatsapp-bridge.exe
  projetos\
    Vendedores\
      vendedor-joao\
        whatsapp-bridge\
          store\
            whatsapp.db
            messages.db
        bridge.out.log
        bridge.err.log
        .bridge.pid
    Administrativo\
      financeiro\
        whatsapp-bridge\
          store\
            whatsapp.db
            messages.db
```

Cada perfil tem:

- `slug`: identificador tecnico.
- `project`: projeto visivel.
- `name`: nome visivel do perfil.
- `description`: descricao livre.
- `number`: numero esperado ou identificado pelo QR.
- `port`: porta local exclusiva, como `8101`, `8102`, `8103`.
- `whatsapp.db`: sessao autenticada daquele numero.
- `messages.db`: mensagens sincronizadas daquele numero.

## Instalacao

```powershell
git clone https://github.com/spanevello0x/whatsapp-mcp-local-kit.git
cd whatsapp-mcp-local-kit
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp
```

Com tentativa de dependencias via `winget`, se o usuario autorizar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp -InstallMissingDependencies
```

Validacao:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
```

O comando instala o painel, compila a bridge de perfis, cria o atalho e registra o MCP `whatsapp-profiles`.

## Primeiro Uso No Painel

1. Abra o icone **WhatsApp MCP Tray** na area de trabalho.
2. Na primeira abertura, escolha a pasta geral das bases.
3. Clique em **Cadastrar primeiro perfil**.
4. Digite um projeto novo ou escolha um projeto ja criado.
5. Preencha nome e descricao do perfil.
6. O numero e opcional. Exemplo recomendado: `+55 (55) 999096505`.
7. Salve.
8. Selecione o perfil e clique em **Conectar QR**.
9. Escaneie o QR no WhatsApp do celular.
10. Quando aparecer autenticado, clique em **Voltar ao painel**.
11. O perfil segue sincronizando em background.

Para outro numero, clique em **Adicionar outro perfil** e repita.

## Projetos

Projetos sao categorias criadas pelo usuario, como:

```text
Vendedores
Pessoal
Administrativo
Obra da casa
```

O painel nao precisa trazer projetos pre-cadastrados. Ao digitar um projeto novo, ele cria a pasta do projeto automaticamente dentro da pasta geral. Ao cadastrar outro perfil, os projetos existentes aparecem como opcoes.

## Regra De Sincronizacao

Depois que um perfil autentica:

- a primeira sincronizacao entra em modo inteligente;
- ela roda por no minimo 60 minutos;
- ela pode ficar aberta por ate 24 horas;
- ela pode fechar antes quando a ultima mensagem local estiver perto do horario atual e o ritmo de importacao ficar baixo por tempo suficiente;
- depois disso, entra em sincronizacoes random.

Valores padrao:

```text
minimo primeira sync: 60 min
lag maximo para considerar perto do agora: 45 min
ritmo maximo para considerar estabilizado: 20 msgs/min
tempo estavel antes de fechar: 30 min
limite maximo: 24 h
```

Esses parametros existem para evitar fechar cedo durante uma importacao pesada. A regra nao depende apenas de tempo; ela olha tambem para horario da ultima mensagem e velocidade de crescimento da base.

## Status Do Painel

- **Aguardando QR**: o perfil ainda nao autenticou.
- **Primeira sync inteligente**: autenticado e importando base inicial.
- **Sincronizando random**: porta aberta em uma janela curta de sync.
- **Aguardando random**: porta fechada, base pesquisavel, proxima sync agendada.
- **Pausado**: perfil parado ate o usuario retomar.

## Remover Perfil

Selecione o perfil e clique em **Remover perfil**.

O painel pergunta:

- **Remover so do painel**: remove da UI e do MCP, mas mantem a pasta do perfil com `messages.db`, `whatsapp.db`, logs e midias.
- **Apagar perfil e dados locais**: fecha a bridge e apaga a pasta do perfil.

Por seguranca, a exclusao automatica so apaga pastas dentro da pasta geral do sistema.

## MCP De Perfis

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

Exemplos:

```text
Liste os perfis de WhatsApp disponiveis e diga quais estao com base sincronizada.
```

```text
Pesquise "orcamento" em todos os perfis e agrupe por vendedor.
```

```text
No perfil vendedor-joao, liste PDFs, imagens, audios e links do telefone +55 (11) 91234-5678.
```

## Comandos Uteis

Status:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-status.ps1
```

Iniciar todos os perfis com sessao:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-start-all.ps1
```

Parar todos:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\profiles-stop-all.ps1
```

## Isolamento

Cada perfil usa:

- porta propria;
- `whatsapp.db` proprio;
- `messages.db` proprio;
- logs proprios;
- pasta propria.

Assim, sincronizar o numero de um vendedor nao mistura base com outro.

## Limites Desta Versao

- O QR exige acao humana no celular.
- Envio de mensagem por perfil nao foi exposto no MCP de perfis.
- Download de midia fisica exige que a bridge daquele perfil esteja rodando.
- Se uma porta estiver ocupada, altere o campo `port` em `profiles.json`.
