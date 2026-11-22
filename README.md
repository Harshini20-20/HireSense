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
