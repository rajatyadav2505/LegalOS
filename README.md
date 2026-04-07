# LegalOS

India-first litigation operating system for advocates, chambers, senior briefing teams, and DLSA or institutional legal-aid workflows.

LegalOS is not a generic legal chatbot. It is a source-grounded litigation workspace built around verified research, quote-safe citation handling, matter-bundle intelligence, structured drafting, bounded strategy support, institutional auditability, and bounded court-intelligence ingestion from official public surfaces.

## Current Scope

This repository contains a modular monolith plus worker planes with Phase 0 through Phase 6 implemented as runnable local slices:

- Research and precedent engine with verified citations, exact quote spans, saved authorities, and memo export
- Document operating system with uploads, extraction, OCR-backed image handling, chunking, quote-lock spans, and matter/public-law search
- Bundle intelligence with chronology, contradictions, duplicate groups, exhibit links, clustering, and ingest-state visibility
- Drafting studio with structured draft schemas, style packs, unresolved placeholders, annexure scheduling, markdown export, and redlines
- Strategy engine with best/fallback/risk lines, issue cards, rebuttal cards, bench questions, bounded scenario branches, and lawful sequencing guidance
- Institutional mode with approval requests, reviews, audit visibility, low-bandwidth summaries, and plain-language English/Hindi matter briefs
- Court-intelligence layer with official-artifact ingestion, canonical court and docket models, litigant and case memory snapshots, judge and court profiles, hybrid retrieval, and a bounded orchestration worker

## Trust Rails

The product is designed around litigation-grade traceability:

- No fabricated authorities, citations, or verbatim quotes
- Exact quotes render only from stored `quote_spans` with checksums
- Drafting uses saved verified authorities, not freehand citation insertion
- Public court artifacts are stored as raw snapshots before normalization, with source system, fetch metadata, checksums, parser version, confidence, and verification status
- Markdown memories are generated views only; the database remains the source of truth
- “Hide information” is implemented as a lawful sequencing console, not concealment coaching
- Strategy output is explicitly decision support only, not certainty or outcome prediction
- Matter access is organization-scoped from the API boundary inward
- Official-court connectors do not attempt captcha bypass or covert scraping

## Architecture

### Application shape

- `apps/web`: Next.js App Router + TypeScript frontend
- `apps/api`: FastAPI + SQLAlchemy + Pydantic backend
- `apps/worker-ingest`: ingest drain path for queued document processing
- `apps/worker-ai`: bounded orchestration worker for public-court sync, memory refresh, profile refresh, and hybrid-index jobs
- `packages/contracts`: shared typed contracts used by the web client
- `packages/ui`: shared UI primitives
- `packages/prompts`: versioned prompt and template assets

### Data and infrastructure

- PostgreSQL is the source of truth
- Full-text search starts in PostgreSQL
- Hybrid retrieval combines Postgres-backed lexical candidate selection with pgvector-ready embeddings behind adapter interfaces
- Valkey is reserved for cache, queue, and ephemeral coordination
- Local filesystem storage is the default object-storage adapter
- MinIO and Apache Tika are available in the local compose stack for self-hosted evolution

### Product boundaries

- Modular monolith first, not premature microservices
- Worker-plane boundaries are present and a bounded jobs table now backs intelligence refresh flows, while keeping orchestration behind interfaces for future Temporal adoption
- Search, storage, model-provider, and workflow concerns are kept behind service/repository boundaries to stay self-hostable and vendor-neutral

### Runtime responsibilities

- Web: matter cockpit, research canvas, bundle map, court-intelligence workspace, draft studio, strategy workspace, and institutional dashboards
- API: authentication, organization and matter access control, ingest orchestration, search, public-court normalization, memory/profile generation, and audit persistence
- Worker ingest: queued document recovery and large-bundle catch-up processing
- Worker AI: bounded intelligence job execution kept separate from the domain core

## Repository Layout

```text
apps/
  api/             FastAPI domain and API service
  web/             Next.js web application
  worker-ingest/   queued ingest drain path
  worker-ai/       AI worker-plane boundary

packages/
  contracts/       shared typed API contracts
  ui/              shared design system primitives
  prompts/         versioned drafting and strategy prompt assets
  config/          reserved shared config package
  types/           reserved shared types package

docs/
  adr/             architecture decision records
  product/         product overview
  runbooks/        local-dev, self-hosting, testing guides
  evals/           product-specific trust and quality eval docs

infra/
  compose/         local container stack
  env/             example environment files
  scripts/         bootstrap and tooling helpers

tests/
  fixtures/        demo corpus and matter bundle
  integration/     API + DB workflow coverage
  e2e/             Playwright browser smoke specs
```

## Demo Credentials

- Email: `demo@legalos.local`
- Password: `DemoPass123!`

## Local Setup

For a native Windows 10/11 walkthrough using PowerShell and Docker Desktop, use [WindowsSetup.md](./WindowsSetup.md). The repo `Makefile` supports macOS, Linux, WSL, and Git Bash on Windows; the PowerShell guide remains the most direct native-Windows path.

### Prerequisites

- Python 3.12+
- Node.js 20+
- `corepack`
- Docker or an already-running local Postgres/Valkey-compatible stack
- Tesseract if you want OCR paths to run outside containers

### Bootstrapping

1. Copy [`.env.example`](./.env.example) to `.env`.
2. Run `make setup`.
3. Start infrastructure with `make compose-up`.
4. Apply migrations with `make migrate`.
5. Seed demo data with `make seed`.
6. Start the API with `make dev-api`.
7. Start the web app with `make dev-web`.
8. If queued documents need recovery after a restart, run `make drain-queued`.
9. If intelligence jobs remain queued, run `make drain-intelligence-jobs`.

### Core commands

- `make lint`
- `make test`
- `make build-web`
- `make migrate`
- `make seed`
- `make compose-up`
- `make compose-down`
- `make drain-queued`
- `make drain-intelligence-jobs`

## Configuration

Use [`.env.example`](./.env.example) as the baseline. The sample file now defaults to migration-first and safer runtime behavior:

- `AUTO_CREATE_DB=false`: schema changes should come from Alembic, not implicit startup DDL
- `AUTO_SEED_DEMO=false`: seed explicitly with `make seed` so demo writes are intentional
- `JWT_SECRET`: set a real secret before any non-local deployment
- `MAX_UPLOAD_SIZE_BYTES=26214400`: default 25 MB request ceiling for direct uploads
- `LOGIN_RATE_LIMIT_ATTEMPTS=5` and `LOGIN_RATE_LIMIT_WINDOW_SECONDS=300`: baseline login throttling
- `LOCAL_STORAGE_DIR=.data/storage`: local filesystem object-storage adapter root
- `EMBEDDING_PROVIDER`, `RERANKER_PROVIDER`, and `GENERATION_PROVIDER`: adapter selection for the bounded intelligence plane
- `HYBRID_EMBEDDING_DIMENSIONS`: deterministic embedding width for the default local adapter

For local development, the intended path is:

1. keep `APP_ENV=development`
2. run `make compose-up`
3. run `make migrate`
4. run `make seed`
5. start `make dev-api` and `make dev-web`

## Demo Workflow

Use the seeded matter to walk the product vertically:

1. Open `/login` and sign in with the demo user.
2. Open the matter cockpit from `/matters`.
3. Upload one or more matter documents from the Upload workspace.
4. Open the Bundle Map and confirm chronology, contradictions, duplicates, exhibit links, and ingest state.
5. Search the Research workspace and save at least one verified authority.
6. Export the research memo.
7. Open Draft Studio, optionally create a style pack, and generate a structured petition or reply.
8. Export the draft and compare versions with the redline view.
9. Open Strategy Engine and review best/fallback/risk lines, issue cards, and the sequencing console.
10. Open Institutional Mode, request approval for the latest draft, review it, and inspect the audit trail and low-bandwidth brief.
11. Open the Court Intelligence workspace, import an official court artifact, and inspect the merged chronology, memory cards, and profile cards.

## Security and Hardening Notes

The current codebase now includes:

- startup guardrails against the default JWT secret outside development/test
- migration-first defaults in config and `.env.example`
- safer upload handling with a configured size limit
- sanitized local-storage paths and safer stored file names
- organization scoping for quote-span lookup, saved authority retrieval, quote-lock reads, and memo export
- provenance-preserving storage and normalization for imported official court artifacts
- organization-scoped public-court memories, profiles, and connected-matter search
- login throttling for repeated failed attempts
- cookie-only browser token storage with `Secure` enabled on HTTPS
- safer LIKE filtering to avoid wildcard manipulation in search filters
- regex-based sequencing keyword matching to reduce false positives

These hardening changes were driven by an external assessment review. Two items from that review were adjusted rather than accepted verbatim:

- the search filter issue was not raw SQL injection, but it was still worth fixing as LIKE wildcard manipulation
- the matter list path was not a classic N+1 in its current loader configuration, but it was still inefficient and is now count-aggregated plus paginated

## Verification

The repository has been verified with the following commands:

- `make lint`
- `make test`
- `make build-web`
- `python -m ruff check apps/api tests/bootstrap tests/integration`
- `python -m mypy apps/api/app`
- `python -m pytest tests/bootstrap tests/integration -q`
- `python -m pytest tests/integration/test_court_intelligence_flow.py -q`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH apps/web/node_modules/.bin/tsc -p packages/contracts/tsconfig.build.json`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH apps/web/node_modules/.bin/tsc -p packages/ui/tsconfig.build.json`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH apps/web/node_modules/.bin/tsc -p apps/web/tsconfig.json --noEmit --incremental false`
- `PATH=/usr/local/bin:/opt/homebrew/bin:$PATH node_modules/.bin/next build`
- `DATABASE_URL=sqlite+aiosqlite:///./.data/court-intelligence-migrate.db PYTHONPATH=apps/api python apps/worker-ai/src/worker_ai.py --run-next`

## Tests and Evals

### Current automated coverage

- `tests/integration/test_quote_lock.py`
- `tests/integration/test_research_flow.py`
- `tests/integration/test_bundle_flow.py`
- `tests/integration/test_workflow_phases.py`
- `tests/integration/test_security_hardening.py`
- `tests/integration/test_court_intelligence_flow.py`
- `tests/e2e/research-smoke.spec.ts`
- `tests/e2e/workflows-smoke.spec.ts`
- `tests/e2e/court-intelligence-smoke.spec.ts`

### Product eval docs

See [docs/evals/citation-integrity.md](./docs/evals/citation-integrity.md), [docs/evals/quote-span-integrity.md](./docs/evals/quote-span-integrity.md), [docs/evals/chronology-fidelity.md](./docs/evals/chronology-fidelity.md), [docs/evals/memory-grounding.md](./docs/evals/memory-grounding.md), [docs/evals/profile-safety.md](./docs/evals/profile-safety.md), [docs/evals/retrieval-relevance.md](./docs/evals/retrieval-relevance.md), [docs/evals/missing-record-detection.md](./docs/evals/missing-record-detection.md), [docs/evals/source-attribution-integrity.md](./docs/evals/source-attribution-integrity.md), [docs/evals/draft-completeness.md](./docs/evals/draft-completeness.md), [docs/evals/strategy-boundedness.md](./docs/evals/strategy-boundedness.md), and [docs/evals/institutional-auditability.md](./docs/evals/institutional-auditability.md).

## Self-Hosting Notes

The local baseline is aimed at a Mac mini or Linux self-hosted deployment:

- open-source/self-hostable components first
- no hardwired paid cloud dependencies in the domain model
- filesystem object storage works first, with future S3-compatible evolution
- compose stack includes Postgres, Valkey, MinIO, and Tika
- web and API can also run against an already-provisioned local stack
- official court ingestion supports lawful feeds and user-assisted imports first; captcha-protected surfaces require manual or operator-assisted paths rather than bypass

See [docs/runbooks/self-hosting.md](./docs/runbooks/self-hosting.md) for deployment expectations and security notes.

## Important Limitations

- Docker Compose is documented but was not runtime-verified on this host because Docker is unavailable here.
- Official-court coverage is still selective and grounded in user-assisted imports plus non-protected surfaces; broader connector coverage remains future work.
- Drafting is structured and production-usable, but still template-driven pending broader corpus and style eval work.
- The demo corpus is intentionally narrow and does not yet represent a production-scale verified Indian case-law corpus.
- Browser e2e specs exist but were not executed in this environment because Playwright tooling is not installed locally.

## Troubleshooting

- If the API refuses to start outside development, check `JWT_SECRET` and confirm `AUTO_CREATE_DB=false`.
- If uploads remain queued after an interrupted API process, run `make drain-queued`.
- If court-intelligence refresh jobs remain queued, run `make drain-intelligence-jobs`.
- If OCR output is sparse, confirm Tesseract is installed on the host or available in the container path.
- If an official import does not normalize as expected, inspect the raw snapshot and parser-run metadata before retrying.
- If the web app builds but auth fails locally, verify `APP_URL`, `API_URL`, and CORS settings in `.env`.

## Documentation

- [docs/product/overview.md](./docs/product/overview.md)
- [docs/adr/0001-architecture.md](./docs/adr/0001-architecture.md)
- [docs/adr/0002-public-data-ingestion-strategy.md](./docs/adr/0002-public-data-ingestion-strategy.md)
- [docs/adr/0003-bounded-intelligence-orchestration.md](./docs/adr/0003-bounded-intelligence-orchestration.md)
- [docs/adr/0004-litigant-memory-design.md](./docs/adr/0004-litigant-memory-design.md)
- [docs/adr/0005-profile-guardrails.md](./docs/adr/0005-profile-guardrails.md)
- [docs/adr/0006-hybrid-retrieval-architecture.md](./docs/adr/0006-hybrid-retrieval-architecture.md)
- [docs/runbooks/local-dev.md](./docs/runbooks/local-dev.md)
- [docs/runbooks/importing-official-artifacts.md](./docs/runbooks/importing-official-artifacts.md)
- [docs/runbooks/refreshing-memory-and-profiles.md](./docs/runbooks/refreshing-memory-and-profiles.md)
- [docs/runbooks/troubleshooting-connector-failures.md](./docs/runbooks/troubleshooting-connector-failures.md)
- [docs/runbooks/testing.md](./docs/runbooks/testing.md)
- [WindowsSetup.md](./WindowsSetup.md)
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)
- [BACKLOG.md](./BACKLOG.md)

## Next Priorities

Post-Phase-6 work is now mostly broadening and hardening:

- broader official connector coverage and normalization depth across Indian courts
- richer descriptive profiling windows and connected-matter heuristics
- pgvector-backed production validation against a live Postgres deployment
- stronger OCR and scanned-bundle scaling
- CI-executed browser e2e and broader eval automation
