# 07 - Checklist antes de publicar

Antes de fazer push para GitHub:

```powershell
rg -n "NOME_REAL|EMPRESA_REAL|TELEFONE_REAL|whatsapp.db|messages.db|bridge.log|QR|token|secret" .
git status --short
```

Pode aparecer `whatsapp.db` e `messages.db` apenas em documentacao, como aviso. Nao pode existir arquivo `.db` real no status do Git.

Confirme tambem:

- `.gitignore` esta presente.
- Nao existe pasta `store/`.
- Nao existe pasta `.venv/`.
- Nao existe log da bridge.
- Nao existe print de QR Code.

Sugestao de descricao para o GitHub:

```text
Local tray/menu bar kit and docs for running an unofficial WhatsApp MCP bridge safely with Codex or Claude Desktop on Windows and macOS.
```
