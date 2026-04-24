# Prompt pronto para colar no Codex

Use este prompt em uma conversa nova do Codex no computador Windows ou macOS onde a bridge vai rodar.

```text
Quero instalar e configurar o WhatsApp MCP Local Kit neste computador.

Objetivo:
- Rodar uma bridge local do WhatsApp baseada em lharries/whatsapp-mcp.
- Criar um painel de bandeja com sincronizacao manual e random.
- Configurar uso com Codex e/ou Claude Desktop.
- Fazer tudo sem publicar conversas, sessoes, QR Codes ou bancos .db.

Regras obrigatorias:
- Comece pelo diagnostico. Nao apague, substitua ou mova arquivos antes de mostrar o estado encontrado.
- Antes de instalar dependencias, criar atalhos, configurar MCP ou rodar build, explique o que sera feito e por que.
- Se existir whatsapp.db ou messages.db, faca backup antes de qualquer reinstalacao.
- Nao crie excecao global para powershell.exe, cmd.exe, wscript.exe, python.exe ou go.exe.
- Para antivirus, apenas me diga exatamente quais pastas/arquivos liberar e espere eu confirmar que fiz.
- Se algum antivirus colocar arquivo em quarentena, pare e me oriente a restaurar somente se o caminho estiver dentro das pastas esperadas.
- Operacoes de envio de mensagem no WhatsApp precisam de confirmacao explicita.
- Prefira bridge acessivel apenas em 127.0.0.1.
- Ao final, valide com operacoes read-only.

Passos esperados:
1. Ler README.md e docs/.
2. Identificar o sistema operacional e seguir os scripts Windows ou macOS.
3. Verificar Go, Python, uv, Git e GCC/MSYS2 no Windows ou Xcode Command Line Tools/clang no macOS.
4. Verificar se ja existe instalacao local da bridge.
5. Preservar store/whatsapp.db e store/messages.db.
6. Se faltarem dependencias, explicar e pedir confirmacao antes de instalar.
7. Rodar o bootstrap correto quando for seguro.
8. Se eu pedir MCP automatico, usar o configurador correto para Codex, Claude ou ambos.
9. Se nao existir sessao, rodar first-login em terminal visivel para eu escanear QR.
10. Confirmar que o atalho/launcher abre sem terminal permanente.
11. Confirmar que o painel fica na bandeja/menu bar e registra ultima sincronizacao.
12. Rodar o verificador do sistema operacional e explicar o resultado.
13. Me entregar um resumo com os caminhos criados, o que ficou no auto-start e como pausar.
```
