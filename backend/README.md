# FitZone backend

Flask REST API using SQLAlchemy and MySQL. Authentication uses short-lived JWT
access tokens. Public registration creates member accounts only.

## Local setup

From the repository root in PowerShell:

```powershell
Set-Location .\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local MySQL database and account with permission to use it:

```sql
CREATE DATABASE fitzone_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

Set `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and `SECRET_KEY`
in `backend/.env`. `JWT_SECRET_KEY` can be set separately; when omitted, the
application uses `SECRET_KEY` for signing. Generate a strong key with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set `CORS_ORIGINS` to the comma-separated frontend origins. The defaults only
allow the local Vite origins. Do not set `*` when `APP_ENV=production`.

On an existing Phase 1 database, apply
[`migrations/001_add_user_profile_fields.sql`](./migrations/001_add_user_profile_fields.sql)
once to add the nullable profile columns. For a new database, create tables
from the models:

```powershell
flask --app app shell
```

Then run:

```python
from extensions import db
db.create_all()
```

If the Phase 1 `memberships` placeholder table was created, apply
[`migrations/002_create_memberships.sql`](./migrations/002_create_memberships.sql)
once to add its columns, constraints, indexes, and user foreign key. Existing
placeholder rows have no member or plan data; back them up or remove them
before migrating if any were inserted.

After migrations `001` through `004`, apply
[`migrations/005_admin_dashboard.sql`](./migrations/005_admin_dashboard.sql)
once to add member activation, configurable membership plans, payment reporting
fields, and announcements. The migration seeds the BASIC, PRO, and ELITE
plans. It assumes the Phase 1 `payments` and `notifications` placeholder tables
exist with only an `id` column. If either table contains placeholder rows,
backfill valid member ownership/payment values or announcement title/body
before applying the `NOT NULL` columns in this migration.

Apply [`migrations/003_create_attendance.sql`](./migrations/003_create_attendance.sql)
once to create the attendance table on an existing database. For a new
database, `db.create_all()` creates it from the model.

Create an admin separately using an interactive prompt (it never accepts a
password as a command-line argument):

```powershell
flask --app app create-admin
```

Start the API with either:

```powershell
python app.py
```

or:

```powershell
flask --app app run
```

The development server listens on port `5000` by default. Set `PORT` to
override the `python app.py` port. Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

## Authentication API

All request and response bodies are JSON.

### `POST /api/auth/register`

Required fields: `name`, `email`, `phone`, and `password`. Passwords must be
8–128 characters. Email is trimmed and normalized to lowercase. The server
hashes passwords with Werkzeug and always assigns the `member` role.

### `POST /api/auth/login`

Accepts `email` and `password`. A successful response includes a 15-minute
JWT access token and a public user profile. Invalid credentials return HTTP
401 without distinguishing an unknown email from a wrong password.

### `GET /api/auth/me`

Returns the current account. Send the token in this header:

```text
Authorization: Bearer <access-token>
```

### `PUT /api/auth/profile`

Requires a bearer token. Accepts any non-empty subset of `name`, `phone`,
`fitness_goal`, `date_of_birth` (`YYYY-MM-DD`), `gender`, and `profile_photo`
(absolute HTTP/HTTPS URL). `null` clears optional fields. Role, email, and
password cannot be changed through this endpoint.

## Membership API

The initial membership plan fallback is configured in `membership_plans.py`.
After migration `005`, plan prices and supported durations are managed in the
database; the initial BASIC, PRO, and ELITE plan records are seeded there.

### `GET /api/membership/plans`

Public endpoint returning the available plans, monthly prices, supported
durations, and total price for each duration.

### `GET /api/membership/current`

Requires a member JWT. Returns `membership: null` when no membership is active.
Otherwise includes start/end dates, status, price, and `remaining_days`
calculated from the end date. A membership ending today remains active for
that date; expired active records are marked expired when membership data is
read.

### `GET /api/membership/history`

Requires a member JWT. Returns that account's membership records newest first.

### Admin endpoints

All admin membership endpoints require a JWT whose account currently has the
`admin` role:

- `GET /api/admin/memberships` lists membership records.
- `POST /api/admin/memberships` assigns a plan; JSON requires `user_id`,
  `plan_type`, and `duration_months`.
- `PUT /api/admin/memberships/<id>` updates `plan_type` and/or
  `duration_months`.
- `POST /api/admin/memberships/<id>/renew` renews a membership; duration
  defaults to one month and can optionally specify another plan type.
- `DELETE /api/admin/memberships/<id>` cancels the record (soft cancellation).

The server determines price from the configured plan data; clients cannot
submit arbitrary prices. Assignments reject overlapping active periods. An
active membership renewal extends that record and adds the configured renewal
price; expired memberships restart from today.

## Gym admin API

Every `/api/admin/*` endpoint requires a valid JWT for an active account with
the `admin` role. A member receives HTTP 403. Admin-created members are always
created with the member role and passwords are hashed. Member deletion is a
soft deactivation; deactivated accounts cannot log in, and can be reactivated
with the member update endpoint.

- `GET /api/admin/members` supports `search`, `status=active|inactive`,
  `membership=active|expired|cancelled|none`, `page`, and `per_page`.
- `GET /api/admin/members/<id>` returns member profile, membership records,
  up to 100 attendance records, and up to 100 payment records. Payment output
  contains amount/status/date only; it excludes payment methods and transaction
  identifiers.
- `POST /api/admin/members` creates a member from `name`, `email`, `phone`,
  and `password`.
- `PUT /api/admin/members/<id>` updates permitted profile fields or
  `is_active`.
- `DELETE /api/admin/members/<id>` deactivates the member without deleting
  their history.
- `GET|POST /api/admin/membership-plans` lists or creates plans. Create JSON
  uses `plan_type`, `name`, `monthly_price`, and `durations_months`.
- `PUT /api/admin/membership-plans/<id>` updates a plan;
  `DELETE /api/admin/membership-plans/<id>` deactivates it. Deactivation
  preserves existing membership history and prevents new assignment.
- Membership assignment and renewal use the existing
  `POST /api/admin/memberships` and
  `POST /api/admin/memberships/<id>/renew` routes. Plan prices and allowed
  durations come from the active plan configuration.
- `GET /api/admin/attendance/today` lists today's visits.
  `GET /api/admin/attendance` lists visits and accepts `month` + `year` and/or
  `member_id`; `GET /api/admin/attendance/member/<id>` lists one member's
  history. Check-in and checkout timestamps are included.
- `GET /api/admin/dashboard` returns total/active/expired members, daily and
  monthly attendance, members expiring in the next seven days, all-time/current/
  previous-month completed-payment revenue, new members this month, and daily
  attendance/revenue trends for the last seven days. Supplying both
  `start_date` and `end_date` (`YYYY-MM-DD`) adds custom-period revenue.
- `POST|GET /api/admin/announcements` creates or lists announcements;
  `PUT|DELETE /api/admin/announcements/<id>` updates or deletes one.

Revenue totals include only payment rows with `status=completed`; pending,
failed, and refunded payments are excluded. Date-bounded revenue uses `paid_at`
to determine the reporting period. This phase adds the payment record schema
for reporting but does not add payment processing or payment creation
endpoints.

## Attendance API

Attendance uses the backend server's local date and time. A member must have an
active membership whose start and end dates include today. A unique database
constraint allows only one attendance row per member per date. Streaks are
derived from attendance dates: today or yesterday may anchor the current
streak, and it resets after both have been missed.

Member endpoints require a member JWT:

- `POST /api/attendance/check-in` records today's check-in and returns the
  current streak. An expired membership returns a renewal message.
- `POST /api/attendance/check-out` records checkout for today's attendance.
- `GET /api/attendance/history` returns records newest first. Optional `month`
  (1–12) and `year` (1–9999) query parameters filter the results.
- `GET /api/attendance/summary` returns total days, current-month attendance,
  current and longest streaks, and the last attendance date.

Admin endpoints require a JWT for an account with the current `admin` role:

- `GET /api/admin/attendance/today` lists today's attendance.
- `GET /api/admin/attendance/member/<user_id>` lists an individual member's
  attendance history.
- `GET /api/admin/attendance/statistics` returns overall, today's, and
  current-month counts and the longest member streak.

Apply [`migrations/004_create_workout_progress.sql`](./migrations/004_create_workout_progress.sql)
once to upgrade the Phase 1 workout/progress placeholder tables and create the
exercise table. On a new database, `db.create_all()` creates these tables from
the models. After `db.create_all()` on a new database, seed the initial plan
records with:

```powershell
flask --app app seed-membership-plans
```

The seed command is safe to rerun; it only inserts missing BASIC, PRO, and
ELITE plan records.

## Workouts, progress, and dashboard

Workout and progress endpoints require a member JWT and scope every record to
the authenticated account:

- `POST /api/workouts` creates a workout with `workout_type`, positive integer
  `duration` (minutes), optional `workout_date`, `notes`, and an optional
  `exercises` array. Each exercise requires `exercise_name`; `sets`, `reps`,
  and `weight` are optional.
- `GET /api/workouts` lists workouts newest first.
- `GET /api/workouts/<id>` retrieves one owned workout.
- `PUT /api/workouts/<id>` updates provided workout fields. Providing
  `exercises` replaces the workout's exercise list.
- `DELETE /api/workouts/<id>` removes the owned workout and its exercises.
- `POST /api/progress` stores a dated progress record; provide one or more of
  `weight`, `height`, `body_fat`, `chest`, `waist`, `arms`, or `notes`.
  Measurements may be omitted or set to `null`.
- `GET /api/progress` lists progress newest first.
- `GET /api/progress/latest` returns the latest record or `null`.
- `GET /api/dashboard` returns safe user details, current membership and
  remaining days, attendance streak/month totals, latest progress, five recent
  workouts, and up to five active gym announcements in `recent_notifications`.

For a React dashboard, call `/api/membership/current` and
`/api/membership/history` with the login JWT in the `Authorization: Bearer ...`
header. Request `/api/membership/plans` to populate plan selection and pricing.

API errors use `{ "success": false, "message": "..." }`. Success responses
include `success`, `message`, and where relevant `user` and `token`. The
`password_hash` is never included in API responses.

For a React client, keep the access token in application memory where practical
and send it as a Bearer token on protected requests. Do not store it in
`localStorage` unless the XSS risk is explicitly addressed. Tokens expire after
15 minutes; a refresh-token flow is not part of this phase.

## Tests

Tests use an in-memory SQLite database and do not require a running MySQL
server:

```powershell
python -m unittest discover -s tests -v
```
