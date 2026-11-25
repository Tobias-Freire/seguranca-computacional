#!/usr/bin/env bash
# Testes do bruteforce.sh e da lista branca (não enviam tráfego de rede).
# Uso: attack/tests/test_bruteforce.sh
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$AQUI/../bruteforce.sh"
falhas=0

espera_codigo() {  # espera_codigo <descrição> <código esperado> <comando...>
  local descricao=$1 esperado=$2
  shift 2
  "$@" >/dev/null 2>&1
  local obtido=$?
  if [[ $obtido -eq $esperado ]]; then
    echo "OK    $descricao"
  else
    echo "FALHA $descricao (esperado $esperado, obtido $obtido)"
    falhas=$((falhas + 1))
  fi
}

espera_codigo "--help sai com 0" 0 "$SCRIPT" --help
espera_codigo "sem alvo sai com 1" 1 "$SCRIPT"
espera_codigo "opção desconhecida sai com 1" 1 "$SCRIPT" honeypot --nada
espera_codigo "threads não numérico sai com 1" 1 "$SCRIPT" honeypot --threads abc
espera_codigo "IP público 8.8.8.8 recusado" 2 "$SCRIPT" 8.8.8.8
espera_codigo "example.com recusado" 2 "$SCRIPT" example.com
espera_codigo "honeypot.evil.com recusado (sem correspondência parcial)" 2 "$SCRIPT" honeypot.evil.com
espera_codigo "prefixo 'honey' recusado" 2 "$SCRIPT" honey

# O alvo permitido passa da validação: com uma lista de usuários inexistente falha por uso (1), não por recusa (2).
espera_codigo "alvo 'honeypot' passa na lista branca" 1 "$SCRIPT" honeypot --users /nao/existe

[[ "$(wc -l <"$AQUI/../wordlists/users.txt")" -ge 25 ]] && echo "OK    users.txt tem ~30 entradas" || { echo "FALHA users.txt curta"; falhas=$((falhas + 1)); }
[[ "$(wc -l <"$AQUI/../wordlists/passwords.txt")" -ge 250 ]] && echo "OK    passwords.txt tem ~300 entradas" || { echo "FALHA passwords.txt curta"; falhas=$((falhas + 1)); }

exit $((falhas > 0))
