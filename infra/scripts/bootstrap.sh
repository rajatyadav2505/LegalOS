#!/usr/bin/env bash
set -euo pipefail

./infra/scripts/resolve-python.sh --run ./infra/scripts/lint_bootstrap.py
