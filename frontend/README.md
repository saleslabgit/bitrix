# Frontend

React/TypeScript/Vite frontend for the Bitrix sales analytics MVP.

Implemented screen:

- `Contacts` report table with search, filters, pagination, loading, error, and empty states.

The app reads only the local backend API. It does not call Bitrix.

## Commands

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

## Design System

The app imports `../ui-kits/styles.css`, which includes the approved color,
typography, spacing, and effects tokens. The Contacts screen mirrors the
provided SaaS web-app direction: light surface, left navigation, blue primary
states, Manrope typography, 8px controls, subtle borders, and compact data-table
density.
