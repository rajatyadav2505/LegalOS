#!/usr/bin/env bash
set -euo pipefail

check_candidate() {
  local candidate="$1"
  local executable="${candidate%% *}"

  if ! command -v "$executable" >/dev/null 2>&1; then
    return 1
  fi

  if eval "$candidate -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'" >/dev/null 2>&1; then
    printf '%s\n' "$candidate"
    exit 0
  fi
}

for candidate in \
  /usr/local/bin/python3.12 \
  /opt/homebrew/bin/python3.12 \
  python3.12 \
  python3 \
  python \
  "py -3.12" \
  "py -3"
do
  check_candidate "$candidate"
done

printf '%s\n' 'Unable to locate Python 3.12+' >&2
exit 1
