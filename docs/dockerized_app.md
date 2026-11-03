# Dockerized Application

The dockerized application stack runs independently of the lab's 4G and 5G
scenarios:

- `frontend`: Nginx serving the React application and proxying `/api`.
- `backend`: FastAPI; access to the host's Docker daemon requires a separate opt-in.
- `prometheus`: scrapes the backend and monitoring services on the private Compose network.
- `loki`: retains centralized container logs locally for seven days.
- `grafana`: reads Prometheus and Loki and provisions runtime and log dashboards.
- `alloy`: in operations mode, discovers OpenLain5G Compose containers and forwards their logs to Loki.

It does not replace the network deployments selected by the user.

## CLI Usage

```bash
./lain5g app start --operations --open
./lain5g app status
./lain5g app logs
./lain5g app stop
```

`app start` creates `.env.app`, automatically records the repository's absolute
path, and restricts the file to `0600` permissions. `--operations` enables
downloads and operations for software and RF scenarios from the interface.

The operational opt-in enables `LAIN5G_MUTATING_OPERATIONS_ENABLED` and
`LAIN5G_IMAGE_PULL_ENABLED`, uses `docker-compose.app-operations.yml`, and keeps
`LAIN5G_RF_WEB_CONTROL_ENABLED=true`. This enables the protected RF workflow, not
automatic transmission: every session continues to require preflight checks,
authorization, the checklist, the exact phrase, a finite duration, and
emergency-stop safeguards.

The user selects 4G LTE, 5G SA, or the protected RF profiles under **Scenarios**.
When the selected simulation starts, the backend creates or retains its local
synthetic credentials file with `0600` permissions without returning secrets to the app.

## Direct Usage with Make

```bash
make app-up
make app-ps
make app-logs
make app-down
```

These targets do not create `.env.app`; first run `./lain5g app setup`, or copy and
edit `.env.app.example` manually.

Web interface:

```text
http://127.0.0.1:8080
```

API exposed for local debugging:

```text
http://127.0.0.1:8000/api/health
```

Observability interfaces:

```text
Grafana metrics: http://127.0.0.1:8080/grafana/d/openlain5g-runtime/openlain5g-runtime
Grafana components: http://127.0.0.1:8080/grafana/d/openlain5g-components/openlain5g-components
Grafana logs:    http://127.0.0.1:8080/grafana/d/openlain5g-logs/openlain5g-central-logs
Grafana direct: http://127.0.0.1:3000/d/openlain5g-runtime/openlain5g-runtime
Prometheus:  http://127.0.0.1:9090/targets
Backend:     http://127.0.0.1:8000/metrics
```

The frontend's **Metrics** page links to separate application-runtime and
network-component dashboards and keeps the latest validation summary separate.
The application-runtime dashboard shows scrape status, backend request rate,
p95 API latency, 5xx responses, and Python process CPU and memory. The backend
exports bounded route-template labels only; request paths, query strings,
IMSIs, phone numbers, and subscriber credentials are not metric labels.

The **Network Components** dashboard groups RAN (srsRAN / UERANSIM), Open5GS
packet-core functions, IMS voice services (Kamailio / SIP / RTP), and subscriber
data services. Its component activity and error panels are derived from Loki
container logs. The current profile images do not export radio or protocol KPIs
such as CQI, MCS, BLER, SIP transaction counters, or per-subscriber throughput
to Prometheus; those values are not inferred from log volume.

The **Logs** page keeps the direct, recent Docker Compose output and links to a
central Grafana log dashboard. Alloy discovers Compose containers whose project
name begins with `lain5g-lab-` and applies `scenario`, `service`, and `container`
labels plus an architecture `component` label (`ran`, `open5gs_core`,
`ims_voice`, `subscriber_data`, `platform`, or `support`) before sending output
to Loki. The central logs dashboard has profile and service filters, log
volume, error counts, and a searchable log stream. Loki
keeps logs for seven days in the `loki-data` volume; Prometheus keeps metrics for
15 days. Central collection starts with `./lain5g app start --operations --open`;
the base, read-only application mode leaves the Docker socket unmounted and does
not collect Docker logs into Loki. The direct Logs page continues to read
Docker's local log buffer.

Prometheus, Grafana, Loki, Alloy, the backend, and the frontend communicate
using Compose service DNS names on `lain5g-lab-app` (`backend:8000`,
`prometheus:9090`, `loki:3100`, and `grafana:3000`). Prometheus samples every 15 seconds and retains 15 days of
time series. Named Docker volumes persist Prometheus data and Grafana state
across container recreation; Loki and Alloy also persist log chunks and read
positions in named volumes. Host ports are bound to loopback and can be
changed with `PROMETHEUS_PORT` and `GRAFANA_PORT` in `.env.app`; the Metrics
page link uses the frontend's same-origin `/grafana/` proxy, so it continues
to work when the host-side frontend port changes. Port 3000 remains available
for direct local access.

Grafana is provisioned with read-only dashboards and Prometheus and Loki data sources.
It allows anonymous viewer access because the service is local-only and bound
to loopback; do not publish these ports on an untrusted network.

## Manual Build

```bash
make app-build
```

The backend build uses the root context to copy `VERSION`; its Python packages
are resolved with `src/backend/constraints.txt`. The frontend installs from
`src/frontend/package-lock.json` using `npm ci`.

Equivalent command:

```bash
docker compose --env-file .env.app -f docker-compose.app.yml build
```

## Dry-Run Mode

To test the application without starting actual 5G SA containers:

```env
LAIN5G_DRY_RUN=true
```

In this mode, the backend returns the commands it would have executed, and validations appear as `NOT_TESTED`.

## Operational Security

- The base Compose configuration does not mount `/var/run/docker.sock`, uses a read-only project directory, and publishes only on loopback.
- `docker-compose.app-operations.yml` explicitly enables a writable project directory and Docker socket access for the backend and Alloy, which is equivalent to root control of the host.
- Mutations also require `LAIN5G_MUTATING_OPERATIONS_ENABLED=true`.
- Do not expose the application outside the local machine.
- `.env.app`, `src/backend/.env`, `src/frontend/.env`, and `deployments/5g-sa/.env` must not be committed.
- Do not use real keys or non-anonymized IMSIs in the lab.
- See `docs/security/local-deployment.md` for the exact opt-in command.

## Relationship to the 5G SA Lab

The backend calls the existing scripts:

```text
deployments/5g-sa/scripts/start.sh
deployments/5g-sa/scripts/stop.sh
deployments/5g-sa/scripts/restart.sh
deployments/5g-sa/scripts/status.sh
deployments/5g-sa/scripts/logs.sh
deployments/5g-sa/scripts/validate.sh
```

The application stack is defined in `docker-compose.app.yml`. The operational 5G SA stack remains in `deployments/5g-sa/docker-compose.yml`.

## Subscriber Management

The backend uses `pymongo` to access Open5GS MongoDB when the lab is active. The app does not depend on MongoDB at startup: if 5G SA is stopped, `/api/subscribers/connection` returns `disconnected` or `timeout`, and the rest of the application continues to operate.

The connection is controlled by:

```env
LAIN5G_OPEN5GS_MONGO_URI=mongodb://mongo:27017/open5gs
LAIN5G_OPEN5GS_MONGO_DATABASE=open5gs
LAIN5G_OPEN5GS_SUBSCRIBER_COLLECTION=subscribers
LAIN5G_OPEN5GS_DOCKER_NETWORK=lain5g-lab-5g-sa-x310-core
LAIN5G_OPEN5GS_DOCKER_IP=10.20.0.250
```

The backend attempts to join an existing 5G SA Docker network only when
`LAIN5G_MUTATING_OPERATIONS_ENABLED=true`. In the checked-in profile,
`10.20.0.250` is reserved to avoid its known static service addresses. A custom
subnet must use an available address inside that subnet and update the network
and IP variables consistently. The 5G startup process also corrects a stale
connection before cleaning up or starting services. Base mode never modifies
Docker networks.

See `docs/subscribers.md`.
