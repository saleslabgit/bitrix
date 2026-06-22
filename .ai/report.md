# Отчет: TASK-2026-06-22-30

Статус: done

## Кратко

Добавил простой single-user login gate для backend API и frontend workspace.
Auth выключена по умолчанию для локальной разработки. При включении через env
backend требует username, password и session secret, выдает подписанную
HttpOnly SameSite=Lax cookie-сессию и защищает все `/api/*` маршруты кроме
`/api/auth/*`. Frontend показывает форму входа, не хранит пароль или token в
browser storage, возвращается к login при `401` и сохраняет report filters.

## Измененные файлы

- `.env.example`
- `backend/README.md`
- `backend/app/api/models.py`
- `backend/app/core/auth.py`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/tests/test_auth.py`
- `docs/development.md`
- `docs/project-status.md`
- `frontend/README.md`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/styles.css`
- `.ai/report.md`

## Backend

- Добавлены env settings:
  `APP_AUTH_ENABLED`, `APP_AUTH_USERNAME`, `APP_AUTH_PASSWORD`,
  `APP_AUTH_SESSION_SECRET`, `APP_AUTH_SESSION_TTL_SECONDS`,
  `APP_AUTH_COOKIE_SECURE`.
- Если `APP_AUTH_ENABLED=true`, но username/password/session secret пустые,
  settings validation падает с safe explicit error.
- Добавлен `backend/app/core/auth.py`:
  - constant-time credential comparison;
  - HMAC SHA-256 signed cookie token;
  - expiry validation;
  - invalid/expired cookie rejection;
  - safe auth status response without password, secret, or raw token.
- Добавлены endpoints:
  - `GET /api/auth/session`;
  - `POST /api/auth/login`;
  - `POST /api/auth/logout`.
- Logout clears the session cookie.
- Central ASGI middleware protects all non-auth `/api/*` routes when auth is
  enabled. `/health` remains public.
- No DuckDB session storage was added.
- No Bitrix calls were added by auth checks.

## Frontend

- API client now sends cookies with requests and exposes `401` as auth state.
- App startup checks `/api/auth/session`.
- If auth is disabled, existing report workspace opens normally.
- If auth is enabled and unauthenticated, a compact login form is shown.
- Valid login refetches session/status/filter data.
- Logout clears backend cookie and returns to login.
- Existing report filter localStorage keys are preserved and are not cleared on
  login/logout/session expiry.

## Documentation

- Documented auth env values in `.env.example`, `docs/development.md`,
  `backend/README.md`, and `frontend/README.md`.
- Updated `docs/project-status.md` to move authentication out of not-done state.
- Documentation uses placeholders only and says not to commit real credentials
  or reusable secrets.

## Запущенные проверки

- `npm run build` from `frontend/` — passed. Vite reported the existing
  Recharts-related bundle-size warning; build succeeded.
- `/tmp/bitrix-backend-venv/bin/pytest backend/tests/test_auth.py` — passed,
  9 tests.
- `/tmp/bitrix-backend-venv/bin/pytest backend/tests` — passed, 124 tests.
- `docker compose config` — passed.
- `docker compose up --build -d` — passed.
- `curl -f http://127.0.0.1:8000/health` — passed when run with unsandboxed
  localhost access.
- `curl -f http://127.0.0.1:5173/` — passed when run with unsandboxed
  localhost access.
- `docker compose down -v` — passed.
- `rg "crm\\.[A-Za-z0-9_.]*(add|update|delete|set)" backend/app backend/tests frontend/src`
  — found only the existing negative test `crm.deal.update`; no Bitrix write
  method was added.

## Факты

- Docker Compose still starts services only and does not refresh Bitrix data.
- Current local `.env` keeps auth disabled, so local report workspace remains
  open by default.
- Auth-enabled behavior is covered by backend HTTP-level tests over ASGI
  transport.
- The project test venv has a broken/deprecated `fastapi.testclient.TestClient`
  path for sync FastAPI endpoints; auth tests use `httpx.ASGITransport`
  instead. Existing direct-call endpoint tests remain unchanged.
- Compose config loaded local `.env`; real values were not copied into docs or
  committed files.

## Предположения

- A stateless signed cookie is sufficient for this single-user internal gate
  until deployment planning decides whether a reverse proxy or stronger auth
  boundary is needed.
- `SameSite=Lax` plus optional `APP_AUTH_COOKIE_SECURE=true` is the intended
  deployment baseline for HTTPS.

## Неизвестное

- Final deployment host, HTTPS/proxy behavior, and production secret management
  are still unknown.
- Browser visual verification with Playwright was not run for the login screen;
  build and HTTP/operator checks passed.

## Риски или следующий шаг

- Before deployment, set `APP_AUTH_ENABLED=true`, strong non-reused
  `APP_AUTH_SESSION_SECRET`, real username/password, and
  `APP_AUTH_COOKIE_SECURE=true` behind HTTPS.
