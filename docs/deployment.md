# Deployment

## FASTVPS Docker Path

Local development remains unchanged:

```bash
docker compose up --build
```

Production on FASTVPS uses a separate Compose file:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

The production Compose stack runs:

- `backend` on the private Docker network only;
- `web`, an nginx container serving the built frontend and proxying `/api/*`
  plus `/health` to `http://backend:8000`;
- one host binding for the hosting panel reverse proxy:
  `127.0.0.1:8080:80`.

The project does not manage public HTTPS certificates in this path. FASTVPS
panel or provider-level reverse proxy terminates HTTPS and forwards traffic to
the local app port.

## Server Setup

1. Clone or update the repository on the VPS.
2. Create the server-local environment file:

   ```bash
   cp deploy/fastvps/.env.production.example .env
   ```

3. Fill in `.env` on the server only. Use real values for:
   - `APP_AUTH_USERNAME`;
   - `APP_AUTH_PASSWORD`;
   - `APP_AUTH_SESSION_SECRET`;
   - `BITRIX_WEBHOOK_URL`;
   - `BITRIX_CONTACT_TYPE_FIELD`, when the field code is known.
4. Generate a strong session secret, for example:

   ```bash
   openssl rand -hex 32
   ```

5. Keep production auth enabled:

   ```text
   APP_AUTH_ENABLED=true
   APP_AUTH_COOKIE_SECURE=true
   ```

6. Start the production stack:

   ```bash
   docker compose -f docker-compose.prod.yml up --build -d
   ```

7. Check container state and logs:

   ```bash
   docker compose -f docker-compose.prod.yml ps
   docker compose -f docker-compose.prod.yml logs --tail=100
   ```

8. Verify the local app port on the VPS:

   ```bash
   curl -f http://127.0.0.1:8080/health
   curl -f http://127.0.0.1:8080/
   ```

## FASTVPS Panel Setup

In the FASTVPS hosting panel:

1. Create the site/domain.
2. Enable HTTPS in the panel.
3. Configure reverse proxying to the local app URL:

   ```text
   http://127.0.0.1:8080
   ```

4. Open the app through the HTTPS domain, not through the local port.

If the panel cannot proxy to `127.0.0.1:8080`, adjust the published host
binding or port in `docker-compose.prod.yml` according to the panel
requirements. Keep only the `web` service published; the backend must remain
private inside Docker.

Same-origin browser access is expected: the frontend, `/api/*`, and `/health`
are served through the same HTTPS domain, so the HttpOnly auth cookie works
cleanly.

## Operations

Restart after configuration changes:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Stop the production stack:

```bash
docker compose -f docker-compose.prod.yml down
```

Update after new commits:

```bash
git pull
docker compose -f docker-compose.prod.yml up --build -d
```

The Compose stack only starts services. It does not call Bitrix, refresh data,
or run scheduled sync jobs during startup. After login, refresh Bitrix data
manually from the UI with `Обновить из Bitrix`.

## Data And Backups

Production data persists in the repository-local `data/` directory through the
bind mount:

```text
./data:/app/data
```

Back up `data/` before server maintenance, before destructive Docker commands,
and before moving the app to another VPS. Store backups outside the repository
and outside the running container directory. The backup destination and
retention policy are operator decisions and are not automated by this task.

Restore by stopping the stack, replacing `data/` with the selected backup, and
starting the stack again:

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up --build -d
```

Do not commit `data/`, DuckDB files, Parquet snapshots, CSV exports, real `.env`
files, webhook URLs, passwords, or session secrets.
