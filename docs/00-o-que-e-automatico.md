# 00 - O Que E Automatico

Este kit tenta deixar a instalacao o mais proxima possivel de copia/cola, mas algumas partes sempre dependem do computador, do antivirus e da conta de WhatsApp da pessoa.

O fluxo principal de producao e o **modo perfis**. Ele permite cadastrar varios numeros, separados por projeto, cada um com base local propria.

## O Que O Bootstrap Pode Fazer

- Verificar se Git, Go, Python, uv e GCC/MSYS2 existem.
- Tentar instalar dependencias faltantes via `winget`, se voce usar `-InstallMissingDependencies`.
- Compilar a bridge Go vendorizada.
- Instalar o painel em `Documents\WhatsApp MCP Panel`.
- Criar icone no Desktop.
- Criar auto-start para abrir o painel minimizado na bandeja.
- Criar a pasta geral das bases, por padrao `Documents\WhatsApp MCP Profiles`.
- Instalar a bridge compartilhada em `Documents\WhatsApp MCP Profiles\bin`.
- Registrar o MCP `whatsapp-profiles` no Codex e/ou Claude Desktop, se voce usar `-ConfigureAllMcp`.
- Validar a instalacao com `scripts/verify-profiles.ps1`.

## O Que Nao Pode Vir Pronto No GitHub

- Sessao do WhatsApp.
- QR Code autenticado.
- Historico de mensagens.
- `whatsapp.db`.
- `messages.db`.
- Excecoes de antivirus aplicadas automaticamente.
- Permissao para enviar mensagens.
- Credenciais do Codex, Claude ou GitHub.

Cada usuario precisa escanear o QR no proprio WhatsApp e decidir quais pastas liberar no proprio antivirus.

## Resultado Esperado

Depois do bootstrap:

- O icone **WhatsApp MCP Tray** aparece na area de trabalho.
- O painel abre sem janela preta permanente.
- O painel pode ficar minimizado na bandeja.
- O usuario escolhe uma pasta geral para as bases.
- Cada perfil fica em uma pasta separada por projeto.
- Cada perfil tem sessao e `messages.db` proprios.
- A bridge abre porta local apenas para sincronizar, autenticar ou baixar midia.
- Codex/Claude Desktop podem consultar a base via MCP depois de configurados.

## Comando Principal

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp
```

Com instalacao de dependencias via `winget`, se o usuario autorizar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp -InstallMissingDependencies
```
