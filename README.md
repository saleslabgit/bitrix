# Bitrix Sales Analytics

Internal sales analytics system based on Bitrix CRM data.

## Current Stage

The project is at the initial scaffold stage. The backend has a minimal FastAPI application with a health endpoint and pytest coverage. Business analytics, Bitrix integration, authentication, local storage, and frontend screens are not implemented yet.

Frontend implementation is blocked until the external design system is approved.

## Quick Start

Copy the placeholder environment file if local overrides are needed:

```bash
cp .env.example .env
```

Run the backend through Docker Compose:

```bash
docker compose up --build backend
```

The backend serves:

```text
GET http://localhost:8000/health
```

Run backend tests locally:

```bash
cd backend
pytest
```

## Key Commands

```bash
docker compose config
docker compose up --build backend
cd backend && pytest
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
