# ADR 0006: Hybrid Retrieval Architecture

## Status

Accepted

## Context

Court intelligence needs retrieval across private matter data, public-court events, filings, memories, and profiles. The platform must remain self-hostable, vendor-neutral, and compatible with PostgreSQL-first deployment while leaving room for richer retrieval later.

## Decision

Adopt hybrid retrieval behind adapter interfaces:

- PostgreSQL-backed lexical filtering remains supported
- embeddings are produced through an embedding adapter interface
- reranking is produced through a reranker adapter interface
- generation stays behind a chat or generation adapter interface
- `hybrid_index_entries` stores retrieval-ready records and pgvector-compatible embeddings

The first implementation uses deterministic local adapters so the product stays runnable without a hard dependency on a paid model vendor.

## Consequences

### Positive

- Retrieval can span public and private records through one abstraction.
- pgvector-backed production evolution stays possible without rewriting domain logic.
- Providers remain configurable by environment.

### Negative

- The deterministic local adapters are a baseline, not a final relevance ceiling.
- Query quality will improve further as production vector search is validated on live Postgres.

## Alternatives Considered

- PostgreSQL lexical search only: rejected because court-intelligence retrieval benefits from semantic similarity.
- Hardwiring a single hosted model vendor: rejected because the product must remain self-hostable and adapter-driven.
