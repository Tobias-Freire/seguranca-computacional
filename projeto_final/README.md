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

Os alvos `up`, `attack`, `report` e `demo` serão ativados nas próximas fases (veja `.sdd/honeypot-ssh/plan.md`).

## Segurança

Todo o laboratório roda em uma rede Docker interna. Os scripts de ataque só aceitam alvos listados em
`lab/allowed_targets.txt`. Nada é exposto à internet.

## Solução de problemas

(a preencher conforme as fases avançam)
