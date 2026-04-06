# ADR 0003: Bounded Intelligence Orchestration

## Status

Accepted

## Context

The court-intelligence slice needs background execution for external-case sync, public artifact normalization, memory refresh, profile refresh, and hybrid indexing. The product must not rely on an unbounded agent swarm, but it should preserve a clean path toward a more durable workflow engine such as Temporal later.

## Decision

Use a bounded jobs subsystem inside the modular monolith and execute it through `apps/worker-ai`.

The orchestration shape includes:

- `jobs`
- `job_attempts`
- `job_artifacts`
- `prompt_runs`
- `model_runs`

Jobs use typed payloads, idempotency keys, retry policy, bounded failure states, and audit-aware sensitive execution. Pipeline stages are implemented as typed services such as fetch, extract, normalize, party resolution, chronology, profile, retrieval, drafting planning, and quality guard services.

## Consequences

### Positive

- The worker plane becomes real and testable without introducing microservices.
- Model and prompt execution remain auditable.
- Future Temporal adoption can happen behind interfaces instead of forcing a rewrite.

### Negative

- The first implementation is simpler than a full durable workflow engine.
- General ingest still uses existing best-effort patterns and has not yet fully migrated to the jobs subsystem.

## Alternatives Considered

- Unbounded agent framework: rejected because the product needs predictable, testable, source-aware behavior.
- Direct route-level execution for every intelligence task: rejected because long-running refresh paths need retry and artifact tracking.
