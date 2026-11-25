# Honeypot SSH com painel de ataques

Projeto final de Segurança Computacional (UFPB). Laboratório isolado em Docker em que atacantes controlados
fazem força bruta contra um honeypot Cowrie, os logs são analisados em SQLite e exibidos em um painel
Streamlit, e uma contramedida (OpenSSH + fail2ban) demonstra o bloqueio do ataque.

Equipe: Tobias Freire e Luis Antonio.

## Pré-requisitos

- Docker Engine e Docker Compose v2
- Make
- Python 3.12 (apenas para rodar testes e scripts no host)

## Uso rápido

```bash
cp .env.example .env
make help
```

```bash
make up                       # sobe honeypot e attacker1
tests/smoke/test_phase1.sh    # verifica isolamento e logs
docker compose exec attacker1 sshpass -p 123456 ssh -p 2222 root@honeypot
tail -f data/cowrie/log/cowrie.json
```

Testes no host: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/python -m pytest attack/tests`.
Ataques manuais (dentro de `attacker1`):

```bash
docker compose exec attacker1 /attack/bruteforce.sh honeypot --users /attack/wordlists/users.txt
docker compose exec attacker1 python3 /attack/post_login_bot.py --target honeypot --sessions 3 --seed 1
```

Os alvos `attack`, `report` e `demo` serão ativados nas próximas fases (veja `.sdd/honeypot-ssh/plan.md`).

## Segurança

Todo o laboratório roda em uma rede Docker interna. Os scripts de ataque só aceitam alvos listados em
`lab/allowed_targets.txt`. Nada é exposto à internet.

## Solução de problemas

- **Logs não aparecem em `data/cowrie/log`:** o Cowrie roda como uid 999; rode `make up` (aplica as permissões) ou `chmod 777 data/cowrie/log data/cowrie/downloads`.
- **`wget` do honeypot falha ao resolver `lab-fileserver`:** o Cowrie só baixa de IPs globais; o servidor do payload fica na `payload_net` (203.0.114.0/29, interna). Não mude essa sub-rede para uma faixa privada.
- **Todos os logins falham:** `honeypot/etc/userdb.txt` deve conter apenas ASCII (sem acentos).
