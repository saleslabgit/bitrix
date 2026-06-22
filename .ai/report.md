# Отчет: TASK-2026-06-22-04

Статус: done

## Кратко

Реализован первый frontend milestone: `frontend/` теперь содержит React/TypeScript/Vite приложение с одним экраном `Contacts`.

Экран работает с существующим локальным backend API и поддерживает:

- таблицу контактов;
- поиск по названию контакта;
- фильтры по нормализованному типу, региону и статусу сделки;
- пагинацию через `limit`/`offset`;
- loading, error и empty states;
- компактный индикатор статуса активного dataset.

Backend не менялся.

## Измененные файлы

- `frontend/package.json` — npm scripts, React/Vite/TypeScript/TanStack Query/Lucide dependencies.
- `frontend/package-lock.json` — lockfile после `npm install`.
- `frontend/index.html` — Vite HTML entry.
- `frontend/tsconfig.json` — strict TypeScript config.
- `frontend/vite.config.ts` — React plugin and dev proxy `/api`/`/health` to local backend.
- `frontend/src/main.tsx` — React entry and `QueryClientProvider`.
- `frontend/src/api.ts` — typed client for existing backend endpoints.
- `frontend/src/App.tsx` — Contacts screen, filters, table, pagination, states, dataset badge.
- `frontend/src/styles.css` — app styles based on `ui-kits` tokens.
- `frontend/src/vite-env.d.ts` — Vite env typing.
- `frontend/README.md` — frontend commands, backend URL, design-system note.
- `.gitignore` — ignores TypeScript build info cache (`*.tsbuildinfo`).
- `docs/development.md` — frontend install/run/build and API config.
- `docs/project-status.md` — current frontend milestone status.
- `.ai/report.md` — this report.

`.ai/task.md` remains a pre-existing unstaged planner change and was not modified by Codex. `ui-kits/`, generated data, DuckDB files, Parquet snapshots, CSV exports, `.env`, logs, caches, and `node_modules` were not staged.

## Endpoints Used

```text
GET /api/reports/contacts
GET /api/meta/filters
GET /api/datasets/status
```

No new backend report endpoint was created.

## Response Shape Notes

The Contacts table follows the actual `ContactSummaryResponse` shape from `backend/app/api/models.py`.

Displayed fields:

- `contact_name`;
- `contact_id`;
- `contact_type_raw`;
- `contact_type_normalized`;
- `region_normalized`;
- `total_deals_count`;
- `won_deals_count`;
- `open_deals_count`;
- `lost_deals_count`;
- `total_amount_original`.

No forbidden personal fields are displayed. The endpoint response does not include phone, email, address, messenger, comments, files, requisites, or arbitrary non-allowlisted Bitrix fields.

## Design System Files Inspected

Inspected and used:

- `ui-kits/readme.md` — product direction, Manrope typography, SaaS web-app layout, color/radius/spacing rules, icon guidance.
- `ui-kits/SKILL.md` — instruction to use README and available files for production code.
- `ui-kits/styles.css` — global import entry.
- `ui-kits/tokens/colors.css` — primary blue, neutral palette, semantic surface/text/border aliases.
- `ui-kits/tokens/typography.css` — Manrope and type tokens.
- `ui-kits/tokens/spacing.css` — 2px/8px spacing scale and desktop max-width.
- `ui-kits/tokens/effects.css` — 8px/12px radii, shadows, focus rings, transitions.
- `ui-kits/components/core/Button.jsx` — button sizes, variants, hover/active behavior.
- `ui-kits/components/core/Input.jsx` — label-above-input pattern and focus ring behavior.
- `ui-kits/components/core/Badge.jsx` — badge variants and compact sizing.
- `ui-kits/components/core/Card.jsx` — surface, border, radius, shadow pattern.
- `ui-kits/components/feedback/Alert.jsx` — alert styling and semantic colors.
- `ui-kits/components/navigation/Sidebar.jsx` — left navigation shell and active item styling.
- `ui-kits/ui_kits/webapp/README.md` — web-app prototype composition.
- `ui-kits/ui_kits/webapp/index.html` — dashboard shell reference.

Applied design-system direction:

- imported `../../ui-kits/styles.css` from the frontend CSS;
- used Manrope, primary blue `#3040CC`, blue-grey neutrals, white cards, subtle borders, `8px` controls, `12px` cards, and compact data-table density;
- used Lucide icons as the documented substitute for Untitled UI icons.

`ui-kits/` files were not modified.

## Architecture Notes

- TanStack Query is used for server state because the screen has three independent backend reads, cacheable filters/status data, and explicit loading/error refetch states.
- The table is plain React for this milestone. TanStack Table was not added because the required table behavior is limited to rendering, filtering via backend query parameters, and simple pagination.
- Backend CORS was not changed. Vite dev proxy handles local frontend-to-backend calls during development.
- `VITE_BACKEND_URL` controls the dev proxy target. `VITE_API_BASE_URL` can be used for built/static deployments when the API is not same-origin.

## Bitrix Calls

Bitrix methods called in this task:

```text
none
```

No Bitrix sync was run. No Bitrix row-listing methods were called. No Bitrix write methods were called.

## Запущенные проверки

Before implementation:

- `git log --oneline -5` — passed. Latest relevant commit was `17035a9 planner: TASK-2026-06-22-04 Build contacts frontend`.
- `git status --short` — passed. Showed only pre-existing modified `.ai/task.md`.

Documentation/library checks:

- Context7 docs queried for Vite, React, and TanStack Query.

Frontend checks from `frontend/`:

- `npm install` — passed. Created `package-lock.json`. npm reported 1 low severity vulnerability.
- `npm run build` — initially failed because `vite.config.ts` needed Node typings.
- `npm install --save-dev @types/node` — passed.
- `npm run build` — passed:
  - `tsc -b`;
  - `vite build`;
  - output under ignored `frontend/dist/`.

Repository/root checks:

- `docker compose config` — not run successfully: Docker CLI is not available in this WSL distro (`The command 'docker' could not be found in this WSL 2 distro.`).

Pre-staging checks:

- `git status --short --branch` — passed. Showed TASK-2026-06-22-04 files plus pre-existing unstaged `.ai/task.md`.
- `git diff --stat HEAD` — passed. Included tracked task docs/report changes plus pre-existing `.ai/task.md`; untracked frontend files are not included by this command before staging.
- `git diff --name-only --cached` — passed with no output.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.
- `git status --short --ignored frontend backend/data data ui-kits` — passed. Showed ignored `frontend/node_modules/`, `frontend/dist/`, `frontend/tsconfig.tsbuildinfo`, and `backend/data/`.

Final staged checks:

- `git status --short --branch` — passed. `.ai/task.md` remained unstaged.
- `git diff --stat HEAD` — passed. Included staged TASK-2026-06-22-04 files plus pre-existing unstaged `.ai/task.md`.
- `git diff --name-only --cached` — passed. Listed only `.ai/report.md`, `.gitignore`, docs, and `frontend/` task files.
- `git diff --check -- ':!AGENTS.md' ':!.ai/task.md'` — passed with no output.
- `git status --short --ignored frontend backend/data data ui-kits` — passed. `ui-kits/`, generated data, `node_modules`, `dist`, and `tsbuildinfo` were not staged.
- `git log --oneline -1` — passed. Latest relevant commit remained `17035a9 planner: TASK-2026-06-22-04 Build contacts frontend`.

## Known Limitations

- Only the Contacts screen is implemented.
- No dashboard, ABC, RFM, stale deals, concentration, type/region analytics, authentication, production deployment, or CI was added.
- The frontend assumes the backend is running separately at `http://localhost:8000` for local development unless `VITE_BACKEND_URL` is set.
- `npm install` reported 1 low severity vulnerability; no automatic `npm audit fix` was run to avoid unplanned dependency changes.
