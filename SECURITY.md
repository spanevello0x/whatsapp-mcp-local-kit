# Seguranca

Este repositorio nao deve conter dados reais de WhatsApp.

Nao publique:

- `whatsapp.db`
- `messages.db`
- `*.db`
- QR Codes
- logs da bridge
- backups da pasta `store`
- tokens, cookies ou credenciais

Se voce encontrar algum arquivo sensivel em um fork publico, remova o arquivo, invalide a sessao do WhatsApp em "Dispositivos conectados" e reescreva o historico do Git se necessario.

## Modelo de ameaca simples

- A bridge deve escutar apenas em `127.0.0.1`.
- O painel deve iniciar a bridge localmente e fechar fora das janelas de sincronizacao, se voce usar modo rajadas.
- Excecoes de antivirus devem ser por pasta/arquivo, nunca por interpretador global.
- O MCP so deve ser usado em conversas onde voce aceita enviar os trechos consultados ao modelo.

