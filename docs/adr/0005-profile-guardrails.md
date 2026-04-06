# ADR 0005: Judge And Court Profiling Guardrails

## Status

Accepted

## Context

The platform needs judge-specific and court-specific intelligence for hearing preparation and operational understanding. These features are especially sensitive because they can be misread as deterministic predictions or advocacy shortcuts.

## Decision

Provide descriptive operational profiles only, never deterministic outcome prediction.

Profile cards must:

- show freshness or staleness
- show sample size
- show confidence bands
- suppress low-coverage metrics
- enforce minimum sample thresholds
- avoid labels such as "pro-petitioner" or "pro-defendant"

Metrics are limited to descriptive workflow signals such as listing density, adjournment share, hearing load, order-upload lag, and roster history.

## Consequences

### Positive

- The UI remains useful for preparation without pretending to predict judicial outcomes.
- Low-coverage data is surfaced honestly.
- Operators can reason about court operations with visible confidence and freshness.

### Negative

- Some users may want stronger predictive claims that the product intentionally does not offer.
- Metric design requires continual review as connector breadth expands.

## Alternatives Considered

- Outcome prediction labels: rejected as unsafe, overconfident, and not aligned with trust requirements.
- Hiding uncertainty behind simple scores: rejected because it obscures coverage and staleness.
