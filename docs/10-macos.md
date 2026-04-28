# 10 - MacBook / macOS

O macOS agora tem um caminho proprio para o **modo perfis**: varios numeros, projetos, base SQLite separada, painel Tkinter, icone na Mesa/Desktop, menu bar via `pystray`, LaunchAgent para iniciar com o login e MCP `whatsapp-profiles`.

Ainda assim, o macOS deve ser tratado como **suporte beta** ate ser validado em um Mac real. A bridge core e multiplataforma, mas detalhes de permissao, Homebrew, Python/Tk e EDR corporativo variam bastante por maquina.

## Instalacao recomendada

```bash
git clone https://github.com/spanevello0x/whatsapp-mcp-local-kit.git
cd whatsapp-mcp-local-kit
chmod +x scripts/*.sh
./scripts/bootstrap-macos.sh --install-missing-dependencies --configure-all-mcp
```

O bootstrap acima instala o modo perfis por padrao.

Se quiser apenas verificar dependencias antes de instalar:

```bash
./scripts/install-dependencies-macos.sh
```

## Dependencias

O script espera:

- Xcode Command Line Tools;
- Homebrew, quando for instalar dependencias automaticamente;
- Git;
- Go;
- Python 3.11+ com Tkinter funcionando;
- uv;
- clang.

Se o Xcode Command Line Tools nao existir, o script chama `xcode-select --install` e para. Depois de concluir a instalacao da Apple, rode o bootstrap de novo.

O bootstrap tambem verifica `python3 tkinter`, porque o painel usa Tkinter. Se esse teste falhar, instale Python com Tkinter via Homebrew/python.org e rode novamente.

## Caminhos padrao

```text
~/Documents/WhatsApp MCP Panel
~/Documents/WhatsApp MCP Profiles
~/Documents/WhatsApp MCP Profiles/bin/whatsapp-bridge
~/Desktop/WhatsApp MCP Tray.app
~/Desktop/WhatsApp MCP Tray.command
~/Library/LaunchAgents/com.whatsapp-mcp.tray.plist
```

Estrutura da base:

```text
~/Documents/WhatsApp MCP Profiles/
  profiles.json
  profiles_state.json
  bin/
    whatsapp-bridge
  projetos/
    Vendedores/
      vendedor-joao/
        whatsapp-bridge/
          store/
            whatsapp.db
            messages.db
        bridge.out.log
        bridge.err.log
```

## Primeiro uso

1. Abra `WhatsApp MCP Tray.app` na Mesa/Desktop. Use `WhatsApp MCP Tray.command` apenas como fallback tecnico.
2. Se for a primeira abertura, escolha a pasta geral das bases.
3. Cadastre um projeto e um perfil.
4. Clique em **Conectar QR** no perfil selecionado.
5. Escaneie pelo WhatsApp do celular.
6. Clique em **Voltar ao painel**.
7. Pode ocultar a janela; o menu bar/LaunchAgent mantem o painel ativo enquanto o Mac estiver logado.

## Auto-start no macOS

O auto-start usa LaunchAgent:

```text
~/Library/LaunchAgents/com.whatsapp-mcp.tray.plist
```

O botao **Auto-start** da UI tambem consegue ativar/desativar esse arquivo no macOS. Se o Mac estiver em ambiente corporativo, um EDR pode bloquear a criacao ou o carregamento do LaunchAgent; nesse caso, a liberacao precisa ser feita pelo admin.

## MCP no Codex e Claude

O bootstrap com `--configure-all-mcp` registra o servidor:

```text
whatsapp-profiles
```

No Claude Desktop macOS, o arquivo alterado e:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

Para configurar manualmente:

```bash
./scripts/configure-profiles-mcp-macos.sh --all
```

## Verificacao

```bash
./scripts/verify-profiles-macos.sh
```

Esse verificador checa arquivos principais, runtimes, painel, LaunchAgent, perfis, portas, sessoes, bancos SQLite e se o MCP consegue carregar `list_profiles`.

## Antivirus, Gatekeeper e EDR

Nao desative Gatekeeper, XProtect, Defender for Endpoint, CrowdStrike, SentinelOne ou outro EDR globalmente.

Se precisar liberar excecoes, prefira caminhos pontuais:

```text
~/Documents/WhatsApp MCP Panel
~/Documents/WhatsApp MCP Profiles
<pasta onde voce clonou o repositorio>
```

O motivo: o painel cria um ambiente Python local, compila um binario Go local e cria um LaunchAgent para iniciar com o macOS. Isso parece automacao para alguns antiviruses/EDRs, mas nao exige liberar `python`, `bash`, `go` ou `launchctl` globalmente.

## Limites atuais no Mac

- Precisa de validacao final em um Mac real.
- O icone fica no menu bar, nao na bandeja do Windows.
- O QR continua manual.
- Downloads de midia fisica exigem a bridge daquele perfil aberta.
- Se Python/Tkinter vier quebrado na instalacao local, instale Python via Homebrew ou python.org e rode o bootstrap novamente.

## Fluxo legado de um numero

O modo antigo de um numero ainda existe para compatibilidade:

```bash
./scripts/bootstrap-macos.sh --legacy-single-profile --install-missing-dependencies --patch-localhost --configure-all-mcp
./scripts/first-login-macos.sh
```

Para novos usuarios, prefira o modo perfis.
