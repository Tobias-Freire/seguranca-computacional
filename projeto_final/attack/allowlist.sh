#!/usr/bin/env bash
# Lista branca de alvos do laboratório. Deve ser carregado com `source`.
# Uso: require_allowed_target <alvo>   (encerra o script com código 2 se o alvo não for permitido)

ALLOWLIST_FILE="${LAB_ALLOWED_TARGETS:-$(dirname "${BASH_SOURCE[0]}")/../lab/allowed_targets.txt}"

# Retorna 0 se o alvo consta, por correspondência exata, na lista branca.
is_allowed_target() {
  local alvo=$1
  [[ -n "$alvo" && -r "$ALLOWLIST_FILE" ]] || return 1
  grep -v '^[[:space:]]*#' "$ALLOWLIST_FILE" | sed 's/[[:space:]]*$//' | grep -Fxq -- "$alvo"
}

require_allowed_target() {
  local alvo=$1
  if ! is_allowed_target "$alvo"; then
    echo "ERRO: alvo '$alvo' recusado. Só são permitidos os alvos de $ALLOWLIST_FILE." >&2
    exit 2
  fi
}
