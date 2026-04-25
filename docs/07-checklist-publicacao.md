# 07 - Checklist Antes De Publicar

Antes de fazer push para GitHub:

```powershell
git status --short
git diff --check
python -m py_compile panel\whatsapp_profiles_panel.py panel\launch_panel.py panel\tray_agent.py profiles-mcp-server\main.py
```

Procure dados sensiveis:

```powershell
Get-ChildItem -Recurse -File | Select-String -Pattern "whatsapp.db","messages.db","QR_CODE_DATA","BEGIN","token","secret"
```

Pode aparecer `whatsapp.db` e `messages.db` apenas em documentacao, como aviso. Nao pode existir arquivo `.db` real no status do Git.

Confirme tambem:

- `.gitignore` esta presente.
- Nao existe pasta `store/` versionada.
- Nao existe pasta `.venv/` versionada.
- Nao existe pasta `WhatsApp MCP Profiles/` versionada.
- Nao existe log da bridge versionado.
- Nao existe print de QR Code.
- Nao existe `panel_config.json` local versionado.
- Nao existe `profiles.json` real versionado.

Sugestao de descricao para o GitHub:

```text
Local Windows tray kit for running an unofficial WhatsApp MCP bridge with multiple local profiles, project-separated SQLite databases, and Codex/Claude MCP search.
```
