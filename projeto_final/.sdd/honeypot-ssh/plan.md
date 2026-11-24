# Plano: Laboratório de Honeypot SSH

Spec: [spec.md](spec.md). O plano tem 12 partes, em ordem de dependência. As partes 1 a 4 formam o escopo mínimo da **prévia de 25/11** (Fase 1 mais o início da Fase 2). Cada parte pode ser construída e verificada sem as seguintes.

| # | Parte | Fase | Cobre | Responsável sugerido |
|---|---|---|---|---|
| 1 | Fundação do repositório | 1 | R1, R7, R8, R38 (parcial), R41 (esqueleto), R42 | Tobias |
| 2 | Rede `lab_net` e honeypot Cowrie | 1 | R2, R3, R4, R9, R10, R11, R12 | Tobias |
| 3 | Atacante base, listas e força bruta | 2 | R5, R13, R18 | Tobias |
| 4 | Bot pós-login e servidor de `sample.sh` | 2 | R14, R15, R16 | Tobias |
| 5 | Orquestrador de cenários | 2 | R17 (baseline, distributed, stealth) | Tobias |
| 6 | Analyzer: modelos, SQLite e ingestão | 3 | R19, R20, R21, R22, R27 | Luis Antonio |
| 7 | Analyzer: métricas, classificação, CLI e relatório | 3 | R23, R24, R25, R26 | Luis Antonio |
| 8 | Dashboard base (modos replay e apresentação) | 4 | R3, R28, R29 (sem comparativo), R30, R31, R32 | Luis Antonio |
| 9 | Servidor `hardened-ssh` com fail2ban | 5 | R33, R34, R35, R37 | Tobias |
| 10 | Cenário `against_hardened`, ingestão do hardened e métricas | 5 | R17, R20 (coluna `sensor`), R36 | Ambos |
| 11 | Comparativo de contramedida no painel | 5 | R29 (comparativo) | Luis Antonio |
| 12 | Demo, plano B e documentação final | 6 | R39, R40, R41 | Ambos |

Notas gerais:
- Rastreabilidade: todos os requisitos R1 a R42 aparecem em pelo menos uma parte. Os critérios de aceite de cada fase são cobertos pelas partes indicadas na tabela.
- As partes 1 a 5 e 9 (infraestrutura) são independentes das partes 6 a 8 e 11 (análise e painel). Os dois alunos podem trabalhar em paralelo até a parte 10.
- Até a parte 6 ficar pronta, os testes do analyzer usam `data/samples/cowrie_sample.json`. Antes do laboratório gerar eventos reais (partes 2 a 5), o arquivo é montado a partir de eventos no formato Cowrie; a versão final é regravada na parte 12.
- Ao fim de cada parte: atualizar `README.md` e `docs/DIARIO.md` (instrução 8 do documento de origem).

---

## Parte 1: Fundação do repositório

- **Objetivo**: ter o esqueleto do repositório, as convenções e os atalhos do Makefile prontos, para que as demais partes só acrescentem conteúdo.
- **Cobre**: R1 (parcial), R7, R8, R38 (parcial), R41 (esqueleto), R42.
- **Depende de**: nenhuma.
- **Arquivos e componentes**: `.gitignore`, `.env.example`, `Makefile`, `README.md`, `docs/{DIARIO,ARQUITETURA,ROTEIRO_DEMO,RESULTADOS}.md`, `lab/allowed_targets.txt`, `pyproject.toml` raiz com a configuração de `ruff`/`black`, diretórios `data/{cowrie/{log,downloads},analysis,samples}/` com `.gitkeep`, `reports/`.
- **Abordagem**:
  1. `.gitignore` exclui `.env`, `data/*` (com exceção de `data/samples/` e dos `.gitkeep`), `reports/*.md` gerados, `__pycache__`, `.venv`, listas externas (`attack/wordlists/external/`).
  2. `.env.example` com `COWRIE_TAG`, `F2B_MAXRETRY=5`, `F2B_FINDTIME=60`, `F2B_BANTIME=300`, `DASHBOARD_REFRESH=5`.
  3. `Makefile` com os alvos `up`, `down`, `attack`, `report`, `demo`, `clean`, `test` e `help`; os que dependem de partes futuras imprimem "ainda não implementado" e saem com 0 (sem quebrar `make help`).
  4. `lab/allowed_targets.txt` com `honeypot`, `hardened-ssh` e os aliases do laboratório (um por linha, comentários com `#`).
  5. `README.md` com visão geral, pré-requisitos (Docker, Compose v2, Make) e a seção de solução de problemas vazia.
- **Testes**: não há lógica; verificar o `.gitignore` com `git check-ignore`.
- **Verificação**:
  - `make help` lista os alvos.
  - `git check-ignore -v data/cowrie/log/cowrie.json .env` indica que ambos são ignorados.
  - `git check-ignore data/samples/cowrie_sample.json` não ignora.
- **Riscos**: `.gitignore` bloquear `data/samples/`; detectar com o comando acima.

## Parte 2: Rede `lab_net` e honeypot Cowrie

- **Objetivo**: subir o Cowrie em uma rede interna, sem portas publicadas, gravando `cowrie.json`.
- **Cobre**: R2, R3, R4, R9, R10, R11, R12, R1.
- **Depende de**: Parte 1.
- **Arquivos e componentes**: `docker-compose.yml` (rede `lab_net` com `internal: true`, serviço `honeypot`, serviço mínimo `attacker1` com `ssh` instalado), `honeypot/etc/cowrie.cfg`, `honeypot/etc/userdb.txt`, `attack/Dockerfile` (versão inicial).
- **Abordagem**:
  1. Consultar o registro para escolher a tag estável de `cowrie/cowrie` e fixá-la via `COWRIE_TAG` com valor padrão (resolve a questão aberta 3).
  2. `cowrie.cfg`: `hostname = srv-backup01`, `ssh_version_string` de OpenSSH, `[output_jsonlog] enabled = true`, Telnet desabilitado, diretório de downloads em volume.
  3. `userdb.txt` no formato do Cowrie (`usuario:x:senha`) apenas com `root:123456`, `admin:admin`, `pi:raspberry`, `ubuntu:ubuntu`, e negação (`*`) para as demais combinações; validar o comportamento na versão fixada.
  4. Volumes `./data/cowrie/log` e `./data/cowrie/downloads`; documentar e resolver permissões (uid do usuário `cowrie`) no `Makefile` (`make up` ajusta com `chmod`/`chown` quando necessário).
  5. Não usar `ports:` em nenhum serviço.
- **Testes**: script de teste de fumaça `tests/smoke/test_phase1.sh` (executa os comandos de verificação e sai ≠ 0 em falha).
- **Verificação**:
  - `docker compose up -d && docker compose ps` mostra `honeypot` e `attacker1` em execução.
  - `docker ps --format '{{.Ports}}'` não mostra mapeamento para o host.
  - `docker network inspect <projeto>_lab_net --format '{{.Internal}}'` retorna `true`.
  - `docker compose exec attacker1 sshpass -p 123456 ssh -o StrictHostKeyChecking=no root@honeypot -p 2222 whoami` retorna `root`.
  - Com `-p errada`, falha; `data/cowrie/log/cowrie.json` contém `cowrie.login.failed` e `cowrie.login.success`.
- **Riscos**: permissões do volume impedem a escrita do log (detectar: arquivo não aparece); sintaxe do `userdb.txt` difere entre versões (validar com login aceito e recusado).

## Parte 3: Atacante base, listas e força bruta

- **Objetivo**: ter a imagem atacante completa e o `bruteforce.sh` com lista branca.
- **Cobre**: R5, R13, R18, R8.
- **Depende de**: Parte 2.
- **Arquivos e componentes**: `attack/Dockerfile` (Debian slim com `hydra`, `python3`, `paramiko`, `pyyaml`, `sshpass`), `attack/bruteforce.sh`, `attack/lib/allowlist.sh` (e equivalente em Python para as próximas partes: `attack/allowlist.py`), `attack/wordlists/{users,passwords}.txt`, serviços `attacker1` e `attacker2` no compose com IPs fixos distintos.
- **Abordagem**:
  1. `users.txt` (≈ 30) e `passwords.txt` (≈ 300) escritas à mão, incluindo as quatro credenciais válidas do honeypot em posições diferentes.
  2. `bruteforce.sh <alvo> [--users] [--passwords] [--threads] [--help]`: valida o alvo contra `lab/allowed_targets.txt` (montado como volume somente leitura) antes de qualquer tráfego; mensagem em português e código de saída 2 em caso de recusa; usa `hydra -L -P -t -s 2222 ssh://alvo`.
  3. `attacker1` e `attacker2` com `ipv4_address` fixo na `lab_net` (sub-rede definida no compose).
- **Testes**: testes de shell (`bats` ou script próprio) em `attack/tests/`: alvo permitido passa na validação; alvo `8.8.8.8` e `example.com` recusados; `--help` sai com 0; opção desconhecida sai com 1.
- **Verificação**:
  - `docker compose exec attacker1 /attack/bruteforce.sh 8.8.8.8` imprime a recusa e retorna 2 (`echo $?`).
  - `docker compose exec attacker1 /attack/bruteforce.sh honeypot --threads 4` conclui e encontra as credenciais válidas; `cowrie.json` ganha dezenas de `login.failed`.
  - `docker inspect` mostra IPs distintos de `attacker1` e `attacker2`.
- **Riscos**: o Hydra/SSH pode abrir sessões demais e o Cowrie limitar conexões (ajustar `--threads`); alvo permitido por substring em vez de correspondência exata (testar com `honeypot.evil.com`).

## Parte 4: Bot pós-login e servidor de `sample.sh`

- **Objetivo**: gerar sessões com comandos e downloads reproduzíveis.
- **Cobre**: R14, R15, R16, R5.
- **Depende de**: Parte 3.
- **Arquivos e componentes**: `attack/post_login_bot.py`, `attack/allowpost.py` (reuso de `allowlist.py`), `attack/payload/sample.sh`, `attack/fileserver.py` (ou `python -m http.server`) iniciado no container atacante, alias de rede `lab-fileserver` (decisão da questão aberta 2).
- **Abordagem**:
  1. O bot recebe `--target`, `--user`, `--password`, `--sessions`, `--interval`, `--profile {noisy,stealthy}`, `--seed`; usa `random.Random(seed)` para a ordem e os intervalos.
  2. Sequência fixa de R14; o perfil `noisy` usa intervalos curtos e repete comandos; `stealthy` usa pausas longas e subconjunto dos comandos.
  3. O `sample.sh` contém apenas `echo "fake payload"`; o `wget` aponta para `http://lab-fileserver:8000/sample.sh`, que também precisa constar em `allowed_targets.txt`.
  4. Separar a geração do plano de comandos (função pura `build_plan(profile, seed)`) da execução SSH, para teste unitário.
- **Testes** (`pytest`, `attack/tests/test_bot.py`): mesmo `seed` gera o mesmo plano; seeds diferentes geram planos diferentes; perfil `stealthy` tem menos comandos e intervalos maiores que `noisy`; alvo fora da lista é recusado antes de abrir socket (mock de `paramiko`).
- **Verificação**:
  - `docker compose exec attacker1 python /attack/post_login_bot.py --target honeypot --user root --password 123456 --sessions 2 --seed 1` sai com 0.
  - `grep -c command.input data/cowrie/log/cowrie.json` > 0 e existe um evento `cowrie.session.file_download` com `shasum`.
  - Arquivo em `data/cowrie/downloads` sem bit de execução (`stat -c %a`).
  - Executar duas vezes com o mesmo seed gera a mesma sequência de comandos nos logs.
- **Riscos**: o Cowrie não alcançar `lab-fileserver` (detectar: evento de download falho); `./sample.sh` retornar erro no shell emulado (aceitável; o evento `command.failed` é tratado).

## Parte 5: Orquestrador de cenários

- **Objetivo**: executar cenários YAML reproduzíveis com um comando.
- **Cobre**: R17 (baseline, distributed, stealth), R5, R8, R38 (`make attack`).
- **Depende de**: Partes 3 e 4.
- **Arquivos e componentes**: `attack/run_scenario.py`, `attack/scenarios/{baseline,distributed,stealth}.yml`, alvo `make attack SCENARIO=baseline`.
- **Abordagem**:
  1. Esquema YAML: `name`, `steps[]` com `type` (`bruteforce`, `post_login`, `sleep`), `container` (`attacker1`/`attacker2`), `target`, parâmetros e `seed`; passos marcados `parallel: true` rodam simultaneamente.
  2. O orquestrador valida o YAML e **todos os alvos** antes de executar o primeiro passo.
  3. Registra o início e o fim de cada cenário em `data/analysis/scenarios.jsonl` (usado depois pelo painel para marcar cenários).
  4. Executa os passos nos containers via `docker compose exec` (o orquestrador roda no host).
- **Testes** (`pytest`): YAML válido é carregado; YAML com alvo inválido falha antes de executar qualquer passo; passos paralelos geram a ordem esperada (com executor falso); a escrita de `scenarios.jsonl` é anexada, não sobrescrita.
- **Verificação**:
  - `python attack/run_scenario.py baseline` produz `login.failed`, `login.success`, `command.input` e `session.file_download` no log (critério de aceite da Fase 2).
  - `python attack/run_scenario.py distributed` produz eventos de dois `src_ip` distintos.
  - Cenário com `target: 1.1.1.1` é recusado com mensagem clara e código ≠ 0, sem tráfego.
- **Riscos**: dependência do `docker compose exec` no host; tratar o caso de containers parados com mensagem orientando `make up`.

## Parte 6: Analyzer: modelos, SQLite e ingestão

- **Objetivo**: ingestão contínua, idempotente e rápida de `cowrie.json` para o SQLite.
- **Cobre**: R19, R20, R21, R22, R27.
- **Depende de**: Parte 1 (usa `data/samples/cowrie_sample.json`, que pode ser sintético até a Parte 12).
- **Arquivos e componentes**: `analyzer/pyproject.toml`, `analyzer/Dockerfile`, `analyzer/analyzer/{__init__,models,db,ingest,__main__}.py`, `analyzer/tests/`, `data/samples/cowrie_sample.json`, serviço `analyzer` no compose.
- **Abordagem**:
  1. `models.py`: modelos `pydantic` por `eventid` com campos comuns (`timestamp`, `src_ip`, `session`, `sensor`) e os campos específicos; eventos desconhecidos são armazenados somente como `raw_json`.
  2. `db.py`: criação do esquema (R20) com a coluna adicional `line_hash UNIQUE` e `sensor` (padrão `cowrie`); `PRAGMA journal_mode=WAL`; atualização das `sessions` a partir de `session.connect`, `login.*`, `client.version` e `session.closed`.
  3. `ingest.py`: leitura incremental com deslocamento (offset) persistido, `tail` com detecção de rotação (inode/tamanho), buffer para linha parcial, inserção em lotes (`executemany` por ~1.000 linhas), `INSERT OR IGNORE`.
  4. Contadores de ingeridos, duplicados e inválidos registrados em log.
- **Testes** (`pytest`):
  - parsing de cada `eventid` suportado em campos corretos;
  - linha JSON inválida é contada e a ingestão continua;
  - linha truncada no fim só é processada quando completada;
  - reingestão do mesmo arquivo mantém `COUNT(*)` igual;
  - rotação (arquivo substituído) retoma do início do novo arquivo sem perder eventos;
  - `sessions` calcula `duration_s` e `login_success` corretamente;
  - benchmark: 50 mil eventos sintéticos ingeridos a ≥ 5.000 eventos/s (marcado `slow`).
- **Verificação**:
  - `pytest analyzer/tests -q` verde.
  - `python -m analyzer ingest --log data/samples/cowrie_sample.json` seguido do mesmo comando mantém o número de linhas de `events`.
  - `sqlite3 data/analysis/honeypot.db '.indexes events'` lista os índices de `ts`, `src_ip` e `eventid`.
- **Riscos**: concorrência de leitura (painel) e escrita (analyzer) no SQLite; mitigada pelo modo WAL. Fuso horário dos timestamps (armazenar em UTC ISO-8601).

## Parte 7: Analyzer: métricas, classificação, CLI e relatório

- **Objetivo**: todas as métricas da spec, a classificação de sessões e os comandos `report` e `export`.
- **Cobre**: R23, R24, R25, R26.
- **Depende de**: Parte 6.
- **Arquivos e componentes**: `analyzer/analyzer/{queries,classify,report}.py`, extensão de `__main__.py`, `reports/`, alvo `make report`.
- **Abordagem**:
  1. `queries.py`: funções puras sobre uma conexão SQLite, retornando `pandas.DataFrame` (top usuários/senhas/pares, tentativas por minuto/hora e por IP, taxa de sucesso por origem, top comandos, sequência por sessão, arquivos baixados, tempo até o primeiro sucesso).
  2. `classify.py`: `classify_session(stats) -> {scanner, bruteforcer, intruder, dropper}` com precedência `dropper` > `intruder` > `bruteforcer` > `scanner` e limiares configuráveis; grava o resultado em coluna `behavior` de `sessions`.
  3. `report.py`: gera Markdown com tabelas (top N, séries por minuto, classificação).
  4. CLI `ingest`, `report --out`, `export --csv`, todos com `--help`.
- **Testes** (`pytest`): cada consulta contra um banco semente pequeno com resultados conhecidos; cada classe de comportamento com um caso mínimo e os casos de fronteira (4 versus 5 falhas); precedência quando a sessão é `intruder` e `dropper`; o relatório contém as seções esperadas; `export` cria um CSV por tabela.
- **Verificação**:
  - `pytest analyzer/tests -q` verde (critério da Fase 3).
  - `python -m analyzer report --out reports/relatorio.md` cria o arquivo com top usuários/senhas, séries por minuto e classificação.
  - `python -m analyzer export --csv /tmp/x` cria os CSVs.
- **Riscos**: ambiguidade das regras de classificação; resolvida com limiares documentados em `docs/ARQUITETURA.md`.

## Parte 8: Dashboard base (modos replay e apresentação)

- **Objetivo**: painel em português com as seções da spec que dependem somente do honeypot.
- **Cobre**: R3 (única porta publicada), R28, R29 (sem o comparativo), R30, R31, R32.
- **Depende de**: Parte 7.
- **Arquivos e componentes**: `dashboard/{Dockerfile,requirements.txt,app.py}`, módulos auxiliares `dashboard/{data.py,charts.py}`, rede `host_net` e serviço `dashboard` no compose (`127.0.0.1:8501:8501`), leitura do SQLite por volume somente leitura.
- **Abordagem**:
  1. `data.py` reutiliza as funções de `analyzer.queries` (pacote instalado na imagem do dashboard) e usa `st.cache_data` com TTL igual ao intervalo de atualização.
  2. `st.fragment(run_every=...)` (ou `streamlit-autorefresh`) para atualizar sem recarregar a página; intervalo lido de `DASHBOARD_REFRESH`.
  3. Seções: cartões; série por minuto com marcas lidas de `scenarios.jsonl`; top 10 em barras horizontais (`plotly`); tabela de origens com o nome do container (mapeamento IP→nome por variável de ambiente ou DNS reverso do Docker); replay textual de sessão; arquivos capturados.
  4. Modo apresentação (fontes maiores, menos controles) e modo replay (`--replay` ou variável `REPLAY_DB`) com o banco gerado de `data/samples/`.
  5. Teste de carga com banco sintético de 100 mil eventos (script `dashboard/tools/make_synthetic_db.py`).
- **Testes** (`pytest`, com `streamlit.testing.v1.AppTest`): o app inicia com banco vazio e mostra o aviso "sem dados ainda"; com banco semente mostra os cartões com os totais esperados; o filtro por IP reduz as tabelas; o modo replay não acessa o banco ao vivo; as funções de dados são testadas separadamente.
- **Verificação**:
  - `docker compose up -d dashboard`; `docker ps` mostra apenas `127.0.0.1:8501->8501` publicado (R3).
  - `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8501` retorna 200.
  - Com `distributed` rodando, o painel mostra dois IPs e os números mudam sem recarregar (critério da Fase 4).
  - Banco de 100 mil eventos: primeira renderização ≤ 3 s (medida registrada em `docs/DIARIO.md`).
- **Riscos**: a rede interna não publica portas, por isso o dashboard fica apenas na `host_net`; se o `host_net` conflitar com a sub-rede da `lab_net`, definir sub-redes explícitas. Desempenho: usar consultas agregadas no SQL.

## Parte 9: Servidor `hardened-ssh` com fail2ban

- **Objetivo**: alvo OpenSSH real com banimento automático efetivo dentro do laboratório.
- **Cobre**: R33, R34, R35, R37.
- **Depende de**: Parte 3 (rede e atacantes). Independente das partes 6 a 8.
- **Arquivos e componentes**: `hardened/Dockerfile`, `hardened/sshd_config`, `hardened/fail2ban/{jail.local,filter.d,action.d}`, `hardened/entrypoint.sh`, serviço `hardened-ssh` no compose (`cap_add: NET_ADMIN`, sem `privileged`), `docs/ARQUITETURA.md` (seção da contramedida e política de senhas).
- **Abordagem**:
  1. Debian com `openssh-server`, `fail2ban`, `iptables`; `sshd_config` com `PasswordAuthentication yes`, `MaxAuthTries 3`, `LoginGraceTime 20`, log em arquivo (`/var/log/auth.log` via `rsyslog` ou `LogLevel VERBOSE` com backend `polling`).
  2. Jail `sshd` com valores vindos de `F2B_MAXRETRY`, `F2B_FINDTIME`, `F2B_BANTIME` (template renderizado no entrypoint); ação `iptables-multiport` com `REJECT` (ou `DROP`) para a porta 22.
  3. Usuários de teste com senhas fortes geradas no build a partir de variáveis do `.env`; usuário `weakuser` com senha fraca apenas quando `HARDENED_WEAK_USER=1`.
  4. Documentar `pam_faillock`/`pam_pwquality`; ativação de `pam_faillock` fica opcional.
  5. Logs do sshd e do fail2ban em volume `data/hardened/log` para a Parte 10.
- **Testes**: script `tests/smoke/test_hardened.sh`: (a) 6 tentativas falhas a partir de `attacker1`; (b) `fail2ban-client status sshd` lista o IP banido; (c) nova conexão recebe `Connection refused`/timeout; (d) `attacker2` (outro IP) não é banido; (e) após `fail2ban-client unban --all`, a conexão volta a funcionar.
- **Verificação**:
  - `docker compose exec attacker1 hydra -l alice -P /attack/wordlists/passwords.txt -t 4 ssh://hardened-ssh` é interrompido por recusa após ≤ 5 falhas em 60 s.
  - `docker compose exec hardened-ssh fail2ban-client status sshd` mostra o IP de `attacker1` em `Banned IP list`.
  - `docker compose exec attacker1 nc -zv -w 3 hardened-ssh 22` falha.
- **Riscos**: o fail2ban não ler o log (backend) ou o iptables ausente no container (detectar com `fail2ban-client status`); o Docker usar `nftables` (instalar `iptables-nft` e testar). O ban de `attacker2` por NAT não ocorre, pois os IPs são distintos na `lab_net`.

## Parte 10: Cenário `against_hardened`, ingestão do hardened e métricas

- **Objetivo**: executar o ataque contra o `hardened-ssh` e levar seus eventos ao mesmo banco, com as métricas do experimento.
- **Cobre**: R17 (`against_hardened`), R20 (coluna `sensor`), R36.
- **Depende de**: Partes 5, 7 e 9.
- **Arquivos e componentes**: `attack/scenarios/against_hardened.yml`, `analyzer/analyzer/ingest_hardened.py`, extensão de `models.py` com os eventos normalizados (`ssh.login.failed`, `ssh.login.success`, `fail2ban.ban`, `fail2ban.unban`), `analyzer/analyzer/experiment.py` (métricas do experimento), extensão do CLI (`python -m analyzer ingest-hardened`, `experiment`).
- **Abordagem**:
  1. Adaptador converte linhas do `auth.log` do sshd (`Failed password`, `Accepted password`, `Invalid user`) e do `fail2ban.log` (`Ban`, `Unban`) para o mesmo esquema de `events` com `sensor='hardened'`.
  2. `experiment.py` calcula: tentativas até o ban, tempo do primeiro evento ao ban, tentativas após o ban (conexões recusadas obtidas do log do atacante em `data/analysis/scenarios.jsonl` ou das conexões fracassadas registradas pelo Hydra) e senhas testadas versus o mesmo ataque ao honeypot.
  3. O cenário limpa o estado do fail2ban antes de iniciar (`unban --all`) e roda duas fases (senha forte e usuário fraco opcional).
- **Testes** (`pytest`): cada formato de linha do `auth.log` e do `fail2ban.log` gera o evento esperado; linhas desconhecidas são ignoradas; reingestão é idempotente; `experiment` calcula as métricas corretas em um log sintético (ban depois de 5 falhas, tempo conhecido).
- **Verificação**:
  - `python attack/run_scenario.py against_hardened` termina com o ban registrado.
  - `python -m analyzer experiment` imprime a tabela com tentativas até o ban (≤ 5), tempo até o ban e tentativas bloqueadas.
  - `sqlite3 data/analysis/honeypot.db "select sensor,count(*) from events group by 1"` mostra `cowrie` e `hardened`.
- **Riscos**: formatos de log variam por versão do OpenSSH (fixar a versão da imagem e guardar amostras reais nos testes).

## Parte 11: Comparativo de contramedida no painel

- **Objetivo**: exibir lado a lado honeypot e hardened, com a marca do ban.
- **Cobre**: R29 (comparativo), R36.
- **Depende de**: Partes 8 e 10.
- **Arquivos e componentes**: seção nova em `dashboard/app.py` e função em `dashboard/charts.py`; reuso de `analyzer.experiment`.
- **Abordagem**: dois gráficos de tentativas por minuto (ou acumuladas) com o mesmo eixo de tempo; linha vertical no instante do ban; tabela com as métricas do experimento; mensagem quando ainda não há dados do hardened.
- **Testes** (`pytest` com `AppTest`): sem eventos `hardened`, exibe o aviso; com eventos e um ban sintético, o dado para a marca de ban corresponde ao `fail2ban.ban`; os números da tabela coincidem com `experiment`.
- **Verificação**: depois de `against_hardened`, o painel mostra o comparativo com o instante do ban (critério da Fase 5); captura de tela salva para `docs/`.
- **Riscos**: alinhar os fusos e as escalas de tempo entre as fontes; usar UTC em tudo.

## Parte 12: Demo, plano B e documentação final

- **Objetivo**: demonstração completa em ≤ 7 min, plano B offline e documentação pronta.
- **Cobre**: R39, R40, R41, R1, R38 (completo), R42.
- **Depende de**: Partes 1 a 11.
- **Arquivos e componentes**: `scripts/demo.sh` (chamado por `make demo`), `data/samples/` (log completo da rodada, banco pronto para replay), `docs/{ROTEIRO_DEMO,RESULTADOS,ARQUITETURA,DIARIO}.md`, `README.md` final, gráficos PNG exportados em `docs/img/`.
- **Abordagem**:
  1. `make demo` executa em sequência: verificação do ambiente, `baseline`, abertura do painel (impressão da URL), `against_hardened` com ban e resumo final (`analyzer report` + `experiment`), com pausas marcadas (`--pause` para a apresentação interativa; `--fast` para teste).
  2. Gravar uma rodada completa: copiar `cowrie.json`, os logs do hardened e `scenarios.jsonl` para `data/samples/` (sem dados pessoais) e conferir se o modo replay funciona só com esses arquivos.
  3. `ROTEIRO_DEMO.md` com o passo a passo minuto a minuto (6 a 7 min), falas-chave e o que fazer se algo falhar.
  4. `RESULTADOS.md` com tabelas, gráficos e as limitações da seção 15 do documento de origem; `README.md` completo (pré-requisitos, comandos, solução de problemas: permissões, portas ocupadas).
  5. Rodar `ruff`/`black` e corrigir avisos simples.
- **Testes**: teste de ponta a ponta `tests/e2e/test_demo.sh` em modo `--fast`: sobe do zero, roda a demo e verifica os critérios (eventos de cada tipo, ban registrado, painel respondendo 200, nenhuma porta publicada exceto `127.0.0.1:8501`).
- **Verificação**:
  - `make clean && time make demo` termina em ≤ 7 min (tempo registrado).
  - `REPLAY_DB=data/samples/... ` com o Docker parado: o painel (executado localmente via `streamlit run`) abre em modo replay.
  - `pytest -q` na raiz passa; `ruff check .` sem erros.
- **Riscos**: tempo total acima de 7 min (ajustar quantidade de senhas e `--threads`); rede do local de apresentação (plano B com o replay); imagens já baixadas antes da apresentação (documentar `docker compose pull`/`build` prévios).
