# Testing Runbook

## Purpose

Define the testing strategy for a trust-sensitive litigation product.

## Test Layers

- Unit tests for domain services and validation
- Integration tests for API/database boundaries
- End-to-end tests for upload, research, drafting, strategy, institutional, and court-intelligence flows
- Evals for citation integrity, quote-lock behavior, chronology fidelity, memory grounding, retrieval relevance, contradiction detection, draft completeness, sequencing safety, profile safety, and institutional auditability

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
- Official artifact import, normalization, chronology merge, memory generation, hybrid retrieval, and profile snapshot rendering
- Failure paths for missing spans, unsupported file types, and empty searches

## Current Commands

Assume the project virtualenv is activated before running the direct Python commands below.

- `make lint`
- `make test`
- `make build-web`
- `python -m ruff check apps/api tests/bootstrap tests/integration`
- `python -m mypy apps/api/app`
- `python -m pytest tests/bootstrap tests/integration -q`
- `python -m pytest tests/integration/test_court_intelligence_flow.py -q`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH apps/web/node_modules/.bin/tsc -p apps/web/tsconfig.json --noEmit --incremental false`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH node_modules/.bin/next build`

## Current Coverage

- `tests/bootstrap/test_bootstrap.py`: root workspace, compose, env, and Makefile guardrails
- `tests/integration/test_quote_lock.py`: checksum-backed quote integrity
- `tests/integration/test_research_flow.py`: upload, search, save, quote retrieval, and export
- `tests/integration/test_bundle_flow.py`: chronology, contradictions, duplicates, exhibit links, and queued-ingest status
- `tests/integration/test_workflow_phases.py`: drafting, style packs, redlines, strategy guardrails, and institutional approvals
- `tests/integration/test_security_hardening.py`: tenant isolation, upload-size enforcement, and login throttling
- `tests/integration/test_court_intelligence_flow.py`: official artifact import, merged chronology, memory/profile refresh, and hybrid search
- `tests/e2e/research-smoke.spec.ts`: browser happy-path placeholder for Playwright wiring
- `tests/e2e/workflows-smoke.spec.ts`: browser-level drafting, strategy, and institutional workflow smoke
- `tests/e2e/court-intelligence-smoke.spec.ts`: browser-level court-intelligence happy path placeholder

## Current Gap

- Browser e2e remains scaffolded and unexecuted in this environment because Playwright tooling is not installed locally.
- Accessibility, large-document ingestion, and court-intelligence evals are documented but not yet run automatically in CI.

## Non-Negotiable Rules

- Do not mock away provenance checks in core tests.
- Do not use invented citations or quote spans in fixtures.
- Keep tests deterministic and self-contained.
- Prefer small fixtures that still exercise real data boundaries.
