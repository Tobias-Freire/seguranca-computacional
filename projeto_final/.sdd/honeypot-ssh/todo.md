# Lista de tarefas: Laboratório de Honeypot SSH

Plano: [plan.md](plan.md). Marque cada item ao concluir. Ao fim de cada parte, atualize `README.md` e `docs/DIARIO.md`.

## Parte 1: Fundação do repositório

- [x] Criar `.gitignore` (ignora `.env`, `data/*` exceto `data/samples/` e `.gitkeep`, caches, listas externas)
- [x] Criar `.env.example` com `COWRIE_TAG`, `F2B_MAXRETRY`, `F2B_FINDTIME`, `F2B_BANTIME`, `DASHBOARD_REFRESH`
- [x] Criar `Makefile` com `up`, `down`, `attack`, `report`, `demo`, `clean`, `test`, `help`
- [x] Criar `lab/allowed_targets.txt` (`honeypot`, `hardened-ssh`, `lab-fileserver`)
- [x] Criar `README.md` (visão geral, pré-requisitos) e `docs/{DIARIO,ARQUITETURA,ROTEIRO_DEMO,RESULTADOS}.md` iniciais
- [x] Criar diretórios `data/...` com `.gitkeep` e `reports/`
- [x] Configurar `ruff` e `black` no `pyproject.toml` raiz
- [x] Check: `make help` lista todos os alvos
- [x] Check: `git check-ignore -v data/cowrie/log/cowrie.json .env` ignora ambos
- [x] Check: `git check-ignore data/samples/cowrie_sample.json` não ignora

## Parte 2: Rede `lab_net` e honeypot Cowrie

- [x] Escolher e fixar a tag de `cowrie/cowrie` (via `COWRIE_TAG`)
- [x] Escrever `docker-compose.yml` com `lab_net` (`internal: true`), `honeypot` e `attacker1`, sem `ports:`
- [x] Escrever `honeypot/etc/cowrie.cfg` (hostname `srv-backup01`, banner OpenSSH, JSON log, Telnet desligado, downloads em volume)
- [x] Escrever `honeypot/etc/userdb.txt` só com `root:123456`, `admin:admin`, `pi:raspberry`, `ubuntu:ubuntu`
- [x] Tratar permissões dos volumes no `make up`
- [x] Criar `tests/smoke/test_phase1.sh`
- [x] Check: `docker compose up -d && docker compose ps` mostra `honeypot` e `attacker1` em execução
- [x] Check: `docker ps --format '{{.Ports}}'` sem mapeamento para o host
- [x] Check: `docker network inspect <projeto>_lab_net --format '{{.Internal}}'` retorna `true`
- [x] Check: login com `root`/`123456` em `honeypot:2222` funciona; com senha errada falha
- [x] Check: `cowrie.json` contém `cowrie.login.failed` e `cowrie.login.success`

## Parte 3: Atacante base, listas e força bruta

- [x] Completar `attack/Dockerfile` (hydra, python3, paramiko, pyyaml, sshpass)
- [x] Criar `attack/wordlists/users.txt` (≈ 30) e `passwords.txt` (≈ 300) incluindo as 4 credenciais válidas
- [x] Implementar `attack/allowlist.sh` e `attack/allowlist.py` (correspondência exata)
- [x] Implementar `attack/bruteforce.sh` com `--users`, `--passwords`, `--threads`, `--help`
- [x] Adicionar `attacker2` e IPs fixos distintos na `lab_net`
- [x] Teste: alvo permitido passa na validação
- [x] Teste: `8.8.8.8`, `example.com` e `honeypot.evil.com` são recusados
- [x] Teste: `--help` sai com 0; opção desconhecida sai com 1
- [x] Check: `bruteforce.sh 8.8.8.8` imprime recusa e retorna 2
- [x] Check: `bruteforce.sh honeypot --threads 4` encontra as credenciais válidas e gera `login.failed` no log
- [x] Check: `docker inspect` mostra IPs distintos para `attacker1` e `attacker2`

## Parte 4: Bot pós-login e servidor de `sample.sh`

- [x] Criar `attack/payload/sample.sh` (apenas `echo "fake payload"`)
- [x] Servir o payload por HTTP no container atacante (porta 8000) e criar o alias `lab-fileserver`
- [x] Implementar `build_plan(profile, seed)` como função pura
- [x] Implementar `attack/post_login_bot.py` (`--target`, `--user`, `--password`, `--sessions`, `--interval`, `--profile`, `--seed`, `--help`)
- [x] Teste: mesmo `seed` gera o mesmo plano
- [x] Teste: seeds diferentes geram planos diferentes
- [x] Teste: `stealthy` tem menos comandos e intervalos maiores que `noisy`
- [x] Teste: alvo fora da lista é recusado antes de abrir socket
- [x] Check: bot com `--sessions 2 --seed 1` sai com 0
- [x] Check: existe `cowrie.session.file_download` com `shasum` no log
- [x] Check: arquivo em `data/cowrie/downloads` sem bit de execução (`stat -c %a`)
- [x] Check: duas execuções com a mesma semente geram a mesma sequência de comandos

## Parte 5: Orquestrador de cenários

- [ ] Definir o esquema YAML dos cenários
- [ ] Implementar `attack/run_scenario.py` (valida todos os alvos antes de executar)
- [ ] Criar `scenarios/baseline.yml`, `distributed.yml` e `stealth.yml`
- [ ] Gravar início e fim em `data/analysis/scenarios.jsonl`
- [ ] Ligar `make attack SCENARIO=<nome>`
- [ ] Teste: YAML válido é carregado
- [ ] Teste: YAML com alvo inválido falha sem executar nenhum passo
- [ ] Teste: passos `parallel` respeitam a ordem esperada (executor falso)
- [ ] Teste: `scenarios.jsonl` é acrescentado, não sobrescrito
- [ ] Check: `baseline` gera `login.failed`, `login.success`, `command.input` e `session.file_download`
- [ ] Check: `distributed` gera eventos de dois `src_ip` distintos
- [ ] Check: cenário com alvo `1.1.1.1` é recusado com código ≠ 0 e sem tráfego

## Parte 6: Analyzer: modelos, SQLite e ingestão

- [ ] Criar `analyzer/pyproject.toml`, `Dockerfile` e o serviço `analyzer` no compose
- [ ] Criar `data/samples/cowrie_sample.json` (eventos no formato Cowrie)
- [ ] Implementar `models.py` (pydantic por `eventid`; desconhecidos só em `raw_json`)
- [ ] Implementar `db.py` (esquema R20, `line_hash UNIQUE`, `sensor`, WAL, atualização de `sessions`)
- [ ] Implementar `ingest.py` (offset persistido, tail, rotação, linha parcial, lotes de ~1.000)
- [ ] Teste: parsing de cada `eventid` suportado
- [ ] Teste: linha JSON inválida é contada e a ingestão continua
- [ ] Teste: linha truncada só é processada quando completada
- [ ] Teste: reingestão não altera `COUNT(*)`
- [ ] Teste: rotação de arquivo retoma sem perder eventos
- [ ] Teste: `sessions` calcula `duration_s` e `login_success`
- [ ] Teste (`slow`): 50 mil eventos ingeridos a ≥ 5.000 eventos/s
- [ ] Check: `pytest analyzer/tests -q` verde
- [ ] Check: duas execuções de `python -m analyzer ingest --log data/samples/cowrie_sample.json` mantêm o mesmo número de linhas
- [ ] Check: `sqlite3 data/analysis/honeypot.db '.indexes events'` lista índices de `ts`, `src_ip`, `eventid`

## Parte 7: Analyzer: métricas, classificação, CLI e relatório

- [ ] Implementar `queries.py` (todas as métricas de R23)
- [ ] Implementar `classify.py` (precedência `dropper` > `intruder` > `bruteforcer` > `scanner`, limiares configuráveis) e a coluna `behavior`
- [ ] Implementar `report.py` (Markdown com tabelas)
- [ ] Completar a CLI: `ingest`, `report --out`, `export --csv`, com `--help`
- [ ] Documentar os limiares em `docs/ARQUITETURA.md`
- [ ] Teste: cada consulta contra banco semente com resultado conhecido
- [ ] Teste: cada classe de comportamento (inclui fronteira 4 vs 5 falhas)
- [ ] Teste: precedência quando a sessão é `intruder` e `dropper`
- [ ] Teste: o relatório contém as seções esperadas
- [ ] Teste: `export` cria um CSV por tabela
- [ ] Check: `python -m analyzer report --out reports/relatorio.md` gera top usuários/senhas, séries por minuto e classificação
- [ ] Check: `python -m analyzer export --csv <pasta>` cria os CSVs
- [ ] Check: `make report` funciona

## Parte 8: Dashboard base

- [ ] Criar `dashboard/{Dockerfile,requirements.txt}` com versões fixas e a rede `host_net`
- [ ] Publicar o serviço só em `127.0.0.1:8501:8501`, com o banco por volume somente leitura
- [ ] Implementar `data.py` (cache com TTL) e `charts.py` (plotly)
- [ ] Implementar `app.py`: cartões, série temporal com marcas de cenário, top 10, origens com nome do container, replay de sessão, arquivos capturados
- [ ] Implementar atualização automática (`DASHBOARD_REFRESH`) e filtros de período/origem
- [ ] Implementar modos apresentação e replay
- [ ] Criar `dashboard/tools/make_synthetic_db.py` (100 mil eventos)
- [ ] Teste: banco vazio mostra "sem dados ainda"
- [ ] Teste: banco semente mostra os totais esperados nos cartões
- [ ] Teste: filtro por IP reduz as tabelas
- [ ] Teste: modo replay não acessa o banco ao vivo
- [ ] Check: `docker ps` mostra só `127.0.0.1:8501->8501` publicado
- [ ] Check: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8501` retorna 200
- [ ] Check: com `distributed` rodando, dois IPs aparecem e os números mudam sem recarregar
- [ ] Check: banco de 100 mil eventos renderiza em ≤ 3 s

## Parte 9: Servidor `hardened-ssh` com fail2ban

- [ ] Criar `hardened/Dockerfile` (openssh-server, fail2ban, iptables-nft, rsyslog)
- [ ] Criar `hardened/sshd_config` (`PasswordAuthentication yes`, `MaxAuthTries 3`, `LoginGraceTime 20`)
- [ ] Criar `jail.local` renderizado a partir das variáveis `F2B_*` e a ação de bloqueio com `REJECT`
- [ ] Criar `entrypoint.sh` e os usuários de teste (senhas fortes; `weakuser` só com `HARDENED_WEAK_USER=1`)
- [ ] Adicionar o serviço `hardened-ssh` (`cap_add: NET_ADMIN`, sem `privileged`) e o volume `data/hardened/log`
- [ ] Documentar `pam_faillock`/`pam_pwquality` em `docs/ARQUITETURA.md`
- [ ] Criar `tests/smoke/test_hardened.sh`
- [ ] Teste: 6 falhas de `attacker1` resultam em ban
- [ ] Teste: nova conexão de `attacker1` é recusada ou expira
- [ ] Teste: `attacker2` não é banido
- [ ] Teste: `unban --all` restaura o acesso
- [ ] Check: `hydra ... ssh://hardened-ssh` é interrompido por recusa após ≤ 5 falhas em 60 s
- [ ] Check: `fail2ban-client status sshd` lista o IP de `attacker1`
- [ ] Check: `nc -zv -w 3 hardened-ssh 22` a partir de `attacker1` falha

## Parte 10: Cenário `against_hardened`, ingestão do hardened e métricas

- [ ] Criar `attack/scenarios/against_hardened.yml` (limpa o estado do fail2ban antes de iniciar)
- [ ] Implementar `ingest_hardened.py` (`auth.log` e `fail2ban.log` para o esquema comum, `sensor='hardened'`)
- [ ] Estender `models.py` com `ssh.login.failed`, `ssh.login.success`, `fail2ban.ban`, `fail2ban.unban`
- [ ] Implementar `experiment.py` (tentativas até o ban, tempo até o ban, tentativas após o ban, senhas testadas versus honeypot)
- [ ] Estender a CLI (`ingest-hardened`, `experiment`)
- [ ] Teste: cada formato de linha do `auth.log` e do `fail2ban.log` gera o evento esperado
- [ ] Teste: linhas desconhecidas são ignoradas
- [ ] Teste: reingestão do hardened é idempotente
- [ ] Teste: `experiment` calcula as métricas corretas em log sintético
- [ ] Check: `python attack/run_scenario.py against_hardened` termina com o ban registrado
- [ ] Check: `python -m analyzer experiment` mostra tentativas até o ban ≤ 5
- [ ] Check: `select sensor,count(*) from events group by 1` mostra `cowrie` e `hardened`

## Parte 11: Comparativo de contramedida no painel

- [ ] Implementar a seção de comparativo em `app.py` e a função em `charts.py`
- [ ] Marcar o instante do ban (linha vertical) e exibir a tabela de métricas do experimento
- [ ] Exibir aviso quando não houver dados do hardened
- [ ] Teste: sem eventos `hardened`, mostra o aviso
- [ ] Teste: com ban sintético, a marca corresponde ao `fail2ban.ban`
- [ ] Teste: os números da tabela coincidem com `experiment`
- [ ] Check: após `against_hardened`, o painel mostra o comparativo com o instante do ban
- [ ] Check: captura de tela salva em `docs/img/`

## Parte 12: Demo, plano B e documentação final

- [ ] Implementar `scripts/demo.sh` (baseline, painel, against_hardened, resumo; opções `--pause` e `--fast`) e ligar `make demo`
- [ ] Gravar uma rodada completa em `data/samples/` (log do Cowrie, logs do hardened, `scenarios.jsonl`, banco para replay) sem dados pessoais
- [ ] Escrever `docs/ROTEIRO_DEMO.md` (6 a 7 min, minuto a minuto, o que fazer se falhar)
- [ ] Escrever `docs/RESULTADOS.md` (tabelas, gráficos PNG, limitações da seção 15)
- [ ] Completar `README.md` (comandos, solução de problemas: permissões, portas ocupadas, `docker compose pull/build` prévios)
- [ ] Completar `docs/ARQUITETURA.md` e `docs/DIARIO.md`
- [ ] Rodar `ruff` e `black` e corrigir avisos simples
- [ ] Criar `tests/e2e/test_demo.sh` (modo `--fast`)
- [ ] Teste: o e2e confirma eventos de cada tipo, ban registrado, painel com 200 e nenhuma porta publicada além de `127.0.0.1:8501`
- [ ] Check: `make clean && time make demo` termina em ≤ 7 min
- [ ] Check: com o Docker parado, `REPLAY_DB=data/samples/... streamlit run dashboard/app.py` abre em modo replay
- [ ] Check: `pytest -q` na raiz passa e `ruff check .` não reporta erros
