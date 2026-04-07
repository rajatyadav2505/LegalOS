# Local Development Runbook

## Purpose

Run the LegalOS repository locally for development in a self-hostable setup.

For native Windows setup, use the step-by-step [WindowsSetup.md](../../WindowsSetup.md) guide. It covers PowerShell, Docker Desktop, local verification, worker recovery, and common Windows-specific issues. If you are using WSL or Git Bash on Windows, the repo `Makefile` now resolves the Windows virtualenv layout automatically.

## Expected Local Stack

- Next.js web app
- FastAPI API
- Worker processes for ingestion and AI orchestration
- PostgreSQL
- Valkey
- Optional local object storage adapter

## Environment

Use `.env.example` as the starting point for environment configuration.
Keep `AUTO_CREATE_DB=false` and prefer `make migrate` so local development follows the same schema path as production.
Keep `AUTO_SEED_DEMO=false` unless you intentionally want startup-side demo writes; the normal path is `make seed`.

## Setup

1. Copy `.env.example` to `.env`.
2. Run `make setup`.
3. Start infrastructure with `make compose-up`.
4. Apply migrations with `make migrate`.
5. Seed the demo corpus with `make seed`.
6. Start the API with `make dev-api`.
7. Start the web app with `make dev-web`.
8. If documents remain queued after an API restart, process them with `make drain-queued`.
9. If intelligence refresh jobs remain queued after an API restart, process them with `make drain-intelligence-jobs`.

The seeded demo login is:

- `demo@legalos.local`
- `DemoPass123!`

## Recommended Workflow

1. Open `/login` in the browser.
2. Sign in with the demo user.
3. Open the matter cockpit from `/matters`.
4. Upload a matter document from the Upload workspace.
5. Open the Bundle Map and confirm ingest state, chronology, contradictions, duplicates, and exhibit links appear after processing.
6. Run a search from the Research workspace and save at least one authority.
7. Open Draft Studio, create or select a style pack, and generate a structured draft.
8. Export the draft and review a redline after generating a second version.
9. Open Strategy Engine and review issue cards, scenario branches, and sequencing guidance.
10. Open Institutional Mode, request approval for the latest draft, and review the resulting audit trail.
11. Export the memo from the Research workspace.
12. Open the Court Intelligence workspace, import an official court artifact, and inspect chronology, memory, and profile cards.

## Acceptance Checks

- The web app responds in a browser.
- The API exposes a health endpoint.
- Migrations apply cleanly.
- Seed data loads without manual fixes.
- Upload, research, and bundle-map flows run against the demo fixtures.
- Draft generation, export, and redline work from the seeded matter.
- Style pack creation succeeds and affects later draft output.
- Strategy workspace and sequencing review load without frontend or API errors.
- Institutional approval request and review flows persist and appear in the dashboard audit trail.
- Low-bandwidth institutional mode renders a usable brief.
- Queued documents can be recovered with `make drain-queued`.
- Imported official court artifacts normalize into an external case with provenance.
- Court-intelligence jobs can be recovered with `make drain-intelligence-jobs`.

## Operational Notes

- Keep secrets out of the repository.
- Prefer containerized services for repeatable local setup.
- Do not depend on paid cloud services for the baseline development path.
- Docker is required for `make compose-up`, but the API and web app can still be developed against an existing local Postgres/Valkey stack if needed.
- Background ingest is currently best-effort `BackgroundTasks`; the worker drain command is the supported recovery path until durable queue orchestration lands.
- The court-intelligence slice uses bounded jobs in `apps/worker-ai`, but public-court ingestion still favors lawful feeds and user-assisted imports over automated access to protected portals.
- Drafting is structured and deterministic; broader style fidelity will improve as the verified corpus expands.
