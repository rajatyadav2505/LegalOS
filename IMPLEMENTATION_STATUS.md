# Implementation Status

## Baseline

- Repository inspected on 2026-03-24.
- The repo was effectively empty apart from `AGENTS.md`, `.env.example`, `.gitignore`, and local cache/artifact files.
- No application code, package manifests, or app directories existed at the start of implementation.

## Phase 0: Foundation

Status: `complete`

Delivered:

- Monorepo scaffold with `apps/*`, `packages/*`, `docs/*`, `infra/*`, and `tests/*`
- Root workspace metadata, task runner, bootstrap scripts, and CI workflow
- Cross-platform bootstrap support for macOS, Linux, WSL, and Git Bash on Windows, plus a native Windows PowerShell runbook
- Local compose stack for PostgreSQL, Valkey, MinIO, and Apache Tika
- FastAPI application skeleton with settings, auth, domain models, repositories, services, and Alembic baseline
- Next.js App Router shell with typed API client integration
- Shared UI and contract packages
- Demo seed fixtures and seed loader
- Updated README, runbooks, ADR 0001, and implementation tracking

## Phase 1: Research Core

Status: `complete`

Delivered:

- Document upload endpoint and web upload workflow
- Extraction adapters for text, HTML, DOCX, PDF, and image OCR
- Chunking plus paragraph-level quote span creation with checksum-backed quote-lock
- Public-law plus matter-document search over the same research surface
- Authority save flow with `apply`, `distinguish`, `adverse`, and `draft` treatments
- Research memo export endpoint and UI action
- Seeded verified Constitution excerpts for Articles 14, 21, 32(1), and 39A
- Integration tests covering quote integrity, upload, search, save, quote retrieval, and export

## Phase 2: Bundle Intelligence

Status: `complete`

Delivered:

- Matter bundle map API with chronology, contradiction, cluster, duplicate-group, exhibit-link, and ingest-status payloads
- Bundle workspace UI with chronology cards, contradiction lattice, cluster summaries, duplicate detection, exhibit chains, and document processing visibility
- Bundle artifact materialization into Postgres tables for chronology events, document entities, exhibit references, and document relations
- Duplicate detection and issue-level contradiction surfacing across ready matter documents
- Queued-ingest visibility with operator recovery through `make drain-queued` and the worker ingest CLI
- Shared package build pipeline for `@legalos/contracts` and `@legalos/ui`, removing raw-source module resolution drift
- Integration tests covering Phase 2 bundle intelligence and queued-processing status

## Phase 3: Drafting Studio

Status: `complete`

Delivered:

- Structured drafting schemas and routes for petitions, replies, written submissions, affidavits, applications, synopsis, list of dates, legal notice, and settlement note
- Style pack creation with source-document-derived voice notes and chamber-oriented openings and prayer styles
- Verified-authority insertion from saved research only, carrying citation text, anchor labels, and quote checksums into draft responses
- Visible unresolved-fact placeholders surfaced from matter state and bundle completeness checks
- Annexure scheduling, markdown export, and versioned redline support across draft revisions
- Draft Studio web workspace wired to the live API

## Phase 4: Strategy and Arguments

Status: `complete`

Delivered:

- Strategy workspace API and UI with best, fallback, and risk lines
- Issue-level attack, defense, oral, written, rebuttal, and bench-question cards
- Bounded scenario tree built from versioned prompt assets rather than uncontrolled swarm behavior
- Lawful sequencing console that classifies disclosure timing while preserving mandatory-disclosure warnings
- Audit events for sequencing reviews and decision-support labeling throughout the workflow

## Phase 5: Institutional Mode

Status: `complete`

Delivered:

- Institutional dashboard API and UI with urgency posture, latest-draft visibility, and pending-approval counts
- Approval request and review workflows for draft documents
- Organization-level audit event surfacing for sensitive matter actions
- Plain-language English and Hindi matter summaries for beneficiary or coordinator use
- Low-bandwidth brief mode for constrained device or network conditions

## Phase 6: Court Intelligence

Status: `complete`

Delivered:

- Bounded orchestration foundation with `jobs`, `job_attempts`, `job_artifacts`, `prompt_runs`, and `model_runs`
- Typed job payloads, idempotency keys, retries, failure states, and audit-aware sensitive job handling in the AI worker plane
- Canonical court-intelligence models for courts, benches, judges, external cases, parties, counsels, events, listings, filings, deadlines, caveats, provenance, memories, profiles, and hybrid index entries
- Official-artifact connectors and user-assisted import adapters for district eCourts, High Court Services, eCourts judgments, NJDG, and Supreme Court India surfaces without captcha bypass
- Raw snapshot ingestion with stored payloads, parser runs, provenance fields, and normalization into canonical records
- Litigant and case memory generation with markdown artifacts as derived views and the database as the source of truth
- Judge and court profile snapshots with freshness, confidence, sample-size, and descriptive guardrails
- Merged chronology, hearing delta, filing lineage, connected matters, and hybrid retrieval APIs
- Matter cockpit public-docket panel plus a new court-intelligence workspace in the web app
- Integration and browser smoke coverage for the new vertical slice

## Post-Phase-6 Hardening

Status: `in_progress`

Delivered:

- Startup guardrails now reject the default JWT secret outside development and test
- Uploads enforce a configured size limit and sanitize stored file paths and file names
- Research memo export, saved authority retrieval, and quote-lock reads now enforce organization scoping
- Login throttling now blocks repeated failed attempts
- Browser auth storage now uses cookies only, with `Secure` enabled on HTTPS
- LIKE filters now escape wildcard characters, sequencing matching uses safer phrase boundaries, and scanned PDFs can fall back to OCR on embedded page images
- Integration coverage now includes tenant isolation, upload-size enforcement, and login throttling
- Native Windows local onboarding is now documented in `WindowsSetup.md`, including a full PowerShell and Docker Desktop setup path, verification steps, restart instructions, and troubleshooting guidance for friend-to-friend handoff

## Risks And Constraints

- Docker is still unavailable on this host, so compose services remain documented but not runtime-verified in this environment.
- The demo corpus is still intentionally narrow and focused on constitutional safeguards plus a synthetic detention bundle; broader verified case-law ingestion is still pending.
- General ingest is still best-effort FastAPI `BackgroundTasks`, while the court-intelligence slice now uses bounded job orchestration through `apps/worker-ai`.
- Bundle analysis is recomputed at matter scope after each processed document; large-bundle scaling still needs more granular job orchestration.
- Official public-court coverage currently favors user-assisted imports and non-protected surfaces; deeper connector breadth remains future work.
- Draft generation is deterministic and structured, but still template-driven pending a broader chamber-style corpus and eval suite.
- Browser e2e remains partially scaffolded and was not executed in this environment because Playwright tooling is not installed locally.

## Verification Completed

- `make lint`
- `make test`
- `make build-web`
- `python -m ruff check apps/api tests/bootstrap tests/integration`
- `python -m mypy apps/api/app`
- `python -m pytest tests/bootstrap tests/integration -q`
- `python -m pytest tests/integration/test_workflow_phases.py -q`
- `python -m pytest tests/integration/test_security_hardening.py -q`
- `python -m pytest tests/integration/test_court_intelligence_flow.py -q`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH apps/web/node_modules/.bin/tsc -p packages/contracts/tsconfig.build.json`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH apps/web/node_modules/.bin/tsc -p packages/ui/tsconfig.build.json`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH apps/web/node_modules/.bin/tsc -p apps/web/tsconfig.json --noEmit --incremental false`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH node_modules/.bin/next build`
- `cd apps/api && DATABASE_URL=sqlite+aiosqlite:///../../.data/migrate-phase345-smoke.db ../../.venv/bin/alembic upgrade head`
- `cd apps/api && DATABASE_URL=sqlite+aiosqlite:///../../.data/migrate-phase2-final.db ../../.venv/bin/alembic upgrade head`
- `cd apps/api && DATABASE_URL=sqlite+aiosqlite:///../../.data/court-intelligence-migrate.db ../../.venv/bin/alembic upgrade head`
- `PYTHONPATH=apps/api python apps/worker-ingest/src/worker_ingest.py --help`
- `DATABASE_URL=sqlite+aiosqlite:///./.data/court-intelligence-migrate.db PYTHONPATH=apps/api python apps/worker-ai/src/worker_ai.py --run-next`
- `cd apps/api && DATABASE_URL=sqlite+aiosqlite:///../../.data/run-smoke.db AUTO_CREATE_DB=true ../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010`
- `curl -s http://127.0.0.1:8010/api/v1/health` -> `{"message":"ok"}`
- `PATH=/usr/local/bin:$PATH COREPACK_HOME=/tmp/corepack /usr/local/bin/corepack pnpm --filter @legalos/web exec next start --hostname 127.0.0.1 --port 3000`
- `curl -I http://127.0.0.1:3000/login` -> `200 OK`

## Immediate Next Step

Broaden post-Phase-6 court-intelligence coverage: expand official connectors, production-validate pgvector-backed retrieval on Postgres, and deepen descriptive operational analytics without compromising provenance or guardrails.
