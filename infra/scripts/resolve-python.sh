#!/usr/bin/env bash
set -euo pipefail

for candidate in \
  /usr/local/bin/python3.12 \
  /opt/homebrew/bin/python3.12 \
  python3.12 \
  python3
do
  if ! command -v "$candidate" >/dev/null 2>&1; then
    continue
  fi

  if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
    printf '%s\n' "$(command -v "$candidate")"
    exit 0
  fi
done

printf '%s\n' 'Unable to locate Python 3.12+' >&2
exit 1
