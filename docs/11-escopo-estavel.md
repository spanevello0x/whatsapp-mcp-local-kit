# 11 - Escopo Estavel

Este documento congela o escopo operacional atual do kit.

O fluxo estavel atual e o **modo perfis**: varios numeros de WhatsApp na mesma maquina, separados por projeto, com uma base SQLite local por perfil.

## Incluido Na Versao Estavel

- Instalar a bridge vendorizada.
- Compilar a bridge Go compartilhada.
- Instalar painel local em Python/Tkinter.
- Criar icone no Desktop.
- Criar auto-start do painel na bandeja.
- Escolher uma pasta geral para todas as bases.
- Criar projetos e perfis pelo painel.
- Abrir QR somente sob demanda, por perfil.
- Identificar numero pelo QR quando a bridge retorna o JID do WhatsApp.
- Sincronizar varios perfis, cada um com porta local propria.
- Primeira sincronizacao inteligente por perfil.
- Sincronizacao manual e random por perfil.
- Manter a porta local aberta apenas durante QR, sync, envio ou download de midia.
- Consultar mensagens locais via MCP `whatsapp-profiles`.
- Listar arquivos e links por perfil ou em todos os perfis.
- Abrir pasta do projeto pelo painel.
- Copiar caminho do `messages.db` pelo painel.
- Remover perfil preservando dados.
- Remover perfil apagando dados locais, com confirmacao.
- Configurar MCP no Codex e/ou Claude Desktop.
- Verificar a instalacao com `scripts/verify-profiles.ps1`.

## Fora Do Escopo Por Enquanto

- Instalador `.exe` assinado.
- App nativo empacotado.
- Envio de mensagens por perfil via MCP de perfis.
- CRM visual dentro do painel.
- Exportador automatico de clientes pronto.
- Download automatico em lote de todas as midias.
- Transcricao automatica de audios.
- Garantia oficial de compatibilidade com WhatsApp Web.

Esses itens podem virar features futuras, mas nao sao necessarios para o objetivo principal: manter bases locais pesquisaveis por IA.

## Contrato Operacional

`messages.db` e a fonte local de consulta.

Codex/Claude podem pesquisar a base com a porta fechada, desde que o MCP esteja configurado e o perfil ainda exista no painel.

A bridge precisa abrir a porta local do perfil para:

- escanear QR;
- sincronizar mensagens novas;
- enviar mensagem, se alguma tool futura expuser isso;
- baixar midia fisica com `download_profile_media`.

Cada perfil usa:

- porta propria;
- `whatsapp.db` proprio;
- `messages.db` proprio;
- logs proprios;
- pasta propria.

## Criterios De Estabilidade

Antes de publicar mudancas, valide:

```powershell
python -m py_compile panel\whatsapp_profiles_panel.py panel\launch_panel.py panel\tray_agent.py profiles-mcp-server\main.py
git diff --check
git status --short
```

Tambem confira que nenhum `.db`, log, print de QR, backup ou credencial entrou no Git.
