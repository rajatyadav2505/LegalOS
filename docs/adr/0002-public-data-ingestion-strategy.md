# ADR 0002: Public Data Ingestion Strategy

## Status

Accepted

## Context

LegalOS needs to ingest official public-court information for Indian litigation without compromising provenance, legality, or trust. Many useful public surfaces exist across district eCourts, High Court services, Supreme Court India, NJDG, and judgments portals. Some are straightforward to import, while others are captcha-protected or otherwise unsuitable for unattended fetches.

The product requirements explicitly reject:

- captcha bypass
- covert scraping
- fake or inferred provenance
- markdown memories as the primary store

## Decision

Adopt a provenance-first public-data ingestion strategy with three lawful modes:

1. official-feed or non-protected fetch adapters where the surface is openly accessible
2. user-assisted import of downloaded HTML, PDF, JSON, or copied metadata from official portals
3. optional operator-triggered session-assisted fetch ports only when implemented explicitly and lawfully

All public imports must store a raw snapshot before normalization.

## Required Provenance

Every normalized public record carries:

- `source_system`
- `source_url`
- `raw_snapshot_id`
- `observed_at`
- `fetched_at`
- `content_hash`
- `parser_version`
- `confidence`
- `verification_status`

## Consequences

### Positive

- The system can ingest official court data without pretending protected surfaces are fully automatable.
- Raw snapshots remain available for parser re-runs and manual review.
- Canonical records stay traceable back to a concrete source artifact.

### Negative

- Coverage grows more slowly than an aggressive scraping approach.
- Operator and user-assisted imports remain part of the workflow for some courts.

## Alternatives Considered

- Fully automated scraping of protected surfaces: rejected as unlawful and brittle.
- Storing only normalized records without raw artifacts: rejected because it weakens auditability and parser recovery.
