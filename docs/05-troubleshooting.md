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

O argumento deve apontar para:

```text
"C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\launch_panel.py" --minimized
```

## Auto-start pendente

Se `verify-local.ps1` mostrar:

```text
PENDENTE: nenhum auto-start valido encontrado
```

ou:

```text
PENDENTE: fallback legado existe, mas ABRIR_WHATSAPP_MCP.bat esta desatualizado
```

o Windows/antivirus provavelmente bloqueou escrita na pasta Startup ou no launcher `.bat`.

O painel ainda funciona pelo atalho da Area de Trabalho. Para auto-start, libere pontualmente no antivirus:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
C:\Users\SEU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

Depois rode:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-panel.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\verify-local.ps1
```

## Conferir banco

```powershell
python -c "import sqlite3, os; db=os.path.expandvars(r'%USERPROFILE%\CLAUDE COWORK\Whatsapp\whatsapp-mcp\whatsapp-bridge\store\messages.db'); c=sqlite3.connect(db); print(c.execute('select count(*) from messages').fetchone()[0]); print(c.execute('select max(timestamp) from messages').fetchone()[0])"
```

## `no sender key`

Pode acontecer em mensagens de grupos durante sync parcial. Normal em bridges baseadas em WhatsApp Web.

## `gcc: executable file not found`

A bridge usa SQLite com CGO. No Windows, isso precisa de compilador C.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-dependencies.ps1 -UseWinget -InstallMsys2
powershell -ExecutionPolicy Bypass -File .\scripts\build-bridge.ps1 -PatchLocalhost
```

Se acabou de instalar MSYS2/GCC, feche e reabra o terminal.

## Verificacao geral

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-local.ps1
```
