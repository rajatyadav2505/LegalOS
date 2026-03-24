# Quote Span Integrity Eval

## Goal

Ensure that exact quotes can only be emitted from stored quote spans with checksum validation.

## Phase 1 Checks

- Every ingested paragraph creates a `quote_span`.
- Quote checksum validation passes for the stored text and fails for a modified candidate.
- Research result cards render only `quote_text` from stored spans.
- The quote retrieval endpoint returns the exact stored span plus its checksum.
- Draft exports and redlines may rearrange text, but they must not invent new verbatim quotes outside stored spans.
