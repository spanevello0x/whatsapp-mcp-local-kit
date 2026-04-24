# 02 - Antivirus

Antivirus pode bloquear este tipo de ferramenta porque ela roda em background, cria atalhos, usa Python/uv e executa uma bridge local.

O kit nao tenta configurar excecoes automaticamente. Cada antivirus muda a interface, entao o caminho seguro e abrir a tela de protecao/quarentena do seu produto e liberar apenas os caminhos abaixo.

## Nao libere globalmente

Nao crie excecao geral para:

```text
powershell.exe
cmd.exe
wscript.exe
python.exe
go.exe
```

## Excecoes pontuais

Libere apenas estes caminhos, adaptando `SEU_USUARIO`:

```text
C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp\whatsapp-mcp
C:\Users\SEU_USUARIO\Documents\WhatsApp MCP Panel
C:\Users\SEU_USUARIO\.local\bin\uv.exe
C:\Users\SEU_USUARIO\CLAUDE COWORK\Whatsapp\whatsapp-mcp\build-tmp\whatsapp-bridge.exe
```

Se for compilar:

```text
C:\Program Files\Go\bin\go.exe
C:\msys64\ucrt64\bin\gcc.exe
```

## Como pensar em qualquer antivirus

Procure por nomes como:

```text
Excecoes
Itens permitidos
Lista branca
Permitir aplicativo
Quarentena
Historico de protecao
```

Se aparecer quarentena, restaure apenas arquivos dentro dessas pastas. Se o alerta apontar para outro local, nao restaure.

Se o antivirus reclamar de uma linha de comando, confira o comando inteiro. Linhas que param processos, compilam binarios ou criam atalhos podem parecer suspeitas mesmo quando sao esperadas. Ainda assim, prefira liberar caminho especifico, nao o interpretador inteiro.

## macOS

No macOS, nao desative Gatekeeper, XProtect, Defender for Endpoint, CrowdStrike, SentinelOne ou outro EDR globalmente.

Se precisar liberar excecoes, prefira apenas:

```text
~/WhatsApp-MCP/whatsapp-mcp
~/Documents/WhatsApp MCP Panel
```

Em Mac corporativo, a liberacao pode depender do administrador de TI.
