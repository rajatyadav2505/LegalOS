# Worker Ingest

Worker-plane entrypoint for filesystem-to-document ingestion jobs.

Current modes:

- Ingest a filesystem job envelope into the API/domain pipeline.
- Process a specific queued document with `--document-id`.
- Drain queued documents in created order with `--drain-queued --limit N`.

This is the supported Phase 2 recovery path for queued ingest if the API process restarts before FastAPI background tasks complete. Queue execution is still best-effort today; durable orchestration is a later milestone.
