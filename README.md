# LegalOS

Indian litigation operating system for advocates, chambers, and institutional legal-aid teams.

This repository is implemented as a modular monolith with worker planes. Phase 0 through Phase 5 are now delivered as runnable local slices: a FastAPI backend, a Next.js App Router frontend, typed workspace packages, local compose infrastructure, seeded demo data, quote-lock research flows, bundle intelligence, structured drafting, bounded strategy support, and institutional approval and audit workflows.

## Phase 0 / 5 Delivered

- `apps/api`: auth, matter, document upload, extraction, chunking, quote spans, research search, saved authorities, memo export
- `apps/api`: chronology, contradiction, duplicate, exhibit-link, and bundle-map APIs
- `apps/api`: style packs, structured draft generation, annexures, verified-authority insertion, markdown export, and redlines
- `apps/api`: strategy workspace, issue cards, bench questions, rebuttal cards, bounded scenario branches, and sequencing console guardrails
- `apps/api`: institutional dashboard, approvals, audit trail, low-bandwidth brief, and plain-language English/Hindi summaries
- `apps/web`: login, matter index, matter cockpit, upload workspace, research canvas, bundle map workspace, draft studio, strategy engine, and institutional mode
- `apps/worker-ingest` and `apps/worker-ai`: worker-plane entrypoints with a runnable ingest drain path
- `packages/contracts`: typed web/API contracts
- `packages/ui`: shared UI primitives with buildable workspace packaging
- `infra/compose`: Postgres, Valkey, MinIO, and Tika local stack
- `tests/fixtures`: demo matter bundle and verified public-law excerpts
- `tests/integration`: quote-lock, research flow, bundle intelligence, drafting, strategy, sequencing, and institutional approval coverage

## Demo Credentials

- Email: `demo@legalos.local`
- Password: `DemoPass123!`

## What This Repo Will Contain

- `apps/web`: Next.js App Router frontend
- `apps/api`: FastAPI domain/API service
- `apps/worker-ingest`: document parsing, OCR, extraction, chunking, indexing
- `apps/worker-ai`: research orchestration, drafting, contradiction analysis, strategy support
- `packages/*`: shared UI, contracts, prompts, config, and types
- `docs/*`: architecture decisions, product notes, runbooks, and evals
- `infra/*`: local development and self-hosting assets

## Local Setup

1. Copy [`.env.example`](/Users/rajatyadav/LegalOS/.env.example) to `.env`.
2. Run `make setup`.
3. Start infrastructure with `make compose-up`.
4. Apply migrations with `make migrate`.
5. Seed demo data with `make seed`.
6. Start the API with `make dev-api`.
7. Start the web app with `make dev-web`.
8. Optionally drain queued ingest jobs with `make drain-queued`.

## Verification Commands

- `make lint`
- `make test`
- `make build-web`

## Product Principles

- No fabricated authorities, citations, or quote spans
- Quote-lock for exact quoted text from stored source spans only
- Self-hostable, open-source friendly, and containerized by default
- Modular monolith first, not premature microservices
- Provenance, auditability, and access control are first-class
- AI features are decision support, not legal certainty

## Current Status

Phase 0 through Phase 5 are in place. The current corpus uses verified Constitution excerpts with stored quote spans, including Article 22 safeguards, and the demo matter bundle exercises upload, extraction, research, saved authority handling, memo export, chronology generation, contradiction surfacing, duplicate detection, structured draft generation, redlines, bounded strategy review, lawful sequencing guidance, institutional approvals, audit events, and low-bandwidth summaries.

## Operational Caveats

- Docker Compose is documented but not runtime-verified on this host because Docker is unavailable here.
- Background ingest is currently best-effort FastAPI `BackgroundTasks` plus the explicit `make drain-queued` worker path, not a durable queue.
- Bundle analysis rebuilds matter-level intelligence after each processed document, which is acceptable for Phase 2 but should move to more granular orchestration in later phases.
- Drafting is structured and traceable, but still template-driven rather than learned from a larger verified chamber corpus.
- Strategy, sequencing, and institutional summaries are explicitly decision support only and must not be treated as certainty or outcome prediction.

## Next Milestones

1. Durable workflow execution with queue-backed ingest and AI orchestration boundaries.
2. Broader verified case-law and statute corpus beyond the seeded constitutional baseline.
3. OCR and large-bundle hardening for scanned production records.
4. Expanded Playwright and product-eval automation on a fully provisioned self-hosted stack.
