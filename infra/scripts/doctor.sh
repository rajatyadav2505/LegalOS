#!/usr/bin/env bash
set -euo pipefail

python_bin="$("./infra/scripts/resolve-python.sh")"
printf '%s\n' "Python: ${python_bin}"
if command -v node >/dev/null 2>&1; then
  printf '%s\n' "Node: $(command -v node)"
else
  printf '%s\n' "Node: unavailable on PATH"
fi
if command -v docker >/dev/null 2>&1; then
  printf '%s\n' "Docker: $(command -v docker)"
else
  printf '%s\n' "Docker: unavailable on PATH"
fi
