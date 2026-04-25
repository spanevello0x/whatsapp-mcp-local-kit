# Comece Aqui

Este arquivo existe para o usuario copiar o repositorio em uma IA, como Codex ou Claude, e pedir a instalacao completa sem precisar conhecer os detalhes tecnicos.

## Antes De Rodar

1. Confirme que voce esta em um computador onde pode instalar dependencias.
2. Leia ou peca para a IA ler `docs/02-antivirus.md`.
3. Crie excecoes pontuais no antivirus antes de compilar ou iniciar o painel.
4. Nao desative o antivirus inteiro.
5. Nao libere `powershell.exe`, `cmd.exe`, `python.exe`, `go.exe` ou `wscript.exe` globalmente.

Excecoes principais no Windows:

```text
C:\Users\SEU_USUARIO\Documents\whatsapp-mcp-local-kit
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles
```

Se o repositorio for clonado em outro local, libere a pasta real do clone.

## Prompt Para Colar Na IA

Cole o texto abaixo em uma conversa nova do Codex ou Claude com acesso ao computador.

```text
Quero instalar o WhatsApp MCP Local Kit neste computador usando este repositorio.

Objetivo:
- Instalar o modo perfis como fluxo principal.
- Criar o painel local com icone no Desktop e bandeja.
- Permitir cadastrar varios numeros de WhatsApp separados por projeto.
- Cada perfil precisa ter sessao, porta, logs e messages.db proprios.
- Configurar o MCP whatsapp-profiles para Codex e/ou Claude Desktop.
- Nao publicar conversas, sessoes, QR Codes, bancos .db, logs ou tokens.

Regras obrigatorias:
- Comece lendo README.md, COMECE_AQUI.md e docs/02-antivirus.md.
- Diagnostique antes de alterar: sistema operacional, git, python, uv, go, gcc/msys2 e pastas existentes.
- Antes de instalar dependencias, criar atalhos, configurar MCP ou rodar build, explique o que sera feito e por que.
- Se existir whatsapp.db ou messages.db, faca backup antes de qualquer reinstalacao.
- Nao apague bancos .db sem minha confirmacao explicita.
- Nao crie excecao global para powershell.exe, cmd.exe, wscript.exe, python.exe ou go.exe.
- Para antivirus, informe exatamente quais pastas/arquivos liberar e espere eu confirmar.
- Se o antivirus colocar algo em quarentena, oriente restaurar somente se o caminho estiver dentro das pastas esperadas.
- Operacoes de envio de mensagem precisam de confirmacao explicita.
- A bridge deve escutar apenas em 127.0.0.1.
- Ao final, valide com operacoes read-only.

Comando esperado no Windows, depois do diagnostico e das excecoes:
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp

Se faltarem dependencias e eu autorizar instalar via winget:
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp -InstallMissingDependencies

Validacao final:
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1

Depois da instalacao:
- Abra o icone WhatsApp MCP Tray.
- Na primeira abertura, escolha a pasta geral das bases.
- Cadastre o primeiro perfil com projeto, nome e descricao.
- Clique em Conectar QR somente no perfil desejado.
- Depois de autenticar, clique em Voltar ao painel.
- Confirme que o painel mostra status, mensagens, porta e proxima acao.
- Confirme que o auto-start esta ativo ou mostre como ativar no painel.

No resumo final, informe:
- caminho do repositorio;
- caminho do painel instalado;
- caminho da pasta geral das bases;
- caminho do profiles.json;
- nome do MCP configurado;
- como pausar, sincronizar, remover perfil e abrir a pasta do projeto.
```

## Fluxo Para Usuario Leigo

Depois de instalado:

1. Abra **WhatsApp MCP Tray**.
2. Escolha a pasta geral das bases.
3. Clique em **Cadastrar primeiro perfil**.
4. Crie ou escolha um projeto.
5. Preencha nome e descricao do perfil.
6. Clique em **Conectar QR**.
7. Escaneie no WhatsApp.
8. Clique em **Voltar ao painel**.
9. Deixe rodando ou clique em **Ocultar na bandeja**.

Para adicionar outro numero, clique em **Adicionar outro perfil** e repita.

Para remover um numero, selecione o perfil e clique em **Remover perfil**. Escolha entre preservar os dados ou apagar a pasta do perfil.

## Onde Ficam Os Dados

Por padrao:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles
```

Dentro dela:

```text
projetos\NOME_DO_PROJETO\SLUG_DO_PERFIL\whatsapp-bridge\store\messages.db
projetos\NOME_DO_PROJETO\SLUG_DO_PERFIL\whatsapp-bridge\store\whatsapp.db
```

`messages.db` e a base de pesquisa. `whatsapp.db` e a sessao autenticada. Nao publique esses arquivos.
