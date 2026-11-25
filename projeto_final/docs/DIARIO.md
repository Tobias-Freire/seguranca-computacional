# Diário do projeto

## 2026-11-24: Parte 1 (fundação do repositório)

- Criados `.gitignore`, `.env.example`, `Makefile`, `lab/allowed_targets.txt`, `pyproject.toml` (ruff/black), README e docs iniciais.
- Decisão: `data/samples/` é versionado (plano B da demo); o restante de `data/` é ignorado.

## 2026-11-24: Parte 2 (rede lab_net e honeypot Cowrie)

- Tag fixada: `cowrie/cowrie:3.1.8` (mais recente estável em 24/11). A imagem é distroless (sem shell); `etc` e `var` são volumes.
- `docker-compose.yml`: `lab_net` interna (172.30.0.0/24), sem `ports:`. IPs fixos: honeypot .10, attacker1 .21.
- Problema: o Cowrie lê `userdb.txt` como ASCII; um comentário com acentos fez o arquivo ser ignorado (todos os logins falhavam). Solução: arquivo só em ASCII.
- Permissões: o Cowrie roda como uid 999; `make up` aplica `chmod 777` nos volumes de log e downloads.
- Verificação: `tests/smoke/test_phase1.sh` (7 checks) passa.

## 2026-11-24: Parte 3 (atacante base, listas e força bruta)

- `attack/bruteforce.sh` valida o alvo na lista branca (correspondência exata) antes de qualquer tráfego; recusa retorna código 2. Equivalente Python em `attack/allowlist.py`.
- Wordlists: 30 usuários e 270 senhas, com as 4 credenciais válidas do honeypot em posições diferentes.
- Desempenho do Hydra contra o Cowrie: 4 tarefas ≈ 3 tentativas/s; 16 tarefas ≈ 21 tentativas/s. A lista completa (30 x 270) leva ≈ 6 min com 16 tarefas; por isso o padrão é 16 e os cenários da demo devem usar listas menores.
- O Hydra para de testar um usuário depois de achar a senha; com os 4 usuários válidos e 270 senhas leva ≈ 20 s e encontra as 4 credenciais.
- `attacker2` adicionado (172.30.0.22). Testes: `attack/tests/test_bruteforce.sh` (11 checks) e `attack/tests/test_allowlist.py`.

## 2026-11-24: Parte 4 (bot pós-login e servidor de sample.sh)

- `attack/post_login_bot.py`: `build_plan(profile, rng, fileserver)` é pura e determinística (mesma semente, mesma sequência); sessões usam shell interativo do Paramiko para preservar o diretório entre `wget`, `chmod` e `./sample.sh`.
- **Descoberta importante:** o `wget` do Cowrie 3.1.8 só baixa de IPs *globais* (lista `BLOCKED_IPS` fixa no código, proteção contra SSRF) e não usa o DNS do Docker. Solução: rede `payload_net` interna (203.0.114.0/29, sem rota para fora) onde `attacker1` serve o `sample.sh` (alias `lab-fileserver`), e `extra_hosts` no honeypot para resolver o nome.
- O Cowrie limita `wget` a 5 por minuto por host; desligado em `[shell]` do `cowrie.cfg` para que os cenários repitam downloads.
- Verificado: `file_download` com SHA-256 igual ao do `sample.sh` (`b3a7705a...`), arquivo em `data/cowrie/downloads` com modo 644 (sem execução), 7 sessões seguidas geram 7 downloads, duas execuções com `--seed 5` geram a mesma sequência de comandos.
- Observação: o `./sample.sh` no shell emulado imprime o conteúdo do arquivo e o Cowrie o registra como mais um `command.input`; nada é executado de fato.
- Ambiente de testes no host: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`.
