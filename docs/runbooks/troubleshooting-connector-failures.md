# Troubleshooting Connector Failures

## Purpose

Provide a recovery checklist for public-court connector or parser failures.

## Common Failure Modes

- unsupported artifact structure
- malformed or partial downloaded HTML
- scanned PDF with weak OCR
- missing identifiers such as CNR or case number
- stale parser assumptions after a portal layout change

## First Checks

1. Confirm the artifact came from an official source.
2. Confirm the file type matches the chosen `artifact_kind`.
3. Confirm the raw snapshot was stored successfully.
4. Inspect `parser_runs` and any recorded error messages.
5. Verify the content hash changed before retrying with a new artifact.

## Safe Recovery Steps

- re-import a cleaner official download
- retry after updating parser logic
- refresh linked memories and profiles after normalization succeeds
- keep unsupported assertions out of memory and profile outputs until source data improves

## Guardrails

- do not add portal-specific bypass code for protected surfaces
- do not hand-edit normalized records to mask parser defects
- do not delete raw snapshots that are still needed for audit or parser comparison
