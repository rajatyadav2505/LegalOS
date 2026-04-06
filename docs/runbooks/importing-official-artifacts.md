# Importing Official Artifacts

## Purpose

Describe the lawful import path for official public-court artifacts.

## Supported Import Modes

1. Non-protected official fetch surfaces through a connector.
2. User-assisted import of downloaded HTML, PDF, or JSON from an official portal.
3. Optional operator-assisted session workflows when implemented explicitly and lawfully.

## Explicit Non-Support

- no captcha bypass
- no covert scraping
- no fake provenance reconstruction

## Supported Artifact Types

- case history pages
- cause lists
- order PDFs
- judgment PDFs
- exported JSON where an official source provides it

## API Flow

1. Call `POST /api/v1/matters/{matter_id}/external-cases/import`.
2. Provide `source_system`, `artifact_kind`, optional `source_url`, optional `observed_at`, and the uploaded file.
3. Inspect the returned external-case summary.
4. Open the court-intelligence workspace to review chronology, filings, memory, and profile output.

## What Gets Stored

- raw snapshot payload
- content hash
- parser run metadata
- normalized canonical records
- generated memory/profile artifacts when refresh completes

## Review Expectations

- Check provenance badges before relying on any normalized output.
- Re-run import only when a corrected artifact or parser version is available.
- Treat markdown memories as generated views; use the database-backed API state as the source of truth.
