# Task: TASK-2026-06-22-30

Status: planned
Created from: current `main` after accepted `TASK-2026-06-22-29`

## Title

Add single-user login

## Goal

Add a simple internal login gate before deployment preparation.

The app needs exactly one configured username and password, stored only in environment variables, with an authenticated browser session protecting local analytics API access.

## User Request

The user said:

```text
Следующим этапом нужно сделать простой логин, чисто под один логин и пароль. После этого будем готовить к деплою
```

## Facts

- Authentication is currently explicitly listed as not done in `docs/project-status.md`.
- Backend is FastAPI/Pydantic v2 under `backend/`.
- Frontend is React/Vite/TanStack Query under `frontend/`.
- Docker Compose loads `.env.example` and optional local `.env`.
- Real `.env` files are gitignored and must not be committed.
- Current frontend stores report filter state in localStorage, but no auth state exists.
- Current backend APIs expose local analytics data under `/api/*`.
- Bitrix remains a read-only source and report page loads must not call Bitrix directly.
- The app is not yet production deployed.

## Product Semantics

Implement a minimal internal auth model:

- one username;
- one password;
- no registration;
- no password reset;
- no roles;
- no user database;
- no audit UI;
- no multi-user permissions.

The login should protect the internal analytics UI and API from casual unauthenticated access before deployment.

## Security Semantics

Required:

- Username/password must come from environment variables only.
- Do not commit real credentials.
- Do not log the password.
- Do not return the password or auth secret in API responses.
- Do not store the password or session token in browser localStorage.
- Use an HttpOnly cookie for the browser session.
- Use constant-time comparison for credential checks.
- Session cookie must have `HttpOnly` and `SameSite=Lax` at minimum.
- Support a configurable session signing secret from env.
- Support a configurable session TTL.
- Logout must clear the cookie.

Recommended:

- Use only Python standard library for the simple signed session token if that fits current stack.
- Use HMAC signing with expiry timestamp for the cookie payload.
- Add `APP_AUTH_COOKIE_SECURE` or equivalent so deployment can enable secure cookies behind HTTPS.

## Auth Configuration

Add env-driven settings.

Recommended variables:

```text
APP_AUTH_ENABLED=false
APP_AUTH_USERNAME=
APP_AUTH_PASSWORD=
APP_AUTH_SESSION_SECRET=
APP_AUTH_SESSION_TTL_SECONDS=86400
APP_AUTH_COOKIE_SECURE=false
```

Behavior:

- If `APP_AUTH_ENABLED=false`, local development remains open and the frontend should not show a login screen.
- If `APP_AUTH_ENABLED=true`, backend must require all necessary auth settings.
- If auth is enabled but username/password/session secret are missing, fail closed with an explicit safe error. Do not silently run open.
- `.env.example` must contain only placeholder/empty values, not real credentials and not a reusable default password.

## Backend Scope

### 1. Settings

Update `backend/app/core/config.py`:

- add auth settings;
- validate required auth values when auth is enabled;
- keep existing Bitrix/data settings behavior unchanged.

### 2. Auth helpers

Add a small backend auth module consistent with current project structure.

Required helpers:

- validate login credentials with constant-time comparison;
- create signed session cookie value with expiry;
- validate signed session cookie;
- detect expired/invalid cookie safely;
- build safe auth status response.

Do not store sessions in DuckDB.

### 3. Auth endpoints

Add typed endpoints:

```text
GET  /api/auth/session
POST /api/auth/login
POST /api/auth/logout
```

Required behavior:

- `GET /api/auth/session` returns whether auth is enabled and whether the current request is authenticated.
- `POST /api/auth/login` accepts username/password JSON and sets the session cookie on success.
- Invalid login returns `401` with a generic message, not which field failed.
- `POST /api/auth/logout` clears the cookie.
- Do not expose password, secret, or raw cookie token.

Suggested response shape:

```json
{
  "auth_enabled": true,
  "authenticated": true,
  "username": "..."
}
```

When auth is disabled, `authenticated` can be `true` and `username` can be `null` or a safe local label.

### 4. Protect API routes

Protect backend routes when auth is enabled.

Required:

- `/health` remains public.
- `/api/auth/*` remains public enough to login/session/logout.
- All other `/api/*` routes require a valid session cookie when auth is enabled.
- Protected unauthenticated requests return `401` JSON.
- No Bitrix calls are added by auth checks.
- Manual refresh endpoint `/api/local/refresh-data` must be protected.
- Internal diagnostics/reconciliation endpoints must be protected.

Implementation may use FastAPI middleware or dependencies, but it must be centralized enough that new API routes are unlikely to be accidentally left open.

### 5. Backend tests

Add tests for:

- auth disabled: existing route functions/tests continue to work;
- auth enabled with missing config fails closed or returns safe explicit config error according to implementation;
- unauthenticated `/api/meta/filters` or another representative `/api/*` endpoint returns `401` through HTTP client;
- `GET /api/auth/session` works before login;
- invalid login returns `401` and does not set a valid session;
- valid login sets HttpOnly cookie;
- authenticated request to protected endpoint succeeds;
- logout clears session and protected endpoint returns `401` again;
- password/secret are not included in JSON responses.

Prefer HTTP-level tests with FastAPI `TestClient` for middleware behavior.

## Frontend Scope

### 1. API client

Update `frontend/src/api.ts`:

- add auth types and functions for session/login/logout;
- include cookies in requests, e.g. `credentials: "include"`;
- expose `401` in a way the app can route to login instead of showing a table error forever.

### 2. Login screen

Update `frontend/src/App.tsx` and styles:

- on app start, query `/api/auth/session`;
- if auth is disabled, render the existing app normally;
- if auth is enabled and unauthenticated, show a compact login screen;
- login form contains username, password, submit button;
- show loading and generic invalid-credentials error;
- do not store password or token in localStorage/sessionStorage;
- after successful login, refetch session and normal app data;
- add logout action in compact top area when authenticated and auth is enabled;
- logout should clear cookie and return to login screen.

UI requirements:

- Use existing design tokens/style direction.
- Keep it simple; no marketing page.
- Login screen should be usable on desktop and narrow screens.
- Do not expose auth settings or secrets.

### 3. Existing report behavior

Do not regress:

- Contacts, Deals, ABC report screens;
- right-side filter drawer;
- table width/height fix from `TASK-2026-06-22-29`;
- contact revenue chart modal;
- manual refresh UX;
- localStorage report filters.

When session expires or an API returns `401`, the frontend should move back to login or clearly require re-login, without clearing saved report filters.

## Documentation Scope

Update:

- `.env.example` with auth variables and safe comments/placeholders;
- `docs/development.md` with local auth configuration and operator flow;
- `docs/project-status.md` to move authentication out of not-done state;
- `frontend/README.md` with login behavior and verification steps;
- backend README if one exists and is relevant.

Document:

- auth disabled by default for local dev if that is the chosen implementation;
- how to enable auth in local `.env`;
- never commit real auth credentials or secrets;
- deployment must set auth env variables and use a strong session secret.

## Out Of Scope

- Multi-user accounts.
- Roles/permissions.
- Password reset.
- User management UI.
- Persistent session table in DuckDB.
- OAuth/SSO.
- Rate limiting/brute-force protection beyond generic error responses.
- Full deployment/Nginx/HTTPS setup.
- Changing Bitrix refresh behavior.
- Calling Bitrix from auth flow.

## Constraints

- Work only from current GitHub repository files.
- Keep Bitrix read-only.
- Do not add CRM write methods matching:

```text
crm.*.add
crm.*.update
crm.*.delete
crm.*.set
```

- Do not commit real `.env`, credentials, webhook URLs, auth passwords, session secrets, DuckDB files, Parquet, CSV, raw data, generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes.
- Do not store password/session token in browser localStorage.
- Do not use `git add .`.

## Acceptance Criteria

### Backend

- Auth can be enabled with one username/password/session secret from env.
- Auth disabled mode preserves current local dev flow.
- When auth is enabled, unauthenticated `/api/*` except `/api/auth/*` returns `401`.
- Login with valid credentials sets an HttpOnly session cookie.
- Login with invalid credentials returns generic `401`.
- Logout clears session cookie.
- Auth status endpoint returns safe auth status only.
- Missing auth config when enabled fails closed with a safe explicit error.
- No Bitrix calls are added.

### Frontend

- When auth is enabled and user is not logged in, login screen is shown instead of report data.
- Valid login opens the existing report workspace.
- Invalid login shows a generic error.
- Logout returns to login screen.
- Session expiry/`401` sends user back to login or shows re-login state.
- Existing report filters/table state are not wiped by login/logout.
- Existing Contacts/Deals/ABC UI still works after login.

### Safety and docs

- `.env.example` has safe auth placeholders only.
- Docs explain how to enable auth and that real credentials stay in local/deploy env.
- No secrets or forbidden artifacts are committed.
- No CRM write methods are added.
- `.ai/report.md` is updated.

## Checks

Required before implementation:

```bash
git log --oneline -5
git status --short
```

Backend checks:

```bash
cd backend && python -m pytest tests/test_api_local.py
```

If auth helpers/tests are placed in new test files, run them explicitly too.

If shared backend app/middleware behavior changes broadly, run full backend tests:

```bash
cd backend && python -m pytest
```

Frontend checks:

```bash
cd frontend && npm run build
```

Runtime/browser verification if practical:

```bash
docker compose up --build -d
curl -f http://localhost:8000/health
curl -i http://localhost:8000/api/auth/session
curl -i http://localhost:8000/api/meta/filters
curl -f http://localhost:5173/
```

If auth is enabled for runtime smoke, verify:

- unauthenticated report API returns `401`;
- login succeeds with configured test credentials;
- protected API works after login cookie;
- logout clears access;
- frontend login screen appears before login and report workspace appears after login.

Safety search:

```bash
rg "crm\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src
```

Secret/artifact check before commit:

```bash
git status --short
```

## Hard Workflow Gate

Before committing, verify:

- only task-related files are staged;
- no real credentials or secrets are staged;
- no `.env`, local DB, raw/generated data, logs, caches, `node_modules`, `frontend/dist`, or `ui-kits/` changes are staged;
- `.ai/report.md` is updated;
- backend tests are recorded;
- frontend build is recorded;
- auth runtime/browser verification is recorded or explicitly marked unavailable;
- no Bitrix write methods were added.

Commit message:

```text
codex: TASK-2026-06-22-30 Add single-user login
```