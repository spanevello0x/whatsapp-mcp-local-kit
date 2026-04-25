# 11 - Escopo estavel

Este documento congela o escopo operacional atual do kit. Ideias como multiplos perfis de vendedores, exportador automatico de clientes, download em lote e transcricao de audios ficam como backlog e nao fazem parte do fluxo estavel por enquanto.

## Incluido na versao estavel

- Instalar a bridge vendorizada em uma pasta local.
- Compilar a bridge Go.
- Instalar painel local em Python/Tkinter.
- Criar atalho no Desktop e auto-start do painel.
- Rodar sincronizacao em rajadas ou sob demanda.
- Manter a porta local aberta apenas durante sincronizacao, envio ou download de midia.
- Consultar mensagens locais via MCP.
- Listar arquivos e links ja registrados na base com `list_chat_assets`.
- Abrir a pasta do `messages.db` pelo painel.
- Copiar o caminho do `messages.db` pelo painel.
- Configurar MCP no Codex e/ou Claude Desktop.
- Verificar a instalacao com `scripts/verify-local.ps1` ou `scripts/verify-local-macos.sh`.

## Fora do escopo por enquanto

- Varios WhatsApps simultaneos na mesma maquina.
- Perfis separados por vendedor.
- CRM/exportador automatico de clientes.
- Download automatico em lote de PDFs, imagens, videos ou audios.
- Transcricao automatica de audios.
- Painel para revisar leads, funil ou status comercial.
- Instalador assinado.
- App nativo empacotado.

## Contrato operacional

O `messages.db` e a fonte local de consulta. Claude/Codex podem pesquisar a base com a porta fechada.

A bridge precisa abrir a porta `127.0.0.1:8080` para:

- sincronizar mensagens novas;
- enviar mensagem;
- enviar arquivo;
- baixar midia fisica com `download_media`.

## Criterios de estabilidade

Antes de publicar mudancas, valide:

```powershell
python -m py_compile panel\whatsapp_mcp_panel.py panel\launch_panel.py vendor\lharries-whatsapp-mcp\whatsapp-mcp-server\whatsapp.py vendor\lharries-whatsapp-mcp\whatsapp-mcp-server\main.py
git diff --check
git status --short
```

Tambem confira que nenhum `.db`, log, print de QR, backup ou credencial entrou no Git.
