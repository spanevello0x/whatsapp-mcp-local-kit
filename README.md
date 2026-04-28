# WhatsApp MCP Local Kit

Kit em portugues para instalar um painel local do WhatsApp MCP com:

- varios numeros/perfis na mesma maquina;
- organizacao por projetos;
- base SQLite local separada por perfil;
- icone no Desktop e bandeja do Windows;
- primeira sincronizacao inteligente;
- sincronizacoes random depois da base estabilizar;
- MCP para Codex e Claude pesquisarem mensagens, arquivos e links.

Este repositorio nao inclui mensagens, sessoes, bancos SQLite, QR Codes ou credenciais. Ele inclui instalador, painel, scripts e uma copia vendorizada do projeto open-source [`lharries/whatsapp-mcp`](https://github.com/lharries/whatsapp-mcp), distribuida sob MIT com atribuicao preservada.

## Comece Por Aqui

Para uma instalacao assistida por IA, abra [COMECE_AQUI.md](COMECE_AQUI.md) e cole o prompt em uma conversa nova do Codex ou Claude com acesso ao computador.

O fluxo de producao recomendado hoje e o **modo perfis**:

- cada numero de WhatsApp vira um perfil;
- cada perfil pertence a um projeto, como Vendedores, Pessoal ou Administrativo;
- cada perfil tem `whatsapp.db`, `messages.db`, logs e porta local proprios;
- a IA consulta a base pelo MCP mesmo quando a bridge daquele perfil esta fechada.

## O Que Este Kit Entrega

- Bootstrap Windows para preparar dependencias, compilar a bridge e instalar o painel.
- Bootstrap macOS em modo perfis beta para MacBook.
- Painel local em Python/Tkinter com icone no Desktop/Mesa e bandeja/menu bar.
- Auto-start padrao para abrir minimizado com o Windows ou macOS.
- Cadastro de perfis por projeto.
- QR Code sob demanda por perfil.
- Identificacao do numero pelo QR quando a bridge retorna o JID do WhatsApp.
- Primeira sincronizacao inteligente, com limite maximo e fechamento automatico quando a importacao estabiliza.
- Sincronizacoes random depois da primeira sincronizacao.
- Sync de retomada ao abrir o painel ou reiniciar o PC, com perfis escalonados para evitar sobrecarga.
- Botao para abrir pasta do projeto e copiar caminho do `messages.db`.
- Botao para remover perfil, escolhendo entre preservar dados ou apagar a pasta/base local.
- MCP `whatsapp-profiles` para pesquisar mensagens e listar fotos, videos, audios, PDFs, documentos e links.
- Documentacao de antivirus com excecoes pontuais, sem liberar PowerShell globalmente.
- Guias para Codex e Claude Desktop.

## Aviso De Seguranca

`messages.db` contem conversas reais. Nunca publique `.db`, logs, backups de sessao, QR Codes ou tokens.

O painel usa uma bridge local nao oficial do WhatsApp Web. Ela deve ficar limitada a `127.0.0.1` e pode quebrar se o protocolo do WhatsApp mudar. Para operacao comercial critica e oficial, avalie tambem a WhatsApp Business Platform da Meta.

Esta bridge usa **whatsmeow** em Go. Ela nao e uma conexao Baileys.

Antes de rodar o instalador, leia [docs/02-antivirus.md](docs/02-antivirus.md). O caminho seguro e liberar apenas as pastas do kit, do painel e das bases locais. Nao crie excecao global para `powershell.exe`, `cmd.exe`, `python.exe`, `go.exe` ou `wscript.exe`.

## Como O Sistema Escolhe Windows Ou Mac

O repositorio e o mesmo para Windows e macOS, mas os instaladores sao separados:

- Windows: `scripts/bootstrap-windows.ps1`
- macOS: `scripts/bootstrap-macos.sh`

Quando voce cola este GitHub no Codex ou Claude, a IA deve primeiro diagnosticar o sistema operacional e entao escolher o script correto. Se voce estiver instalando manualmente, use o bloco correspondente abaixo.

Nao rode o script de Windows no Mac nem o script de Mac no Windows. O painel, o MCP `whatsapp-profiles`, a bridge, a sync inteligente/random e a sync de retomada existem nos dois fluxos.

## Instalacao Rapida No Windows

Clone o repositorio:

```powershell
git clone https://github.com/spanevello0x/whatsapp-mcp-local-kit.git
cd whatsapp-mcp-local-kit
```

Instale em modo perfis e configure MCP para Codex e Claude:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp
```

Se faltarem dependencias e voce quiser tentar instalar via `winget`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp -InstallMissingDependencies
```

Valide a instalacao:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
```

Depois abra o icone **WhatsApp MCP Tray** na area de trabalho.

## Instalacao Rapida No MacBook / macOS

No macOS o modo perfis tambem e o fluxo recomendado, mas ainda deve ser tratado como **beta ate validacao em um Mac real**:

```bash
git clone https://github.com/spanevello0x/whatsapp-mcp-local-kit.git
cd whatsapp-mcp-local-kit
chmod +x scripts/*.sh
./scripts/bootstrap-macos.sh --install-missing-dependencies --configure-all-mcp
```

Valide:

```bash
./scripts/verify-profiles-macos.sh
```

Depois abra **WhatsApp MCP Tray.app** na Mesa/Desktop. O arquivo `.command` tambem existe como fallback tecnico. Veja [docs/10-macos.md](docs/10-macos.md).

## Primeiro Uso

1. Ao abrir o painel pela primeira vez, escolha a pasta geral onde as bases ficarao salvas.
2. Clique em **Cadastrar primeiro perfil**.
3. Informe o projeto, nome do perfil e descricao. O numero e opcional; se ficar vazio, o QR pode identificar depois.
4. Clique em **Conectar QR**.
5. Escaneie o QR no WhatsApp do celular.
6. Depois de autenticar, a janela volta ao painel automaticamente; se quiser, clique em **Voltar ao painel**.
7. Pode ocultar na bandeja. A sincronizacao continua em background.

Se o perfil ja estiver autenticado, **Conectar QR** nao gera outro QR: o painel avisa que a sessao ja existe e, se a bridge estiver fechada, inicia uma sincronizacao manual.

Estrutura padrao da base:

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
```

## Como A Sincronizacao Funciona

Na primeira autenticacao de cada perfil, o painel inicia uma **primeira sync inteligente**.

Por padrao, ela:

- roda por no minimo 10 minutos;
- pode ficar aberta por ate 24 horas;
- fecha antes das 24 horas se a ultima mensagem local estiver perto do horario atual e o ritmo de importacao cair por tempo suficiente;
- depois agenda sincronizacoes random.

Depois da primeira sincronizacao, cada perfil abre a porta local somente durante janelas de sync manual ou random. Fora dessas janelas, Codex/Claude ainda conseguem pesquisar o `messages.db` local via MCP.

Quando o painel inicia com o Windows ou e aberto depois de ficar encerrado, ele agenda uma **sync de retomada** para perfis autenticados. Os perfis sao escalonados, por padrao um a cada 2 minutos, para atualizar a base sem abrir todas as bridges ao mesmo tempo.

Pausa manual e respeitada depois de reiniciar. Fechar o sistema ou reiniciar o computador apenas para os processos; no proximo login, perfis autenticados que ainda precisam sincronizar retomam normalmente.

Downloads de midia fisica ainda exigem a bridge do perfil aberta, porque o arquivo precisa ser baixado pelo WhatsApp Web.

## Remover Um Numero

Selecione o perfil no painel e clique em **Remover perfil**.

O painel oferece duas opcoes:

- **Remover so do painel**: tira o perfil da lista e do MCP, mas preserva `whatsapp.db`, `messages.db`, logs e midias na pasta local.
- **Apagar perfil e dados locais**: fecha a bridge e apaga a pasta do perfil, incluindo sessoes, mensagens, logs e arquivos baixados.

Por seguranca, o painel so apaga automaticamente pastas dentro da pasta geral configurada no sistema.

## Se Um QR Vazar

O QR de pareamento e temporario e normalmente perde valor depois que expira ou depois que a sessao e autenticada. Mesmo assim, se alguem escanear o QR antes de voce, essa pessoa pode vincular um aparelho.

Se houver duvida:

1. Abra o WhatsApp no celular.
2. Va em **Aparelhos conectados**.
3. Remova qualquer aparelho desconhecido.
4. Se quiser refazer do zero neste kit, remova esse aparelho tambem e apague apenas o `whatsapp.db` do perfil, preservando `messages.db`.

## Usar Com Codex Ou Claude

Depois do bootstrap com `-ConfigureAllMcp`, o servidor MCP se chama:

```text
whatsapp-profiles
```

Ferramentas principais:

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
Liste os perfis de WhatsApp disponiveis e diga quais ja tem base local.
```

```text
Pesquise "orcamento" em todos os perfis e agrupe por projeto e vendedor.
```

```text
No perfil vendedor-joao, liste PDFs, imagens, audios e links do telefone +55 (11) 91234-5678.
```

## Documentacao

- [COMECE_AQUI.md](COMECE_AQUI.md): roteiro didatico para usuario e IA instalarem.
- [PROMPT-CODEX.md](PROMPT-CODEX.md): prompt pronto para colar no Codex/Claude.
- [docs/00-o-que-e-automatico.md](docs/00-o-que-e-automatico.md): o que o instalador faz e o que depende do usuario.
- [docs/02-antivirus.md](docs/02-antivirus.md): excecoes recomendadas e quarentena.
- [docs/03-mcp-codex-claude.md](docs/03-mcp-codex-claude.md): configuracao MCP.
- [docs/04-seguranca.md](docs/04-seguranca.md): privacidade e exposicao local.
- [docs/05-troubleshooting.md](docs/05-troubleshooting.md): erros comuns.
- [docs/10-macos.md](docs/10-macos.md): instalacao e limites no MacBook/macOS.
- [docs/12-perfis-multiplos.md](docs/12-perfis-multiplos.md): detalhes do modo perfis.

## Licenca E Origem

Partes da bridge sao vendorizadas de `lharries/whatsapp-mcp` sob MIT. Veja [NOTICE](NOTICE) e [docs/08-vendor-e-licenca.md](docs/08-vendor-e-licenca.md).
