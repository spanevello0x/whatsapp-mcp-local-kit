# 04 - Seguranca

Riscos principais:

- `messages.db` contem conversas reais.
- `whatsapp.db` contem sessao autenticada do WhatsApp.
- A bridge abre API local na porta do perfil durante QR, sync ou download.
- O MCP envia ao modelo apenas os trechos que voce pedir, mas esses trechos saem do PC.
- Excecoes de antivirus reduzem inspecao nas pastas liberadas.

Recomendacoes:

- Nunca commite `.db`, logs, backups, QR Codes ou tokens.
- Prefira bridge ligada apenas a `127.0.0.1`.
- Use firewall para bloquear acesso externo as portas dos perfis.
- Deixe o modo random fechar a porta quando nao estiver sincronizando.
- Nao coloque downloads aleatorios nas pastas liberadas no antivirus.
- Crie excecoes apenas para o clone, painel e pasta de bases.
- Nao compartilhe a pasta `WhatsApp MCP Profiles` sem revisar o conteudo.

## Portas

Cada perfil usa uma porta local, como:

```text
8101
8102
8103
```

Essas portas devem ficar acessiveis apenas localmente (`127.0.0.1`).

## Pesquisa Com Porta Fechada

Codex/Claude podem pesquisar `messages.db` com a porta fechada. Isso reduz exposicao, porque a bridge nao precisa ficar aceitando conexao o dia inteiro.

## Remocao Segura

Ao remover um perfil, escolha:

- **Remover so do painel** se quiser preservar historico e sessao local.
- **Apagar perfil e dados locais** se quiser eliminar `whatsapp.db`, `messages.db`, logs e midias daquele perfil.

O painel so apaga automaticamente pastas dentro da pasta geral configurada.

## Patch Localhost

A bridge vendorizada deve escutar em `127.0.0.1`, nao em todas as interfaces.

Trecho esperado no codigo Go:

```go
serverAddr := fmt.Sprintf("127.0.0.1:%d", port)
```
