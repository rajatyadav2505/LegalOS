SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE_FILE := infra/compose/docker-compose.yml
PYTHON := $(shell ./infra/scripts/resolve-python.sh)
COREPACK := $(shell command -v corepack 2>/dev/null || echo /usr/local/bin/corepack)
NODE_BIN_DIR := $(shell dirname "$$(command -v node 2>/dev/null || echo /usr/local/bin/node)")
PNPM := PATH=$(NODE_BIN_DIR):$$PATH COREPACK_HOME=/tmp/corepack $(COREPACK) pnpm

.PHONY: help bootstrap doctor setup lint test dev dev-api dev-web build-web e2e seed migrate drain-queued compose-up compose-down compose-logs

help:
	@printf '%s\n' 'Targets:'
	@printf '%s\n' '  bootstrap    Validate root and infra bootstrap files'
	@printf '%s\n' '  setup        Create the Python env, install API deps, and install pnpm workspaces'
	@printf '%s\n' '  doctor       Print local toolchain status'
	@printf '%s\n' '  lint         Run bootstrap lint, Ruff, mypy, and frontend typecheck'
	@printf '%s\n' '  test         Run bootstrap and integration tests'
	@printf '%s\n' '  dev          Start local infrastructure stack'
	@printf '%s\n' '  dev-api      Run the FastAPI app locally'
	@printf '%s\n' '  dev-web      Run the Next.js app locally'
	@printf '%s\n' '  build-web    Build the production web bundle'
	@printf '%s\n' '  e2e          Reserved for browser tests once Playwright is installed'
	@printf '%s\n' '  seed         Apply demo seed data through the API package'
	@printf '%s\n' '  migrate      Apply Alembic migrations for the API service'
	@printf '%s\n' '  drain-queued Drain queued document-ingest work through the worker plane'
	@printf '%s\n' '  compose-up   Start Postgres, Valkey, MinIO, and Tika'
	@printf '%s\n' '  compose-down Stop the local infrastructure stack'

setup: bootstrap
	@$(PYTHON) -m venv .venv
	@./.venv/bin/pip install -e 'apps/api[dev]'
	@$(PNPM) install

bootstrap:
	@./infra/scripts/bootstrap.sh

doctor:
	@./infra/scripts/doctor.sh

lint:
	@$(PYTHON) ./infra/scripts/lint_bootstrap.py
	@./.venv/bin/ruff check apps/api apps/worker-ingest apps/worker-ai tests/bootstrap tests/integration
	@./.venv/bin/mypy apps/api/app
	@$(PNPM) --filter @legalos/web typecheck

test:
	@./.venv/bin/pytest tests/bootstrap tests/integration -q

dev: compose-up

dev-api:
	@cd apps/api && ../../.venv/bin/uvicorn app.main:app --reload

dev-web:
	@$(PNPM) --filter @legalos/web dev

build-web:
	@$(PNPM) --filter @legalos/web build

e2e:
	@printf '%s\n' 'Playwright specs exist under tests/e2e/*.spec.ts; install the browser toolchain before running them.'

seed:
	@cd apps/api && ../../.venv/bin/python -m app.db.seed

migrate:
	@cd apps/api && ../../.venv/bin/alembic upgrade head

drain-queued:
	@PYTHONPATH=apps/api ./.venv/bin/python apps/worker-ingest/src/worker_ingest.py --drain-queued --limit 25

compose-up:
	@docker compose -f $(COMPOSE_FILE) up -d

compose-down:
	@docker compose -f $(COMPOSE_FILE) down

compose-logs:
	@docker compose -f $(COMPOSE_FILE) logs -f
