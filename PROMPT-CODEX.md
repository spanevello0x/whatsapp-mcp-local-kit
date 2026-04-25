# Prompt Pronto Para Codex Ou Claude

Use este prompt em uma conversa nova do Codex ou Claude no computador onde o WhatsApp MCP Local Kit sera instalado.

```text
Quero instalar e configurar o WhatsApp MCP Local Kit neste computador.

Objetivo:
- Usar o modo perfis como fluxo principal de producao.
- Criar um painel local de bandeja para gerenciar varios numeros de WhatsApp.
- Separar as bases por projeto e por perfil.
- Cada perfil deve ter porta local, sessao, logs e messages.db proprios.
- Configurar o MCP whatsapp-profiles para Codex e/ou Claude Desktop.
- Fazer tudo sem publicar conversas, sessoes, QR Codes, bancos .db, logs ou tokens.

Regras obrigatorias:
- Comece lendo README.md, COMECE_AQUI.md, docs/00-o-que-e-automatico.md, docs/02-antivirus.md e docs/12-perfis-multiplos.md.
- Diagnostique o ambiente antes de alterar qualquer coisa.
- Mostre se Git, Python, uv, Go e GCC/MSYS2 estao disponiveis.
- Antes de instalar dependencias, criar atalhos, configurar MCP ou rodar build, explique o que sera feito e por que.
- Se existir whatsapp.db ou messages.db, faca backup antes de qualquer reinstalacao.
- Nao apague bancos .db, logs ou pastas de perfil sem minha confirmacao explicita.
- Nao crie excecao global para powershell.exe, cmd.exe, wscript.exe, python.exe ou go.exe.
- Para antivirus, diga exatamente quais pastas/arquivos liberar e espere eu confirmar.
- Se o antivirus colocar arquivo em quarentena, oriente restaurar somente se o caminho estiver dentro das pastas esperadas.
- Operacoes de envio de mensagem no WhatsApp precisam de confirmacao explicita.
- Prefira bridge acessivel apenas em 127.0.0.1.
- Ao final, valide com operacoes read-only.

Passos esperados:
1. Confirmar o diretorio do repositorio.
2. Confirmar que o repositorio nao contem .db, QR, logs sensiveis ou tokens versionados.
3. Conferir dependencias.
4. Orientar excecoes do antivirus antes de compilar/rodar.
5. Rodar o bootstrap Windows em modo perfis:
   powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp
6. Se faltarem dependencias e eu autorizar, rodar:
   powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp -InstallMissingDependencies
7. Abrir o painel pelo icone WhatsApp MCP Tray.
8. Na primeira abertura, orientar a escolha da pasta geral das bases.
9. Cadastrar o primeiro perfil com projeto, nome e descricao.
10. Abrir QR somente quando eu clicar em Conectar QR no perfil correto.
11. Confirmar que depois do QR o painel mostra status de sync inteligente.
12. Confirmar que auto-start esta ativo ou orientar ativacao pelo painel.
13. Rodar:
    powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
14. Entregar um resumo com caminhos, nome do MCP, como pausar, sincronizar, remover perfil, abrir pasta do projeto e copiar DB.
```

## Comando Principal

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp
```

Windows com tentativa de instalar dependencias via `winget`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-windows.ps1 -ProfilesMode -ConfigureAllMcp -InstallMissingDependencies
```

Validacao:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-profiles.ps1
```

## O Que A IA Deve Explicar Ao Usuario

- O repositorio nao traz mensagens nem sessoes prontas.
- Cada usuario precisa escanear o QR no proprio WhatsApp.
- A primeira sincronizacao pode ficar ativa por bastante tempo, mas fecha quando estabilizar.
- Depois disso, as sincronizacoes acontecem em janelas random.
- A IA consegue pesquisar a base local pelo MCP mesmo com a porta fechada.
- Baixar midias fisicas exige a bridge do perfil aberta.
- Remover perfil pode preservar dados ou apagar a pasta inteira, conforme escolha do usuario.
