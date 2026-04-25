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
```

Tambem nao desative o antivirus inteiro. A liberacao deve ser pontual.

## Excecoes Recomendadas No Windows

Adapte `SEU_USUARIO` e o caminho real onde voce clonou o repositorio.

```text
C:\Users\SEU_USUARIO\Documents\whatsapp-mcp-local-kit
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Profiles
```

Se o repositorio foi clonado em outra pasta, libere essa pasta real do clone. Exemplo:

```text
C:\Users\SEU_USUARIO\Downloads\whatsapp-mcp-local-kit
```

Se o antivirus bloquear o auto-start, libere tambem a pasta Startup do proprio usuario:

```text
C:\Users\SEU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

Essa excecao serve apenas para permitir o atalho `WhatsApp MCP Tray.lnk` criado pelo instalador.

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
~/whatsapp-mcp-local-kit
~/Documents/WhatsApp MCP Panel
~/Documents/WhatsApp MCP Profiles
```

Em Mac corporativo, a liberacao pode depender do administrador de TI.
