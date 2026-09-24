# MissionLens analyst workspace

React and TypeScript interface for the existing FastAPI reports and cases endpoints.
This is a local portfolio demonstration using only synthetic data.

## Run locally

1. From the repository root, start PostgreSQL and apply migrations:

   ```powershell
   docker compose --env-file .env -f infrastructure\compose.yaml up -d postgres
   python -m alembic upgrade head
   ```

2. In one VS Code terminal, run the API:

   ```powershell
   python -m uvicorn backend.app.main:app --reload
   ```

3. In a second VS Code terminal, start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

4. Open `http://127.0.0.1:5173`. The Vite development server proxies `/api`
   requests to FastAPI at `http://127.0.0.1:8000`.

Use **Load synthetic demo data** to add five fictional reports. The action is
repeatable: reports with the same external IDs are skipped. Select reports as
evidence, enter a title and summary, and create a case. Cases are stored in
PostgreSQL by the backend.

## Current boundaries

- Keyword search is local to the loaded reports; the backend currently supports
  language, source type, and bounding-box filters.
- The SVG view places reports using real latitude/longitude coordinates on a
  schematic grid. It has no geographic basemap or MapLibre integration yet.
- There is no login, authorization, approval workflow, or audit history yet.
  Run it locally with synthetic data only.
- Redis and MinIO are not used by this frontend slice.
