# Testing Runbook

## Purpose

Define the testing strategy for a trust-sensitive litigation product.

## Test Layers

- Unit tests for domain services and validation
- Integration tests for API/database boundaries
- End-to-end tests for upload, research, drafting, strategy, and institutional flows
- Evals for citation integrity, quote-lock behavior, retrieval relevance, contradiction detection, draft completeness, sequencing safety, and institutional auditability

## Early Testing Priorities

- Matter and document creation paths
- Quote span validation
- Research result serialization
- Research memo export
- Bundle chronology, contradiction, duplicate, and exhibit-link serialization
- Draft schema completeness, style pack creation, verified-authority insertion, export, and redlines
- Strategy workspace serialization, bounded scenario branching, and sequencing recommendations
- Approval request and review persistence plus audit event emission
- Plain-language summaries and low-bandwidth brief rendering
- Queued-ingest visibility and operator recovery
- Failure paths for missing spans, unsupported file types, and empty searches

## Current Commands

- `make lint`
- `make test`
- `make build-web`
- `./.venv/bin/ruff check apps/api tests/bootstrap tests/integration`
- `./.venv/bin/mypy apps/api/app`
- `./.venv/bin/pytest tests/bootstrap tests/integration -q`
- `PATH=/usr/local/bin:$PATH COREPACK_HOME=/tmp/corepack /usr/local/bin/corepack pnpm --filter @legalos/web typecheck`
- `PATH=/usr/local/bin:$PATH COREPACK_HOME=/tmp/corepack /usr/local/bin/corepack pnpm --filter @legalos/web build`

## Current Coverage

- `tests/bootstrap/test_bootstrap.py`: root workspace, compose, env, and Makefile guardrails
- `tests/integration/test_quote_lock.py`: checksum-backed quote integrity
- `tests/integration/test_research_flow.py`: upload, search, save, quote retrieval, and export
- `tests/integration/test_bundle_flow.py`: chronology, contradictions, duplicates, exhibit links, and queued-ingest status
- `tests/integration/test_workflow_phases.py`: drafting, style packs, redlines, strategy guardrails, and institutional approvals
- `tests/e2e/research-smoke.spec.ts`: browser happy-path placeholder for Playwright wiring
- `tests/e2e/workflows-smoke.spec.ts`: browser-level drafting, strategy, and institutional workflow smoke

## Current Gap

- Browser e2e remains scaffolded and unexecuted in this environment because Playwright tooling is not installed locally.
- Accessibility and large-document ingestion evals are documented but not yet run automatically in CI.

## Non-Negotiable Rules

- Do not mock away provenance checks in core tests.
- Do not use invented citations or quote spans in fixtures.
- Keep tests deterministic and self-contained.
- Prefer small fixtures that still exercise real data boundaries.
