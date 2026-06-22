# Frontend

React/TypeScript/Vite frontend for the Bitrix sales analytics MVP.

Implemented screen:

- `Contacts` report table with search, filters, pagination, loading, error, and empty states.

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
- Contacts table loads.
- Search, filters, and pagination work.
- If the frontend shows an API error, check `http://localhost:8000/api/datasets/status`.

## Design System

The app imports `../ui-kits/styles.css`, which includes the approved color,
typography, spacing, and effects tokens. The Contacts screen mirrors the
provided SaaS web-app direction: light surface, left navigation, blue primary
states, Manrope typography, 8px controls, subtle borders, and compact data-table
density.
