# LegalOS Local Setup on Windows

This guide is for running LegalOS on a native Windows 10/11 machine using PowerShell and Docker Desktop.

It avoids the repo `Makefile` because the current Make targets assume a Unix-style shell. If you prefer WSL2 or Git Bash, you can use the main [README.md](/Users/rajatyadav/LegalOS/README.md) instead. This file is the step-by-step Windows path.

## 1. Prerequisites

Install these first:

- Git for Windows
- Python `3.12.x`
- Node.js `20.x` or newer LTS
- Docker Desktop with WSL2 backend enabled
- PowerShell 7 or Windows PowerShell 5.1
- Optional: Tesseract OCR for local OCR outside containers

Recommended checks:

```powershell
git --version
py --version
node --version
corepack --version
docker --version
docker compose version
```

If your machine is strict about long file paths, run this once:

```powershell
git config --global core.longpaths true
```

## 2. Clone the repository

```powershell
git clone git@github.com:rajatyadav2505/LegalOS.git
cd LegalOS
```

If you do not use SSH for GitHub, use:

```powershell
git clone https://github.com/rajatyadav2505/LegalOS.git
cd LegalOS
```

## 3. Create the environment file

Copy the sample config:

```powershell
Copy-Item .env.example .env
```

Open `.env` and confirm these development-safe values:

- `APP_ENV=development`
- `APP_URL=http://localhost:3000`
- `API_URL=http://localhost:8000`
- `DATABASE_URL=postgresql+asyncpg://legalos:legalos@localhost:5432/legalos`
- `VALKEY_URL=redis://localhost:6379/0`
- `AUTO_CREATE_DB=false`
- `AUTO_SEED_DEMO=false`

Set a local JWT secret before you start:

```text
JWT_SECRET=legalos-local-dev-secret-change-this
```

## 4. Create and activate the Python virtual environment

From the repo root:

```powershell
py -3.12 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this in the current terminal and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Upgrade pip and install the API package with dev dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e "apps/api[dev]"
```

## 5. Install Node workspace dependencies

Enable Corepack and install the pnpm workspace:

```powershell
corepack enable
corepack pnpm install
```

## 6. Start the local infrastructure stack

Start PostgreSQL, Valkey, MinIO, and Apache Tika:

```powershell
docker compose -f .\infra\compose\docker-compose.yml up -d
```

Check that the containers are running:

```powershell
docker compose -f .\infra\compose\docker-compose.yml ps
```

Expected default ports:

- PostgreSQL: `5432`
- Valkey: `6379`
- MinIO API: `9000`
- MinIO Console: `9001`
- Tika: `9998`

## 7. Apply database migrations

Run Alembic from the API directory:

```powershell
cd .\apps\api
..\..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..\..
```

## 8. Seed the demo data

This creates the demo organization, user, matter, authorities, and sample records:

```powershell
cd .\apps\api
..\..\.venv\Scripts\python.exe -m app.db.seed
cd ..\..
```

Demo login:

- Email: `demo@legalos.local`
- Password: `DemoPass123!`

## 9. Start the API

Open a new PowerShell window at the repo root.

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start FastAPI:

```powershell
cd .\apps\api
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

## 10. Start the web app

Open a second PowerShell window at the repo root.

Start Next.js:

```powershell
corepack pnpm --filter @legalos/web dev
```

Open:

- Web app: `http://127.0.0.1:3000/login`
- API docs: `http://127.0.0.1:8000/api/docs`

## 11. Optional: recover queued document jobs

If the API restarts while uploads are queued, open a third PowerShell window at the repo root and run:

```powershell
$env:PYTHONPATH = "apps/api"
.\.venv\Scripts\python.exe .\apps\worker-ingest\src\worker_ingest.py --drain-queued --limit 25
```

This drains queued ingestion work through the worker plane.

## 12. First-run smoke test

Use the app vertically after login:

1. Sign in at `http://127.0.0.1:3000/login`.
2. Open the seeded matter from `/matters`.
3. Upload a document from the Upload workspace.
4. Open the Bundle Map and confirm chronology and contradiction data appears.
5. Open Research, search the seeded corpus, and save an authority.
6. Export the research memo.
7. Open Draft Studio and generate a petition or reply.
8. Open Strategy and Institutional Mode to confirm those workflows load.

## 13. Common Windows issues

### PowerShell blocks script execution

Use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### `corepack` is not found

Reinstall Node.js 20+ from the official installer, then reopen PowerShell.

### Docker containers do not start

- Confirm Docker Desktop is running.
- Confirm WSL2 backend is enabled in Docker Desktop settings.
- Check whether ports `5432`, `6379`, `9000`, `9001`, or `9998` are already in use.

### API cannot connect to Postgres

- Confirm `docker compose ... ps` shows `postgres` as running.
- Confirm `.env` still points to `localhost:5432`.
- Re-run the migration step after Postgres is healthy.

### Upload OCR is weak or missing

Install Tesseract on Windows if you want local OCR outside the container path.

Typical install path:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

If needed, add that folder to `PATH` and restart PowerShell.

### Ports 3000 or 8000 are already in use

Start the services on different ports and update `.env` accordingly. Example:

- web: `3001`
- API: `8001`

If you change ports, update:

- `APP_URL`
- `API_URL`
- `CORS_ORIGINS`

## 14. Shutdown

Stop the web server and API with `Ctrl+C` in their terminals.

Stop the infrastructure stack from the repo root:

```powershell
docker compose -f .\infra\compose\docker-compose.yml down
```

If you want to remove the named volumes too:

```powershell
docker compose -f .\infra\compose\docker-compose.yml down -v
```

## 15. Verification commands

After setup, these are the main checks:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests\bootstrap .\tests\integration -q
.\.venv\Scripts\python.exe -m ruff check .\apps\api .\tests\bootstrap .\tests\integration
.\.venv\Scripts\python.exe -m mypy .\apps\api\app
corepack pnpm --filter @legalos/web typecheck
corepack pnpm --filter @legalos/web build
```

## 16. What this guide does not require

- WSL2 shell usage for day-to-day app startup
- paid cloud services
- managed Postgres
- managed Redis
- S3

The baseline is local and self-hostable.
