# WhatsApp MCP Local Kit

Kit em portugues para rodar uma bridge local do WhatsApp com MCP, painel de bandeja no Windows e guias para usar com Codex ou Claude Desktop.

Este repositorio nao inclui mensagens, sessoes, bancos SQLite, QR Codes ou credenciais. Ele e um wrapper/documentacao em cima do projeto open-source [`lharries/whatsapp-mcp`](https://github.com/lharries/whatsapp-mcp).

## O que este kit entrega

- Guia de preparacao no Windows.
- Checklist de antivirus sem liberar PowerShell globalmente.
- Painel local em Python/Tkinter para bandeja.
- Atalhos com `pythonw.exe`, sem janela preta.
- Modo de sincronizacao em rajadas: manual + janelas aleatorias.
- Guias para Claude Desktop e Codex.
- Checklist de seguranca para nao expor conversas.

## Fluxo recomendado

1. Leia `docs/01-preparacao-windows.md`.
2. Configure excecoes pontuais em `docs/02-antivirus.md`.
3. Clone o upstream `lharries/whatsapp-mcp`.
4. Compile a bridge com `scripts/build-bridge.ps1`.
5. Rode `scripts/verify-local.ps1`.
6. Rode `scripts/install-panel.ps1`.
7. Use o atalho `WhatsApp MCP Tray`.
8. Configure MCP com `docs/03-mcp-codex-claude.md`.

## Para usar com Codex

Abra `PROMPT-CODEX.md`, copie o prompt e cole em uma conversa do Codex com acesso ao seu Windows. O agente deve diagnosticar primeiro, pedir confirmacao antes de mexer em antivirus/quarentena e nunca apagar bancos `.db`.

## Aviso

`messages.db` contem conversas reais. Nunca publique `.db`, logs, backups de sessao ou tokens. Este repo ja vem com `.gitignore` agressivo para reduzir risco.

Este kit nao e oficial da Meta/WhatsApp e pode quebrar se o protocolo do WhatsApp Web mudar. Para uso comercial critico, avalie tambem a WhatsApp Business Platform oficial.
