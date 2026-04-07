# LegalOS API

FastAPI service for the LegalOS modular monolith.

## Responsibilities

- Authentication and matter-scoped access control
- Document metadata, storage, extraction, and indexing orchestration
- Research search, quote-lock enforcement, and memo export
- Contracts consumed by the web frontend and worker planes

## Local Commands

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

On Windows PowerShell, activate the environment with `.\.venv\Scripts\Activate.ps1` before running the same `python -m pip` or `python -m uvicorn` commands.
