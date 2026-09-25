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

Use **Load synthetic demo data** to add five fictional reports. Three reports
in English, Turkish, and Spanish describe a possible terminal access delay;
two other reports are unrelated. **Draft example case** selects the three
related reports and fills the case form for review; it does not save a case.
The load action is repeatable: reports with the same external IDs are skipped.
Cases are stored in PostgreSQL by the backend once submitted.
An analyst can propose an action for a case, then switch to the Supervisor
demo actor to record a reasoned decision and see its audit events. The actor
switch is spoofable and exists solely for the local synthetic-data demo.

## Current boundaries

- Keyword and language searches run on the backend with paginated results;
  the backend also supports source-type and bounding-box filters. Keyword
  search is currently substring matching and needs indexing at larger scale.
- The SVG view places reports using real latitude/longitude coordinates on a
  schematic grid. It has no geographic basemap or MapLibre integration yet.
- There is no real authentication or trusted authorization. The approval and
  audit workflow records decisions only; it executes no operational actions.
  Run it locally with synthetic data only.
- Redis and MinIO are not used by this frontend slice.
