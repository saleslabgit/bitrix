# Frontend

React/TypeScript/Vite frontend for the Bitrix sales analytics MVP.

Implemented screen:

- `Contacts` report table with search, filters, pagination, loading, error, and empty states.
- The Contacts table uses `/api/reports/contacts/analytics` and displays sortable local analytics rows, exact contact ID filtering, Bitrix contact-card links, USD budget, USD estimated profit, latest won close date, and latest deal date. It does not use original-currency sums as the primary financial metric.

The app reads only the local backend API. It does not call Bitrix.

## Commands

Run the full stack from the repository root:

```bash
docker compose up --build
```

Open:

```text
http://localhost:5173
```

Compose only starts services. It does not automatically call Bitrix or refresh
local data. If an active `data/analytics.duckdb` dataset exists, the Contacts
table loads normally. If the screen says `Локальная база не подготовлена.`,
click `Обновить из Bitrix`; the backend runs the manual read-only refresh,
applies approved contact type rules, reruns local normalization, loads NBRB
rates, and then the screen reloads status, filters, and contacts. Local
databases and generated data are intentionally not committed.

The Compose frontend service proxies API calls to `http://backend:8000` inside
the Compose network and mounts the repository `ui-kits/` directory read-only for
design-system CSS imports.

Manual frontend flow:

```bash
npm install
npm run dev
npm run build
```

`npm run dev` starts Vite and proxies `/api` and `/health` to the backend URL.
Default backend URL:

```text
http://localhost:8000
```

Override it for local development:

```bash
VITE_BACKEND_URL=http://localhost:8000 npm run dev
```

For built/static deployments, set `VITE_API_BASE_URL` if the API is not served from the same origin.

## Verification

- Backend health opens at `http://localhost:8000/health`.
- Frontend opens at `http://localhost:5173`.
- Contacts table loads when a local active dataset exists.
- With no active dataset, the manual `Обновить из Bitrix` panel appears.
- Search, exact contact ID filter, type/region/status filters, sorting, reset, and pagination work.
- If the frontend shows an API error, check `http://localhost:8000/api/datasets/status`.

## Design System

The app imports `../ui-kits/styles.css`, which includes the approved color,
typography, spacing, and effects tokens. The Contacts screen mirrors the
provided SaaS web-app direction: light surface, left navigation, blue primary
states, Manrope typography, 8px controls, subtle borders, and compact data-table
density.
