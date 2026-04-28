# 02 - Antivirus

Antivirus pode bloquear este tipo de ferramenta porque ela compila um binario local, roda em background, cria atalhos, usa Python/uv e abre uma bridge local para conversar com WhatsApp Web.

O kit **nao** tenta configurar excecoes automaticamente. Cada antivirus muda a interface, entao o caminho seguro e liberar apenas os caminhos do kit, do painel e das bases locais.

## Nao Libere Globalmente

Nao crie excecao geral para:

```text
powershell.exe
cmd.exe
wscript.exe
python.exe
pythonw.exe
go.exe
gcc.exe
bash
go
launchctl
```

Tambem nao desative o antivirus inteiro. A liberacao deve ser pontual.

## Excecoes Recomendadas No Windows

Adapte `SEU_USUARIO` e o caminho real onde voce clonou o repositorio.

```text
C:\CAMINHO\ONDE\CLONOU\whatsapp-mcp-local-kit
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles
```

Essas tres excecoes sao as principais:

- **Repositorio clonado**: contem scripts, codigo do painel, MCP e codigo da bridge usada no build.
- **WhatsApp MCP Panel**: contem o painel instalado, icones, launcher, ambiente Python local e logs do painel.
- **WhatsApp MCP Profiles**: contem `whatsapp-bridge.exe`, projetos, perfis, sessoes `whatsapp.db` e bases `messages.db`.

Se o repositorio foi clonado em outra pasta, libere a pasta real do clone. Exemplos:

```text
C:\Users\SEU_USUARIO\Downloads\whatsapp-mcp-local-kit
C:\Users\SEU_USUARIO\Documents\New project 2\whatsapp-mcp-local-kit
```

Se o antivirus bloquear o auto-start, prefira liberar apenas o atalho correto:

```text
C:\Users\SEU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\WhatsApp MCP Tray.lnk
```

Evite liberar a pasta Startup inteira se o antivirus permitir excecao por arquivo.

Se mesmo assim o instalador receber **Acesso negado** ao criar o auto-start, ele tenta usar o fallback padrao do Windows para o usuario atual:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WhatsApp MCP Tray
```

Esse fallback aponta para `pythonw.exe` + `launch_panel.py --minimized` e nao exige administrador.

Se quiser reparar isso manualmente pelo repo:

```powershell
python scripts\repair-shortcuts.py --registry-only
```

Se preferir a pasta Startup, crie o atalho manualmente pelo Explorer:

1. Abra `shell:startup` no Executar do Windows.
2. Copie `WhatsApp MCP Tray.lnk` da Area de Trabalho para essa pasta.
3. Remova de `shell:startup` atalhos antigos como `WhatsApp MCP Painel.lnk` ou `WhatsApp MCP Bridge.vbs`.

## Excecoes Antigas Que Nao Devem Ser Necessarias

Se voce veio de uma instalacao antiga, pode encontrar excecoes para:

```text
C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp
C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp\whatsapp-mcp
C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp\whatsapp-mcp\build-tmp\whatsapp-bridge.exe
```

Essas pastas pertencem ao fluxo legado. Para o modo perfis atual, o normal e usar:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles
```

Remova excecoes antigas somente depois de confirmar que o Startup do Windows nao contem mais `WhatsApp MCP Bridge.vbs` nem `WhatsApp MCP Painel.lnk`.

## Arquivos Que Podem Gerar Alerta

Alertas mais comuns:

```text
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles\bin\whatsapp-bridge.exe
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\launch_panel.py
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\whatsapp_profiles_panel.py
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel\.venv-user\Scripts\pythonw.exe
```

Durante build ou instalacao, tambem podem aparecer:

```text
C:\Program Files\Go\bin\go.exe
C:\msys64\ucrt64\bin\gcc.exe
C:\Users\SEU_USUARIO\AppData\Roaming\uv\uv.exe
```

Mesmo assim, prefira liberar a **pasta do projeto/painel/base**, nao o interpretador inteiro.

## Precisa Mexer No Antivirus Todo Dia?

Normalmente nao. As excecoes sao feitas **uma vez na instalacao**.

Voce pode precisar revisar excecoes se:

- mudar a pasta geral das bases no painel;
- clonar o repositorio em outro lugar;
- reinstalar o painel em outra pasta;
- recompilar a bridge e o antivirus tratar o binario novo como suspeito;
- o antivirus colocar `whatsapp-bridge.exe` ou arquivos do painel em quarentena;
- o auto-start for bloqueado depois de uma atualizacao do Windows ou do antivirus.

No uso diario, depois de configurado, nao deveria ser necessario mexer no antivirus.

## Por Que PowerShell Pode Ser Bloqueado

Os scripts usam PowerShell para:

- verificar dependencias;
- compilar a bridge;
- copiar arquivos do painel;
- criar atalho no Desktop;
- criar atalho de auto-start;
- configurar arquivos MCP.

Alguns antivirus classificam linhas de comando com build, atalho e processo em background como suspeitas. Isso nao significa automaticamente que o arquivo e malicioso, mas tambem nao e motivo para liberar PowerShell globalmente.

Se aparecer alerta de linha de comando, confira se o caminho pertence a este repositorio, ao painel ou a pasta de bases. Se apontar para outro local, nao libere.

## Quarentena

Se um arquivo cair em quarentena:

1. Abra a area de quarentena/historico do antivirus.
2. Confira o caminho completo do arquivo.
3. Restaure apenas se ele estiver dentro das pastas esperadas:

```text
...\whatsapp-mcp-local-kit\
...\Documents\WhatsApp MCP Panel\
...\Documents\WhatsApp MCP Profiles\
```

4. Depois de restaurar, adicione a excecao da pasta.
5. Rode a validacao:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
```

## Bitdefender

No Bitdefender, procure por nomes parecidos com:

```text
Protecao
Antivirus
Defesa contra Ameacas
Configuracoes
Excecoes
Quarentena
Gerenciar excecoes
```

Inclua as pastas recomendadas. Quando ele perguntar o tipo de protecao, marque Antivirus/Defesa contra Ameacas para essas pastas.

## Windows Defender

No Windows Defender, procure por:

```text
Seguranca do Windows
Protecao contra virus e ameacas
Gerenciar configuracoes
Exclusoes
Adicionar ou remover exclusoes
```

Use exclusao por pasta para o clone, painel e bases.

## macOS

No macOS, nao desative Gatekeeper, XProtect, Defender for Endpoint, CrowdStrike, SentinelOne ou outro EDR globalmente.

Se precisar liberar excecoes, prefira apenas:

```text
<pasta real onde voce clonou o repositorio>
~/Documents/WhatsApp MCP Panel
~/Documents/WhatsApp MCP Profiles
~/Library/LaunchAgents/com.whatsapp-mcp.tray.plist
```

Em Mac corporativo, a liberacao pode depender do administrador de TI.
