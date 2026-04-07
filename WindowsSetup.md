# LegalOS Local Setup on Windows

This guide is the Windows-first path for running LegalOS locally on a native Windows 10 or Windows 11 machine with PowerShell and Docker Desktop.

Use this guide if your friend wants the most direct setup on Windows without relying on Git Bash or WSL. The repo `Makefile` supports Git Bash on Windows, but native PowerShell users should still follow the explicit commands below.

If they prefer WSL2 or Git Bash, they can use the main [README](./README.md) and [local development runbook](./docs/runbooks/local-dev.md) instead.

## 1. What this setup gives you

After completing this guide, the machine will be able to run:

- the FastAPI backend on `http://127.0.0.1:8000`
- the Next.js frontend on `http://127.0.0.1:3000`
- PostgreSQL, Valkey, MinIO, and Apache Tika through Docker Desktop
- the seeded demo matter and demo login

Demo login after seeding:

- Email: `demo@legalos.local`
- Password: `DemoPass123!`

## 2. Before you start

Use a normal local folder such as `C:\dev\LegalOS` or `D:\projects\LegalOS`.

Avoid placing the repo inside:

- OneDrive-synced folders
- folders with very restrictive corporate antivirus rules
- deeply nested paths

Recommended minimum machine setup:

- Windows 10 or 11
- 16 GB RAM preferred
- at least 10 GB free disk space
- admin access to install Docker Desktop and language runtimes

## 3. Install the required software

Install these tools first:

1. Git for Windows
2. Python `3.12.x`
3. Node.js `20.x` or newer LTS
4. Docker Desktop
5. PowerShell 7 or Windows PowerShell 5.1
6. Optional: Tesseract OCR for stronger local OCR behavior

Recommended install notes:

- During Python install, enable `Add python.exe to PATH`.
- During Docker Desktop setup, enable the WSL2-based engine.
- After Docker Desktop installs, open it once and let it finish initialization.

## 4. Confirm the toolchain works

Open PowerShell and run:

```powershell
git --version
py --version
node --version
corepack --version
docker --version
docker compose version
```

You should see version output for all six commands.

If Git gives trouble with long paths, run this once:

```powershell
git config --global core.longpaths true
```

Optional but helpful for predictable line endings in this repo:

```powershell
git config --global core.autocrlf false
```

## 5. Optional SSH check for GitHub

If your friend will clone over SSH, confirm GitHub SSH access first:

```powershell
ssh -T git@github.com
```

If SSH is not configured yet, they can still clone over HTTPS and come back to SSH later.

## 6. Clone the repository

Choose one of the following.

SSH:

```powershell
git clone git@github.com:rajatyadav2505/LegalOS.git
cd LegalOS
```

HTTPS:

```powershell
git clone https://github.com/rajatyadav2505/LegalOS.git
cd LegalOS
```

At this point, confirm you are at the repo root:

```powershell
git status
```

You should see output similar to `On branch main`.

## 7. Create the environment file

Copy the sample environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` in VS Code, Notepad, or another editor and confirm these local-development values:

```text
APP_ENV=development
APP_URL=http://localhost:3000
API_URL=http://localhost:8000
DATABASE_URL=postgresql+asyncpg://legalos:legalos@localhost:5432/legalos
VALKEY_URL=redis://localhost:6379/0
AUTO_CREATE_DB=false
AUTO_SEED_DEMO=false
```

Change `JWT_SECRET` to any non-default local secret before starting:

```text
JWT_SECRET=legalos-local-dev-secret-change-this
```

You do not need to change the other defaults for a normal first run.

## 8. Create the Python virtual environment

From the repo root, run:

```powershell
py -3.12 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, run this in the current terminal and then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

After activation, your shell prompt usually shows `(.venv)`.

## 9. Install the Python dependencies

With the virtual environment active, run:

```powershell
python -m pip install --upgrade pip
python -m pip install -e "apps/api[dev]"
```

What this does:

- upgrades `pip`
- installs the FastAPI application in editable mode
- installs dev tools such as `pytest`, `ruff`, and `mypy`

Quick check:

```powershell
python -m pip list | Select-String "fastapi|alembic|pytest|ruff|mypy"
```

## 10. Install the Node.js workspace dependencies

From the repo root, run:

```powershell
corepack enable
corepack pnpm install
```

This installs the pnpm workspace for:

- `apps/web`
- `packages/contracts`
- `packages/ui`

If `corepack enable` succeeds but `corepack pnpm install` still fails, try:

```powershell
corepack prepare pnpm@9.15.0 --activate
corepack pnpm install
```

## 11. Start Docker Desktop and the local infrastructure

Make sure Docker Desktop is open and healthy before continuing.

Then start the local services from the repo root:

```powershell
docker compose -f .\infra\compose\docker-compose.yml up -d
```

These services should start:

- `postgres`
- `valkey`
- `minio`
- `tika`

Check container status:

```powershell
docker compose -f .\infra\compose\docker-compose.yml ps
```

Expected default ports:

- PostgreSQL: `5432`
- Valkey: `6379`
- MinIO API: `9000`
- MinIO Console: `9001`
- Tika: `9998`

If Docker needs a minute to settle, wait until `postgres` and `valkey` are healthy before continuing.

## 12. Apply database migrations

From the repo root, run:

```powershell
cd .\apps\api
..\..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..\..
```

This creates the LegalOS schema in Postgres using Alembic.

If the migration fails because Postgres is not ready yet, wait 15 to 30 seconds and run the command again.

## 13. Seed the demo data

From the repo root, run:

```powershell
cd .\apps\api
..\..\.venv\Scripts\python.exe -m app.db.seed
cd ..\..
```

This seeds:

- the demo organization
- the demo user
- a sample matter
- sample authorities
- sample workflow data

## 14. Start the backend API

Open a new PowerShell window.

Move to the repo root, activate the virtual environment, then start the API:

```powershell
cd C:\path\to\LegalOS
.\.venv\Scripts\Activate.ps1
cd .\apps\api
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Leave this terminal open.

When it starts correctly, test the health endpoint from another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Expected response:

```text
message
-------
ok
```

API docs will be available at:

```text
http://127.0.0.1:8000/api/docs
```

## 15. Start the frontend web app

Open a second PowerShell window.

Move to the repo root and start the Next.js app:

```powershell
cd C:\path\to\LegalOS
corepack pnpm --filter @legalos/web dev
```

When the dev server is ready, open:

- `http://127.0.0.1:3000/login`
- `http://127.0.0.1:8000/api/docs`

## 16. Log in and do a first-run smoke test

Use the seeded credentials:

- Email: `demo@legalos.local`
- Password: `DemoPass123!`

Then verify the main product flow:

1. Open `http://127.0.0.1:3000/login` and sign in.
2. Open the matter list and enter the seeded matter.
3. Go to the Upload workspace and upload a sample document.
4. Open the Bundle Map and confirm chronology, contradiction, cluster, and ingest information appear.
5. Open Research and search the seeded legal corpus.
6. Save at least one authority.
7. Export the research memo.
8. Open Draft Studio and generate a petition or reply.
9. Open Strategy Engine and verify best, fallback, and risk lines render.
10. Open Institutional Mode and confirm the dashboard loads.
11. Open Court Intelligence and confirm that workspace loads too.

If those steps work, the local Windows setup is functionally healthy.

## 17. Optional worker recovery commands

These are only needed when queued work gets stuck after a restart.

Drain queued document-ingest jobs from the repo root:

```powershell
$env:PYTHONPATH = "apps/api"
.\.venv\Scripts\python.exe .\apps\worker-ingest\src\worker_ingest.py --drain-queued --limit 25
```

Drain bounded intelligence jobs from the repo root:

```powershell
$env:PYTHONPATH = "apps/api"
.\.venv\Scripts\python.exe .\apps\worker-ai\src\worker_ai.py --drain --limit 25
```

## 18. Verification commands

Once everything is installed, these are the main validation commands to run from the repo root.

Backend tests:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests\bootstrap .\tests\integration -q
```

Backend lint:

```powershell
.\.venv\Scripts\python.exe -m ruff check .\apps\api .\apps\worker-ingest .\apps\worker-ai .\tests\bootstrap .\tests\integration
```

Backend typing:

```powershell
.\.venv\Scripts\python.exe -m mypy .\apps\api\app
```

Frontend typecheck:

```powershell
corepack pnpm --filter @legalos/web typecheck
```

Frontend production build:

```powershell
corepack pnpm --filter @legalos/web build
```

## 19. Common Windows issues and fixes

### PowerShell blocks `.ps1` activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the virtual environment again.

### `py -3.12` does not work

Check installed Python versions:

```powershell
py -0p
```

If Python 3.12 is missing, install Python 3.12 and retry.

### `corepack` is not recognized

Reinstall Node.js 20+ and reopen PowerShell. Then run:

```powershell
corepack enable
corepack prepare pnpm@9.15.0 --activate
```

### Docker containers fail to start

Check:

- Docker Desktop is actually running
- WSL2 backend is enabled
- virtualization is enabled in BIOS if Docker complains
- ports `5432`, `6379`, `9000`, `9001`, and `9998` are free

You can inspect logs with:

```powershell
docker compose -f .\infra\compose\docker-compose.yml logs postgres
docker compose -f .\infra\compose\docker-compose.yml logs valkey
```

### The API cannot connect to Postgres

Confirm:

- `docker compose -f .\infra\compose\docker-compose.yml ps` shows `postgres` running
- `.env` still points to `localhost:5432`
- migrations were actually applied

Then rerun:

```powershell
cd .\apps\api
..\..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..\..
```

### Port `3000` or `8000` is already in use

Use different ports.

Example changes in `.env`:

```text
APP_URL=http://localhost:3001
API_URL=http://localhost:8001
CORS_ORIGINS=http://localhost:3001
```

Then start the API on `8001` and the web app on `3001`.

### OCR is weak or not available

Tesseract is optional but helpful for OCR-heavy workflows outside containerized extraction.

Typical install path:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

If needed, add that folder to the Windows `PATH`, restart PowerShell, and retry.

### `pnpm install` or `next build` fails because of permissions or antivirus

Common fixes:

- move the repo out of OneDrive
- exclude the repo folder from aggressive antivirus scanning if policy allows
- delete `node_modules` and rerun `corepack pnpm install`

## 20. How to stop everything cleanly

Stop the frontend and backend servers with `Ctrl+C` in their open terminals.

From the repo root, stop the infrastructure stack:

```powershell
docker compose -f .\infra\compose\docker-compose.yml down
```

If you want to also remove the local Docker volumes and start fresh later:

```powershell
docker compose -f .\infra\compose\docker-compose.yml down -v
```

## 21. How to start it again later

For future runs, the short version is:

1. Open Docker Desktop.
2. From the repo root, run `docker compose -f .\infra\compose\docker-compose.yml up -d`.
3. Start the API terminal again.
4. Start the web terminal again.

You do not need to recreate the virtual environment or reinstall dependencies every time unless something changed.

## 22. What this guide does not require

This baseline does not require:

- WSL2 shell usage for daily startup
- paid cloud services
- managed Postgres
- managed Redis or Valkey
- S3

The intended local baseline is self-hostable and development-friendly.
