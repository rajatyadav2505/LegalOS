# Self-Hosting Runbook

## Purpose

Run LegalOS on a self-hosted Mac mini or Linux box without relying on proprietary cloud dependencies.

## Baseline Requirements

- Container runtime
- PostgreSQL
- Valkey
- Web application
- API service
- Background workers
- Persistent storage for exports and audit logs

## Hosting Principles

- Use open-source or self-hostable components by default.
- Keep object storage pluggable, with a filesystem adapter available first.
- Keep search and workflow orchestration behind interfaces so future infrastructure changes do not rewrite domain logic.
- Maintain matter-level access control and audit logging from the start.

## Deployment Expectations

The initial self-hosted setup should provide:

- Configurable environment variables
- Migrations and seed steps
- Health checks for app and worker services
- Clear log locations
- Draft export availability
- Approval workflow persistence
- Audit log retention
- Plain-language summary generation
- A path to later reverse-proxy deployment

## Current Self-Hosted Baseline

- infrastructure compose file at `infra/compose/docker-compose.yml`
- Postgres source of truth
- Valkey for future cache/queue coordination
- MinIO and Tika available as self-hostable adapters
- local filesystem storage adapter active in the API
- web and API processes started separately via `make dev-web` and `make dev-api`
- drafting, strategy, and institutional routes are available in the same local web and API baseline

## Security Notes

- Store secrets in environment variables, not in git.
- Separate public law corpus data from private matter data.
- Protect uploads, exports, and AI outputs as sensitive matter content.
- Institutional mode increases auditability and approval visibility, so log retention and access policies should be planned early.
