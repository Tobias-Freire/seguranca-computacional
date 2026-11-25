#!/usr/bin/env bash
# Teste de fumaça da Fase 1: honeypot isolado, sem portas publicadas e gravando logs JSON.
# Uso: tests/smoke/test_phase1.sh [--help]
set -uo pipefail

if [[ "${1:-}" == "--help" ]]; then
  sed -n '2,3p' "$0" | sed 's/^# //'
  exit 0
fi

cd "$(dirname "$0")/../.."
LOG=data/cowrie/log/cowrie.json
falhas=0

verifica() {  # verifica <descrição> <comando...>
  local descricao=$1
  shift
  if "$@" >/dev/null 2>&1; then
    echo "OK    $descricao"
  else
    echo "FALHA $descricao"
    falhas=$((falhas + 1))
  fi
}

ssh_honeypot() {  # ssh_honeypot <usuário> <senha>
  docker compose exec -T attacker1 sshpass -p "$2" ssh -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -p 2222 "$1@honeypot" whoami
}

honeypot_rodando() { docker compose ps --status running --services | grep -qx honeypot; }
sem_portas_publicadas() { ! docker compose ps --format '{{.Ports}}' | grep -q -- '->'; }
rede_interna() { for n in lab_net payload_net; do [[ "$(docker network inspect honeypot-ssh_$n --format "{{.Internal}}")" == true ]] || return 1; done; }
login_recusado() { ! ssh_honeypot root senha-errada; }
log_contem() { grep -q "$1" "$LOG"; }

verifica "honeypot em execução" honeypot_rodando
verifica "nenhuma porta publicada no host" sem_portas_publicadas
verifica "lab_net e payload_net são internas" rede_interna
verifica "login fraco root/123456 aceito" ssh_honeypot root 123456
verifica "login com senha errada recusado" login_recusado
sleep 2
verifica "log contém cowrie.login.success" log_contem cowrie.login.success
verifica "log contém cowrie.login.failed" log_contem cowrie.login.failed

exit $((falhas > 0))
