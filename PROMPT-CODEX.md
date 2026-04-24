# Prompt pronto para colar no Codex

Use este prompt em uma conversa nova do Codex no computador Windows onde a bridge vai rodar.

```text
Quero instalar e configurar o WhatsApp MCP Local Kit neste Windows.

Objetivo:
- Rodar uma bridge local do WhatsApp baseada em lharries/whatsapp-mcp.
- Criar um painel de bandeja com sincronizacao manual e random.
- Configurar uso com Codex e/ou Claude Desktop.
- Fazer tudo sem publicar conversas, sessoes, QR Codes ou bancos .db.

Regras obrigatorias:
- Comece pelo diagnostico. Nao apague, substitua ou mova arquivos antes de mostrar o estado encontrado.
- Se existir whatsapp.db ou messages.db, faca backup antes de qualquer reinstalacao.
- Nao crie excecao global para powershell.exe, cmd.exe, wscript.exe, python.exe ou go.exe.
- Para antivirus, apenas me diga exatamente quais pastas/arquivos liberar e espere eu confirmar que fiz.
- Se algum antivirus colocar arquivo em quarentena, pare e me oriente a restaurar somente se o caminho estiver dentro das pastas esperadas.
- Operacoes de envio de mensagem no WhatsApp precisam de confirmacao explicita.
- Prefira bridge acessivel apenas em 127.0.0.1.
- Ao final, valide com operacoes read-only.

Passos esperados:
1. Ler README.md e docs/.
2. Verificar Go, Python, uv, Git e GCC/MSYS2.
3. Verificar se lharries/whatsapp-mcp ja existe.
4. Preservar store/whatsapp.db e store/messages.db.
5. Compilar a bridge em build-tmp/whatsapp-bridge.exe.
6. Instalar o painel com scripts/install-panel.ps1.
7. Confirmar que o atalho WhatsApp MCP Tray abre sem janela preta.
8. Confirmar que o painel fica na bandeja e registra ultima sincronizacao.
9. Me entregar um resumo com os caminhos criados, o que ficou no auto-start e como pausar.
```

