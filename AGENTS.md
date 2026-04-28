# AGENTS.md

Instrucoes para Codex, Claude Code, Claude Desktop ou outro agente instalarem este repositorio com seguranca.

## Leitura Obrigatoria

Antes de executar scripts, leia:

1. `README.md`
2. `COMECE_AQUI.md`
3. `docs/00-o-que-e-automatico.md`
4. `docs/02-antivirus.md`
5. `docs/12-perfis-multiplos.md`

Este arquivo orienta o agente. O README orienta o usuario. Se houver divergencia, preserve dados do usuario e pare para explicar.

## Objetivo Do Repositorio

Instalar o WhatsApp MCP Local Kit em modo perfis:

- varios numeros de WhatsApp na mesma maquina;
- bases separadas por projeto e perfil;
- painel local com icone, bandeja/menu bar e auto-start;
- MCP `whatsapp-profiles` para Codex/Claude pesquisarem mensagens, arquivos e links;
- bridge limitada a `127.0.0.1`.

O repositorio nao deve conter mensagens, bancos `.db`, sessoes, logs reais, QR Codes, tokens ou credenciais.

## Escolha Do Sistema Operacional

Use um unico codigo, mas fluxos de instalacao separados:

- Windows: `scripts/bootstrap-windows.ps1`
- macOS: `scripts/bootstrap-macos.sh`

Nao rode o script de Windows no macOS nem o script de macOS no Windows. Primeiro diagnostique o sistema, depois escolha o script correto.

## Regras De Seguranca

- Nao apague `whatsapp.db`, `messages.db`, logs ou pastas de perfil sem confirmacao explicita do usuario.
- Se existir banco ou sessao antiga, faca backup antes de reinstalar ou migrar.
- Nao crie excecao global para `powershell.exe`, `cmd.exe`, `wscript.exe`, `python.exe`, `bash`, `go`, `launchctl` ou runtimes inteiros.
- Explique excecoes pontuais de antivirus/EDR antes de compilar ou iniciar o painel.
- Restaure item de quarentena somente se o caminho estiver dentro das pastas esperadas do kit.
- Envio de mensagem WhatsApp exige confirmacao explicita do usuario.
- Prefira comandos simples e auditaveis. Evite comandos longos que criem atalho, matem processo e baixem arquivo na mesma linha.

## Excecoes Recomendadas

Windows:

```text
<pasta onde clonou>\whatsapp-mcp-local-kit
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles
```

macOS:

```text
<pasta onde clonou>/whatsapp-mcp-local-kit
~/Documents/WhatsApp MCP Panel
~/Documents/WhatsApp MCP Profiles
```

Normalmente isso e feito uma vez. Revise se o usuario mudar o local das bases, clonar em outro caminho, reinstalar o painel, recompilar a bridge ou se o antivirus/EDR colocar arquivos em quarentena.

## Fluxo Windows

Diagnostique Git, Python 3.11+, uv, Go e GCC/MSYS2. Depois, com o usuario ciente das excecoes:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp
```

Se faltarem dependencias e o usuario autorizar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp -InstallMissingDependencies
```

Validacao:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
```

O auto-start padrao no Windows usa:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WhatsApp MCP Tray
```

A pasta `shell:startup` e fallback/legado, nao o padrao.

## Fluxo macOS

Diagnostique Git, Python 3.11+ com Tkinter, uv, Go, Xcode Command Line Tools e clang. Depois:

```bash
chmod +x scripts/*.sh
./scripts/bootstrap-macos.sh --install-missing-dependencies --configure-all-mcp
```

Validacao:

```bash
./scripts/verify-profiles-macos.sh
```

O auto-start no macOS usa:

```text
~/Library/LaunchAgents/com.whatsapp-mcp.tray.plist
```

O usuario deve abrir `WhatsApp MCP Tray.app`; o `.command` e fallback tecnico.

## Comportamento Do Painel

- Na primeira abertura, o usuario escolhe a pasta geral das bases.
- Cada perfil pertence a um projeto.
- O numero e opcional no cadastro; o QR pode identificar pelo JID retornado pela bridge.
- Depois de autenticar, a primeira sync inteligente inicia automaticamente.
- Ao reiniciar ou abrir o painel depois de ficar encerrado, perfis autenticados voltam a sincronizar por padrao, mesmo que uma pausa antiga tenha ficado gravada.
- Com a porta fechada, o MCP ainda pesquisa o `messages.db`; a bridge so precisa abrir para QR, sync nova e download de midia fisica.
- Ao remover perfil, o usuario escolhe se preserva dados ou apaga a pasta local. Para apagar dados, o painel exige confirmacao extra.

## Entrega Final Ao Usuario

Ao concluir, informe:

- caminho do repositorio;
- caminho do painel instalado;
- caminho da pasta geral das bases;
- caminho de `profiles.json`;
- nome do MCP: `whatsapp-profiles`;
- status do auto-start;
- como abrir painel, cadastrar perfil, conectar QR, pausar, sincronizar, remover perfil, abrir pasta do projeto e copiar caminho do DB.
