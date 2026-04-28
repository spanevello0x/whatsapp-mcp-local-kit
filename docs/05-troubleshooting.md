# 05 - Troubleshooting

## Validacao Geral

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
```

No macOS:

```bash
./scripts/verify-profiles-macos.sh
```

Esse verificador confere painel, atalhos, auto-start, bridge de perfis, config MCP e bases locais.

## `spawn uv ENOENT`

O cliente tentou chamar `uv`, mas o processo nao encontrou no PATH.

No modo perfis, o MCP normalmente usa o Python do painel, entao esse erro costuma indicar uma configuracao antiga do MCP legado. Rode:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-profiles-mcp.ps1 -All
```

Depois feche e abra Codex/Claude Desktop.

## Janela Preta

O atalho correto deve apontar para um `pythonw.exe`, nao para `python.exe`, `powershell.exe` ou `.bat`.

Destino esperado:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\.venv-user\Scripts\pythonw.exe
```

Argumento esperado:

```text
"C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\launch_panel.py" --minimized
```

Se existir um atalho antigo `WhatsApp MCP Painel.lnk`, prefira `WhatsApp MCP Tray.lnk`.

No macOS, prefira `~/Desktop/WhatsApp MCP Tray.app`, que abre sem Terminal. O arquivo `~/Desktop/WhatsApp MCP Tray.command` fica como fallback tecnico e chama `~/Documents/WhatsApp MCP Panel/.venv/bin/python` com `launch_panel.py`.

## Bandeja Nao Abre O Painel

1. Tente abrir novamente pelo icone do Desktop.
2. Rode `verify-profiles.ps1`.
3. Confira `Documents\WhatsApp MCP Panel\panel-actions.log`.
4. Se o antivirus bloqueou scripts ou atalhos, siga `docs/02-antivirus.md` e reinstale o painel:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-panel.ps1 -ProfilesMode
```

No macOS:

```bash
./scripts/install-panel-macos.sh --profiles-mode
```

## Auto-start Pendente

No Windows, o auto-start padrao do kit e o Registro do usuario:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WhatsApp MCP Tray
```

Isso abre `launch_panel.py --minimized` com `pythonw.exe`, sem janela preta e sem depender da pasta Startup.

Se o verificador mostrar Registro ausente ou apontando para caminho antigo:

1. Libere no antivirus as pastas principais:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles
<pasta real do repositorio clonado>
```

2. Reinstale o painel:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-panel.ps1 -ProfilesMode
```

3. Valide:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
```

Tambem e possivel ativar/desativar auto-start pelo botao **Configuracoes** no painel.

Se encontrar `WhatsApp MCP Painel.lnk`, `WhatsApp MCP Bridge.vbs` ou `WhatsApp MCP Tray.lnk` dentro de `shell:startup`, isso e legado/opcional. O padrao atual e o Registro; remova itens da pasta Startup depois de confirmar que o Tray atual inicia pelo Registro para evitar inicializacao duplicada.

### Se Quiser Usar Startup Como Alternativa

Alguns antivirus bloqueiam escrita automatica em:

```text
C:\Users\SEU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

Isso nao afeta o metodo padrao por Registro. Para reparar o auto-start padrao:

```powershell
python scripts\repair-shortcuts.py --registry-only
```

Se preferir usar a pasta Startup mesmo assim, faca pelo Explorer:

1. Abra a pasta Startup digitando `shell:startup` no Executar do Windows.
2. Copie o atalho `WhatsApp MCP Tray.lnk` da Area de Trabalho para essa pasta.
3. Se existirem `WhatsApp MCP Painel.lnk` ou `WhatsApp MCP Bridge.vbs`, mova para fora da pasta Startup.
4. Se o antivirus perguntar, libere apenas o arquivo `WhatsApp MCP Tray.lnk`, nao o PowerShell inteiro.

Estado esperado no Startup, se esse metodo for usado:

```text
WhatsApp MCP Tray.lnk
```

Estado esperado no Registro, no metodo padrao:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WhatsApp MCP Tray
```

No macOS, o auto-start fica em:

```text
~/Library/LaunchAgents/com.whatsapp-mcp.tray.plist
```

## QR Nao Aparece

- Selecione o perfil correto.
- Clique em **Conectar QR**.
- Se a janela ja estava escondida, o botao deve traze-la de volta.
- Se o perfil ja estiver autenticado, o painel avisa que nao precisa reconectar. Se a bridge estiver fechada, ele inicia uma sync manual.
- Se quiser refazer login, remova o aparelho conectado no WhatsApp do celular e apague somente `whatsapp.db` daquele perfil, preservando `messages.db`.

## Pasta Geral Apareceu De Novo

O painel so deveria pedir a pasta geral no primeiro uso real. Se isso aparecer apos uma atualizacao ou reinicio, normalmente o `panel_config.json` foi recriado sem o marcador `profiles_base_confirmed`.

Versoes novas preservam esse marcador e tambem reconhecem uma instalacao existente quando `profiles.json` ja tem projetos ou perfis.

## Perfil Esta Sincronizando Mas Nao "Termina"

Na primeira sync, o painel usa heuristica:

- tempo minimo;
- horario da ultima mensagem local;
- ritmo de crescimento da base;
- tempo estabilizado;
- limite maximo.

Em contas com muito movimento, ele pode ficar aberto mais tempo para evitar fechar cedo. Depois que estabiliza, entra em modo random.

## Conferir Banco De Um Perfil

No painel, selecione o perfil e clique em **Copiar DB**. Depois, em PowerShell:

```powershell
python -c "import sqlite3, sys; db=sys.argv[1]; c=sqlite3.connect(db); print(c.execute('select count(*) from messages').fetchone()[0]); print(c.execute('select max(timestamp) from messages').fetchone()[0])" "COLE_AQUI_O_CAMINHO_DO_MESSAGES_DB"
```

## `no sender key`

Pode acontecer em mensagens de grupos durante sync parcial. Normal em bridges baseadas em WhatsApp Web.

## `gcc: executable file not found`

A bridge usa SQLite com CGO. No Windows, isso precisa de compilador C.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-dependencies.ps1 -UseWinget -InstallMsys2
```

Depois feche e reabra o terminal.

## Remover Perfil

Use **Remover perfil** no painel.

- Se escolher **Remover so do painel**, a pasta e os bancos ficam preservados.
- Se escolher **Apagar perfil e dados locais**, o painel fecha a bridge e remove a pasta do perfil.

Se a exclusao falhar, normalmente algum processo ainda esta segurando log ou banco. Aguarde alguns segundos, valide os processos e tente de novo.
