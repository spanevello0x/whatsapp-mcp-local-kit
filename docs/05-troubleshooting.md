# 05 - Troubleshooting

## `spawn uv ENOENT`

Use caminho absoluto para `uv.exe` e reinicie Claude/Codex:

```text
C:\Users\SEU_USUARIO\.local\bin\uv.exe
```

## Janela preta

Use atalho para:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\.venv\Scripts\pythonw.exe
```

## Conferir banco

```powershell
python -c "import sqlite3, os; db=os.path.expandvars(r'%USERPROFILE%\CLAUDE COWORK\Whatsapp\whatsapp-mcp\whatsapp-bridge\store\messages.db'); c=sqlite3.connect(db); print(c.execute('select count(*) from messages').fetchone()[0]); print(c.execute('select max(timestamp) from messages').fetchone()[0])"
```

## `no sender key`

Pode acontecer em mensagens de grupos durante sync parcial. Normal em bridges baseadas em WhatsApp Web.
