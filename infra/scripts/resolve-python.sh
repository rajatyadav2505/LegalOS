#!/usr/bin/env bash
set -euo pipefail

run_mode=false
declare -a run_args=()

if [[ "${1:-}" == "--run" ]]; then
  run_mode=true
  shift
  run_args=("$@")
fi

check_candidate() {
  local executable="$1"
  shift
  local -a candidate_args=("$@")

  if ! command -v "$executable" >/dev/null 2>&1; then
    return 1
  fi

  if (( ${#candidate_args[@]} > 0 )); then
    if ! "$executable" "${candidate_args[@]}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
      return 1
    fi
  else
    if ! "$executable" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
      return 1
    fi
  fi

  if [[ "$run_mode" == true ]]; then
    if (( ${#candidate_args[@]} > 0 )); then
      exec "$executable" "${candidate_args[@]}" "${run_args[@]}"
    fi
    exec "$executable" "${run_args[@]}"
  fi

  printf '%s' "$executable"
  if (( ${#candidate_args[@]} > 0 )); then
    for arg in "${candidate_args[@]}"; do
      printf ' %s' "$arg"
    done
  fi
  printf '\n'
  exit 0
}

try_candidate() {
  check_candidate "$@" || true
}

try_candidate python3.12
try_candidate python3
try_candidate python
try_candidate /usr/local/bin/python3.12
try_candidate /opt/homebrew/bin/python3.12
try_candidate py -3.12
try_candidate py -3

printf '%s\n' 'Unable to locate Python 3.12+' >&2
exit 1
