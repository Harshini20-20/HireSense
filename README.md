# HireSense

HireSense is a React + Vite frontend and FastAPI backend with a SQLite database and local resume storage.

## Run with Docker Compose

Docker Desktop with Docker Compose is required. From the project root in PowerShell, create a local environment file:

```powershell
Copy-Item .env.example .env
```

The defaults use the existing `backend/hiresense.db` and `backend/storage/resumes` paths. Confirm both are present before starting. The Compose bind mounts deliberately fail if either host path is missing, instead of silently creating a new database path. Adjust the paths in `.env` only when pointing at an existing data location. `.env` is ignored by Git.

Build the images and start the application:

```powershell
docker compose build
docker compose up -d
docker compose ps
```

Open [http://localhost:8080](http://localhost:8080). Change `FRONTEND_PORT` in `.env` if port 8080 is already in use.

The frontend is a Vite production build served by Nginx. Nginx serves the React single-page application and proxies `/api` requests to the backend over the private Compose network. The backend port is not published to the host. Set `VITE_API_BASE_URL` in `.env` before building to change the frontend API base URL.

### Persistent data

- `HIRESENSE_DB_FILE` bind-mounts the existing SQLite file to `/app/backend/hiresense.db`.
- `HIRESENSE_RESUME_DIR` bind-mounts the existing resume directory to `/app/backend/storage/resumes`.
- A named `model_cache` volume stores downloaded sentence-transformer model files.

Containers do not initialize the database or run migrations on startup. Do not remove or relocate the host database or resume directory while the application is running.

### Database configuration

The backend reads `DATABASE_URL` from the process environment. In Docker Compose, Compose passes the value from the project `.env` file or deployment environment. Leave it blank or unset to use the existing SQLite file at `backend/hiresense.db`. The SQLite bind mount remains in place for local Docker use.

For PostgreSQL, set `DATABASE_URL` to the connection URL supplied by your hosting provider in an untracked `.env` file or deployment secret. PostgreSQL URLs are routed through psycopg 3; `sslmode=require` is added when the URL does not specify an `sslmode`. An explicit `sslmode` and other driver query options are preserved. Never put credentials in frontend build variables or source control.

FastAPI startup does not create or migrate tables. This repository has explicit `create_all`/additive migration utilities, but no versioned Alembic migration history. A PostgreSQL deployment must have its schema reviewed and provisioned before application use. Existing SQLite data is not copied to PostgreSQL by this configuration.

To initialize a **fresh** PostgreSQL database, first put its connection URL in the ignored project `.env` file as `DATABASE_URL`. Then build the backend image and run the explicit, PostgreSQL-only initializer from the project root:

```powershell
docker compose build backend
docker compose run --rm backend python -m backend.app.database.initialize_postgres
```

The command refuses to run when `DATABASE_URL` is missing or uses a non-PostgreSQL dialect. It creates missing tables from the registered SQLAlchemy models, inserts no records, and is safe to repeat. It does not alter existing tables or migrate SQLite data. The application does not invoke this command during startup.

The current metadata defines eight tables: `jobs`, `job_requirements`, `candidates`, `candidate_skills`, `resumes`, `analyses`, `analysis_details`, and `job_candidates`. Primary keys are integer IDs. `analysis_details` uses SQLAlchemy `JSON` columns (PostgreSQL `JSON`, not `JSONB`); other columns use portable `String`, `Text`, `DateTime`, `Float`, and integer types. Explicit unique constraints cover `(candidate_id, normalized_skill)`, `(job_id, candidate_id)` in analyses, `analysis_id`, and `(job_id, candidate_id)` in job associations. `job_candidates.job_id` and `candidate_id` have explicit indexes. Foreign keys connect requirements to jobs; skills and resumes to candidates; analyses to jobs, candidates, and resumes; analysis details to analyses; and job associations to jobs and candidates. Cascade actions are declared on requirements, skills, resumes, analysis details, and job associations. Timestamp columns use `now()` server defaults. `importance`, association `source`/`status`, and analysis-detail JSON defaults are SQLAlchemy client-side defaults.

### Resume storage configuration

`RESUME_STORAGE_BACKEND` defaults to `local`, preserving the existing `HIRESENSE_RESUME_STORAGE` path and Docker bind mount. Set it to `supabase` for a private Supabase Storage bucket, then provide `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, and optionally `SUPABASE_STORAGE_BUCKET` (defaults to `hiresense-resumes`) through the backend environment. Keep the secret key in the untracked `.env` or deployment secret store, and never use a `VITE_` variable for it. Docker Compose passes these values only to the backend; the bucket remains private.

New resume rows store a stable backend-prefixed object key in the existing `resumes.file_path` column, so no schema change or migration is needed. Existing absolute local paths remain supported. Selecting Supabase does not copy existing local resume files to the bucket; keep the local storage mount available for records that still point to local files, or plan a separate controlled migration before removing it. Uploads remain limited to PDF/DOCX and 10 MB. PDFs are served inline through the existing API route, and DOCX files are returned as downloads.

### Stop, restart, and logs

Stop the containers without removing data:

```powershell
docker compose stop
```

Start the stopped containers again:

```powershell
docker compose start
```

Restart services:

```powershell
docker compose restart
```

View logs, or follow them live:

```powershell
docker compose logs
docker compose logs -f backend frontend
```

After changing application or Docker configuration, rebuild and recreate the services while keeping their mounts and volumes:

```powershell
docker compose up -d --build
```

Avoid commands that remove Compose volumes when preserving the model cache matters. The SQLite database and resumes are host bind mounts and remain in their configured host locations.

## Local development

The existing non-container workflow remains available. From the project root, activate your Python environment and run:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8001
```

In another terminal:

```powershell
Set-Location .\frontend
npm run dev
```

Vite continues to proxy `/api` requests to `http://127.0.0.1:8001` during local development.
