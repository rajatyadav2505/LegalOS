# ADR 0001: Modular Monolith With Worker Planes

## Status

Accepted

## Context

The product must serve litigation teams with high trust requirements: verified citations, quote-locked spans, provenance, auditability, and matter-level access control. It also needs to remain self-hostable and open-source friendly. The initial repository state is empty, so the architecture must be established before feature code is added.

The implementation must support:

- A web application for research, uploads, drafting, and review
- A Python API and domain layer
- Background processing for ingestion and AI-assisted workflows
- PostgreSQL as the source of truth
- Local filesystem object storage first, with S3-compatible extension points later
- Search abstraction that can start with Postgres full-text and later add OpenSearch
- Workflow abstractions that can later adopt Temporal without rewriting product logic

## Decision

Adopt a modular monolith with independently scalable worker planes.

### Primary Components

- `apps/web`: Next.js App Router frontend
- `apps/api`: FastAPI domain/API service
- `apps/worker-ingest`: parsing, OCR, extraction, chunking, indexing
- `apps/worker-ai`: research orchestration, drafting, contradiction analysis, strategy simulation

### Data And Infrastructure

- PostgreSQL stores core entities, provenance, quote spans, and audit data
- Bundle intelligence is materialized into Postgres tables for chronology events, document entities, exhibit references, and document relations
- pgvector supports private matter semantic retrieval
- Valkey is used for cache, queue, and ephemeral coordination
- Object storage starts with a local filesystem adapter
- Search starts with Postgres full-text, behind an interface

### Design Constraints

- No business logic in routes/controllers
- No ORM leakage into API responses
- All external data validated at boundaries
- Prompts and AI adapters remain versioned and isolated
- Source spans are the only allowed source of exact quotes

## Consequences

### Positive

- The system remains simple to develop and self-host early.
- Domain boundaries can be enforced without premature distributed-system complexity.
- Workers can scale independently as ingestion and AI workloads grow.
- Future migrations to OpenSearch, Temporal, or S3-compatible storage can happen behind interfaces.

### Negative

- A monolith requires discipline to keep module boundaries clean.
- Worker isolation is weaker than a fully distributed architecture.

### Mitigations

- Document architecture choices in ADRs.
- Use explicit domain packages and interfaces.
- Add tests for quote integrity, provenance, and boundary contracts early.
- Keep background execution behind worker-plane entrypoints so durable orchestration can replace FastAPI background tasks without rewriting domain services.

## Alternatives Considered

- Microservices: rejected because they add operational cost and slow early delivery.
- UI-only shell: rejected because the product requires real backend integration and provenance.
- Vendor-locked managed stack: rejected because the product must remain self-hostable.
