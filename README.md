# Bitrix Sales Analytics

Internal sales analytics system based on Bitrix CRM data.

## Current Stage

The backend has local DuckDB storage, synthetic and mocked Bitrix ingestion,
manual read-only Bitrix refresh, NBRB-backed local USD normalization, local
analytics endpoints, active dataset metadata, and allowlisted raw Parquet
snapshots.

The frontend has React/Vite Contacts and Deals report screens that read only
local backend endpoints. Authentication, deployment hardening, and additional
report screens are not implemented yet.

## Quick Start

Copy the placeholder environment file if local overrides are needed:

```bash
cp .env.example .env
```

Run the app through Docker Compose:

```bash
docker compose up --build
```

Local URLs:

```text
Backend:  http://localhost:8000
Frontend: http://localhost:5173
```

Run backend tests locally:

```bash
cd backend
pip install -e ".[dev]"
pytest
```

## Key Commands

```bash
docker compose config
docker compose up --build
cd backend
pip install -e ".[dev]"
pytest
```

## Documentation Map

- `SPEC.md` - approved product and technical requirements.
- `WORKFLOW.md` - collaboration, task, report, and commit protocol.
- `AGENTS.md` - repository coding rules and operational constraints.
- `docs/project-status.md` - current phase, completed work, blockers, and next steps.
- `docs/architecture.md` - target architecture and module boundaries.
- `docs/development.md` - local setup, commands, environment policy, and limitations.
- `docs/data-model.md` - MVP entities, storage layers, and data safety rules.
- `docs/testing.md` - current checks and future required test areas.
- `backend/README.md` - backend structure and commands.
- `design-system/README.md` - design-system status.
- `frontend/README.md` - frontend status.
