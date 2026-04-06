# ADR 0004: Litigant And Case Memory Design

## Status

Accepted

## Context

LegalOS needs durable memory for litigants, external cases, and optionally matters. These memories should support chronology review, recurring claims, contradiction analysis, and hearing preparation. The product requirements state that markdown memory files are generated views, not the source of truth.

## Decision

Store canonical memory state in database snapshot tables and generate markdown artifacts as derived representations.

The design uses:

- `litigant_memory_snapshots`
- `case_memory_snapshots`
- storage-backed markdown outputs under `memories/litigants/`, `memories/cases/`, and `memories/matters/`

Memory generation must:

- reject unsupported assertions
- cite source references for every non-trivial assertion
- preserve confidence and verification status
- remain organization-scoped and auditable

## Consequences

### Positive

- The database remains authoritative for refresh, comparison, and API retrieval.
- Markdown artifacts are still easy to review, export, and inspect in storage.
- Memory content can be regenerated safely when parsers or canonical data improve.

### Negative

- The system must keep snapshot tables and markdown artifacts consistent.
- Manual override flows need careful design so they do not obscure provenance.

## Alternatives Considered

- Markdown files as the primary system of record: rejected because they are hard to query, scope, and audit.
- Free-form generated memory without citations: rejected because it undermines trust.
