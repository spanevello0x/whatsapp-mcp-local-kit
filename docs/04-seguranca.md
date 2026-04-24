# 04 - Seguranca

Riscos principais:

- `messages.db` contem conversas reais.
- A bridge pode abrir API local na porta 8080.
- O MCP envia ao modelo apenas os trechos que voce pedir, mas esses trechos saem do PC.
- Excecoes de antivirus reduzem inspecao nas pastas liberadas.

Recomendacoes:

- Nunca commite `.db`, logs ou backups.
- Prefira bridge ligada a `127.0.0.1`.
- Use firewall para bloquear acesso externo a 8080.
- Use modo rajadas se nao precisa sync continuo.
- Nao coloque downloads aleatorios nas pastas liberadas.

Patch recomendado no upstream:

```go
serverAddr := fmt.Sprintf("127.0.0.1:%d", port)
```

Depois recompile a bridge.
