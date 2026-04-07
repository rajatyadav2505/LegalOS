# Refreshing Memory And Profiles

## Purpose

Explain how to refresh litigant memory, case memory, judge profiles, and court profiles.

## API Endpoints

- `POST /api/v1/parties/{party_id}/memory/refresh`
- `POST /api/v1/external-cases/{case_id}/memory/refresh`
- `POST /api/v1/judges/{judge_id}/profile/refresh`
- `POST /api/v1/courts/{court_id}/profile/refresh`
- `POST /api/v1/external-cases/{id}/sync`

## Worker Execution

Use the bounded intelligence worker for queued refreshes:

```bash
make drain-intelligence-jobs
```

To run a single claim attempt directly:

```bash
DATABASE_URL=sqlite+aiosqlite:///./.data/court-intelligence-migrate.db \
PYTHONPATH=apps/api \
python apps/worker-ai/src/worker_ai.py --run-next
```

## When To Refresh

- after importing a new official artifact
- after linking a new external case
- after parser improvements that materially change chronology or party resolution
- after profile metrics become stale

## Output Expectations

- database snapshot row created
- markdown artifact written under `memories/`
- prompt and model run metadata recorded when generation logic runs
- API surfaces updated for the next web refresh
