#!/usr/bin/env bash
set -euo pipefail

python_bin="$("./infra/scripts/resolve-python.sh")"
"${python_bin}" ./infra/scripts/lint_bootstrap.py
