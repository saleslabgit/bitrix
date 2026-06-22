# Frontend

React/TypeScript/Vite frontend for the Bitrix sales analytics MVP.

Implemented screen:

- `Contacts` report table with search, filters, clickable deal counters, clickable customer revenue chart modal, pagination, loading, error, and empty states.
- The Contacts table uses `/api/reports/contacts/analytics` and displays sortable local analytics rows, exact contact ID filtering, deal creation date filtering, Bitrix contact-card links, USD budget breakdown, won-only USD revenue, USD estimated profit, latest won close date, and latest deal date. It does not use original-currency sums as the primary financial metric.
- Contacts table state is persisted in browser local storage under `bitrix-sales.contacts.v1`; reset clears the stored state.
- Clicking a contact name opens a modal chart from `/api/reports/contacts/{contact_id}/won-revenue-series`. The chart uses local closed won deals only, aggregates USD revenue by close date, shows total revenue and won deal count, and follows the current Contacts date inputs as the selected period context.
- `Deals` report table with client search, exact deal ID, status, type, deal creation date filters, pagination, loading, error, empty, reset, Bitrix deal-card links, and sortable local USD budget/profit columns.
- The Deals table uses `/api/reports/deals/analytics`. `Бюджет` is the single deal amount in local USD, `Выручка` is won-only USD revenue, and `Прибыль` is won-only: `budget_usd * 0.50` for `won`, otherwise `0.00`. Filtered budget/revenue/profit totals are shown above and below the table and are calculated across all filtered rows before pagination.
- Deals table state is persisted in browser local storage under `bitrix-sales.deals.v1`; reset clears only Deals table state.
- `ABC` report table with exact customer ID, customer search, type, `Было` ABC segment, migration priority, changed-only filter, applied `Было` period, optional applied `Стало` period, pagination, loading, error, empty, reset, Bitrix contact-card links, and sortable local USD revenue/share columns.
- The ABC table uses `/api/reports/abc/analytics`. `Было` ABC is calculated from won-only USD revenue by local `closed_at` dates. When both `Стало` dates are applied, target revenue/segment, transition, and priority columns are shown in the same table; customers with revenue in either period are included so lost and reappeared customers remain visible. Transition direction is always `ABC было -> ABC стало`.
- The ABC filter toolbar wraps inside the report workspace. `Только изменившие ABC` is disabled until `Стало` is applied and is not sent for single-period ABC requests.
- ABC table state is persisted separately under `bitrix-sales.abc.v1`; reset clears only ABC table state.
- Last valid filter metadata is persisted under `bitrix-sales.filter-metadata.v1` so transient empty metadata snapshots do not clear dropdown options.
- Local Vite serves `/favicon.ico` from `frontend/public/favicon.ico`.
- Region filters and columns are temporarily hidden in Contacts, Deals, and ABC while region detection is unfinished. Existing backend region support remains available for later use.
- Contacts, Deals, and ABC table cards are bounded to the available viewport height. Rows scroll inside the card with sticky table headers, while pagination remains visible at the bottom; Deals and ABC totals remain outside the row scroll area.

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
local data. If an active `data/analytics.duckdb` dataset exists, the Contacts,
Deals, and ABC tables load normally. If the screen says `Локальная база не подготовлена.`,
click `Обновить из Bitrix`; the backend runs the manual read-only refresh,
applies approved contact type rules, reruns local normalization, loads NBRB
rates, and then the screen reloads status, filters, and report rows. Local
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
- Contacts, Deals, and ABC tables load when a local active dataset exists.
- With no active dataset, the manual `Обновить из Bitrix` panel appears.
- Contacts search, exact contact ID filter, deal creation date range, type/status filters, clickable non-zero deal counters, sorting, reset, and pagination work.
- Contact names open a modal with won USD revenue by close date; loading, error, empty, Escape, close button, and backdrop-close states work without resetting the Contacts table.
- Deals client search, exact deal ID filter, deal creation date range, type/status filters, sorting, filtered totals, reset, and pagination work. The working area uses the available screen width with horizontal table scroll where needed.
- ABC customer search, exact customer ID filter, `Было` period, optional `Стало` period, segment/priority filters, changed-only mode, sorting, summary totals, reset, and pagination work. `Стало` updates the same table instead of opening a separate table, and ABC filters do not overflow the visible workspace.
- If the frontend shows an API error, check `http://localhost:8000/api/datasets/status`.

## Design System

The app imports `../ui-kits/styles.css`, which includes the approved color,
typography, spacing, and effects tokens. The Contacts, Deals, and ABC screens mirror the
provided SaaS web-app direction: light surface, left navigation, blue primary
states, Manrope typography, 8px controls, subtle borders, and compact data-table
density.
