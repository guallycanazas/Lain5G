# Secure Local Deployment

## Base Mode

Create `.env.app` from the example and set only the absolute project path. Keep
the secure defaults:

```env
LAIN5G_MUTATING_OPERATIONS_ENABLED=false
LAIN5G_IMAGE_PULL_ENABLED=false
LAIN5G_RF_WEB_CONTROL_ENABLED=false
```

Start the base stack with:

```bash
docker compose --env-file .env.app -f docker-compose.app.yml up -d --build
```

This mode publishes the UI and API only on `127.0.0.1`, mounts the repository
read-only, and does not mount `/var/run/docker.sock`. It supports the UI,
project-backed reads, validation that does not need Docker authority, and
dry-run plans. Docker-backed status checks report unavailable when they cannot
reach the daemon.

For the strongest non-operational behavior, also set:

```env
LAIN5G_DRY_RUN=true
```

## Explicit Operations Opt-In

Only on a dedicated trusted workstation, set:

```env
LAIN5G_MUTATING_OPERATIONS_ENABLED=true
```

Then start with both Compose files, in this order:

```bash
docker compose --env-file .env.app \
  -f docker-compose.app.yml \
  -f docker-compose.app-operations.yml \
  up -d --build
```

The override changes the project mount to writable and adds the host Docker
socket. The override alone does not open mutation routes; the independent
environment setting is also required. Conversely, enabling the setting without
the override does not grant a container Docker or project-write capability.

Use the same file set when inspecting or removing this operational stack:

```bash
docker compose --env-file .env.app \
  -f docker-compose.app.yml \
  -f docker-compose.app-operations.yml \
  down
```

## Additional Opt-Ins

Image pulls require both the general mutation setting and:

```env
LAIN5G_IMAGE_PULL_ENABLED=true
```

RF execution requires the general mutation setting, all request and profile
safety checks, and the separate setting:

```env
LAIN5G_RF_WEB_CONTROL_ENABLED=true
```

Do not treat either setting as RF authorization. Complete the laboratory's
physical isolation, attenuation, frequency authorization, duration, and
emergency-stop procedures independently.

## Native Backend

Run the native backend only on loopback:

```bash
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Do not use `--host 0.0.0.0`, port forwarding, a public reverse proxy, or a LAN
bind. The backend intentionally has no user authentication because its only
supported boundary is a trusted local operator.

## MongoDB And Subscribers

Subscriber reads connect only to the configured Open5GS MongoDB endpoint.
When the mutation gate is false, a read never invokes `docker network connect`.
If the operational override and mutation gate are enabled, the backend may
attach itself to `LAIN5G_OPEN5GS_DOCKER_NETWORK` before connecting. Subscriber
writes require the general mutation setting or remain non-persistent in dry-run.

Never expose MongoDB through the web stack. Keep operational subscriber values
and runtime credentials outside Git, use owner-only file permissions, and do
not place secrets in operator notes or logs. API redaction is a last-resort
control, not secret storage.

## Verification

- Confirm UI and API URLs begin with `http://127.0.0.1` or `http://localhost`.
- Confirm mutation requests return `403 MUTATING_OPERATIONS_DISABLED` in base mode.
- Confirm `execute=false` real IMS plans and dry-run actions still work.
- Confirm the base backend has no `/var/run/docker.sock` mount.
- Stop using the operational override when Docker control is no longer needed.

The unavoidable Docker-socket risk and trust assumptions are detailed in
`docs/security/threat-model.md`.
