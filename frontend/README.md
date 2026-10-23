# FitZone frontend

Premium gym website built with React and Vite. The Flask API is maintained in
the sibling [`backend/`](../backend/) directory.

## Run locally

Configure and start the backend independently by following
[backend/README.md](../backend/README.md). For a PowerShell setup from the
project root:

```powershell
Set-Location .\backend
.\.venv\Scripts\Activate.ps1
python app.py
```

In a second PowerShell terminal, start the frontend:

```powershell
Set-Location .\frontend
npm install
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm run dev
```

If `frontend/.env` already exists, keep it and verify that `VITE_API_URL` is
set to `http://127.0.0.1:5000/api` (or the URL where the backend is served).
Restart Vite after changing `.env`. Open the URL printed by Vite, normally
`http://localhost:5173`.

## Configuration

- `frontend/.env` sets the public Vite variable `VITE_API_URL`.
- `backend/.env` holds the Flask database credentials, secret keys, and
  `CORS_ORIGINS`; see the backend README. Do not commit either `.env` file.
- The backend's default CORS origins allow both `localhost:5173` and
  `127.0.0.1:5173`.

For an existing Phase 1 database, apply migrations `001` through `005` once as
documented in [backend/README.md](../backend/README.md). `db.create_all()` does
not upgrade existing placeholder tables. Create an administrator separately
with `flask --app app create-admin` from `backend/`.

## Connected account areas

- `/login` and `/register` connect to the Flask authentication routes.
- `/dashboard`, `/profile`, `/attendance`, and `/workouts` require a member
  account.
- `/admin`, `/admin/members`, `/admin/membership`, `/admin/attendance`, and
  `/admin/announcements` require an administrator account.
- Membership plan names, durations, and prices come from the public backend
  plan endpoint. The backend does not currently provide member self-service
  membership assignment or payment checkout; members must contact the gym.
- The backend issues short-lived access JWTs but does not implement refresh
  tokens or server-side logout. The frontend keeps a JWT in memory rather than
  browser storage, so reloading the page signs the user out.
- Member announcements are displayed from the member dashboard response; no
  separate public announcements endpoint currently exists.

## Validation

```powershell
Set-Location .\frontend
npm run lint
npm run build
```

Backend tests run from `backend/` with:

```powershell
python -m unittest discover -s tests
```
