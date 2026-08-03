# FastAPI Backend

The backend manages the existing 5G SA deployment without replacing its architecture. It reuses the validated scripts in `deployments/5g-sa/scripts/` as its primary operational implementation.

## Installation

```bash
make backend-install
```

The command pins pip, installs the exact direct requirements, and applies the
transitive dependency constraints from `backend/constraints.txt`.

## Environment Variables

Example from `backend/.env.example`:

```env
LAIN5G_PROJECT_ROOT=/path/to/Lain5G
LAIN5G_SCENARIO=5g-sa
LAIN5G_DRY_RUN=false
LAIN5G_MUTATING_OPERATIONS_ENABLED=false
LAIN5G_COMMAND_TIMEOUT=300
LAIN5G_LOG_TAIL_LINES=500
LAIN5G_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
LAIN5G_OPEN5GS_MONGO_URI=mongodb://mongo:27017/open5gs
LAIN5G_OPEN5GS_MONGO_DATABASE=open5gs
LAIN5G_OPEN5GS_SUBSCRIBER_COLLECTION=subscribers
LAIN5G_SUBSCRIBER_SECRETS_VISIBLE=false
LAIN5G_SUBSCRIBER_OPERATION_TIMEOUT=15
LAIN5G_OPEN5GS_DOCKER_NETWORK=lain5g-lab-5g-sa-core
LAIN5G_OPEN5GS_DOCKER_IP=10.20.0.250
```

The network name and address shown above are defaults for the checked-in 5G SA
profile, not universal Docker settings. Custom networks must select an unused
address in their configured subnet and update both values consistently.

`backend/.env` must not be committed.

## Running

```bash
make backend-dev
```

Equivalent command:

```bash
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend does not start Docker during startup.

## Endpoints

- `GET /api/health`
- `GET /api/deployments`
- `GET /api/deployments/5g-sa`
- `POST /api/deployments/5g-sa/start`
- `POST /api/deployments/5g-sa/stop`
- `POST /api/deployments/5g-sa/restart`
- `GET /api/deployments/5g-sa/status`
- `GET /api/deployments/5g-sa/logs?container=amf&tail=200`
- `POST /api/deployments/5g-sa/validate`
- `GET /api/runs`
- `GET /api/runs/latest`
- `GET /api/runs/{run_id}`
- `GET /api/validation/latest`
- `GET /api/subscribers/connection`
- `GET /api/subscribers`
- `GET /api/subscribers/{imsi}`
- `POST /api/subscribers/validate`
- `POST /api/subscribers`
- `PATCH /api/subscribers/{imsi}`
- `POST /api/subscribers/{imsi}/clone`
- `DELETE /api/subscribers/{imsi}`

## cURL Examples

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/deployments
curl -X POST http://127.0.0.1:8000/api/deployments/5g-sa/start
curl http://127.0.0.1:8000/api/deployments/5g-sa/status
curl -X POST http://127.0.0.1:8000/api/deployments/5g-sa/validate
curl http://127.0.0.1:8000/api/runs/latest
curl http://127.0.0.1:8000/api/deployments/5g-sa/logs?tail=200
curl -X POST http://127.0.0.1:8000/api/deployments/5g-sa/stop
curl http://127.0.0.1:8000/api/subscribers/connection
curl http://127.0.0.1:8000/api/subscribers
```

`/api/health` and the OpenAPI document expose the version read from the root
`VERSION` file.

## Dry-Run Mode

```bash
LAIN5G_DRY_RUN=true make backend-dev
```

In dry-run mode, the backend does not run Docker or actual operational scripts, does not modify `runs/`, and returns the command it would have executed. Validations are reported as `NOT_TESTED`.

## Error Codes

HTTP status and machine-readable `detail.code` values identify stable error
categories. Human-readable messages and command diagnostics vary with the
underlying host, profile, and failure; clients should not match exact wording.

- `400`: invalid request.
- `403`: mutation disabled by local configuration.
- `404`: scenario or run not found.
- `409`: state conflict, such as starting an already active deployment.
- `422`: FastAPI input validation error.
- `500`: handled internal error or failed command.
- `504`: command timeout.

Example:

```json
{
  "detail": {
    "code": "DEPLOYMENT_START_FAILED",
    "message": "The 5G SA deployment could not be started.",
    "exit_code": 1,
    "stderr": "..."
  }
}
```

## Security

- Mutations require `LAIN5G_MUTATING_OPERATIONS_ENABLED=true`; dry-run mode does not require this setting.
- RF authorization remains independent through `LAIN5G_RF_WEB_CONTROL_ENABLED` and the existing RF controls.
- `shell=True` is not used.
- Scripts must be located within the repository.
- Symbolic links that resolve outside the project are rejected.
- Complete environment variables are not returned.
- Values associated with `SUBSCRIBER_KEY`, `SUBSCRIBER_OPC`, `SUBSCRIBER_OP`, `K`, `KI`, `OP`, and `OPC` are redacted.
- Subscriber endpoints do not return complete K, OP, or OPc values; they return only redacted indicators.
- `runs/` is read without allowing path traversal or access to arbitrary files.
- See `docs/security/local-deployment.md` and `docs/security/threat-model.md`.

## Structure

```text
backend/app/api/          FastAPI routers
backend/app/models/       Pydantic models
backend/app/services/     command execution, deployments, runs, and validation
backend/tests/            isolated tests and fixtures
```

## Tests

```bash
make backend-test
make backend-cov
```

The unit tests use fixtures and `LAIN5G_DRY_RUN=true`; they do not require a live Docker daemon or modify the actual `runs/` directory.
