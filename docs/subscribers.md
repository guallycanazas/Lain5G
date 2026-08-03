# Open5GS Subscriber Management

OpenLain5G manages Open5GS-compatible subscriber documents. It does not implement the 5G authentication algorithm or replace the AUSF, UDM, or UDR functions.

## Architecture

The React interface communicates exclusively with the FastAPI API:

```text
React /subscribers
  -> Nginx /api
  -> FastAPI /api/subscribers
  -> pymongo
  -> Open5GS MongoDB
```

MongoDB is not exposed to the browser. The UI cannot submit arbitrary MongoDB queries or collection names.

## MongoDB Connection

The backend uses these variables:

```env
LAIN5G_OPEN5GS_MONGO_URI=mongodb://mongo:27017/open5gs
LAIN5G_OPEN5GS_MONGO_DATABASE=open5gs
LAIN5G_OPEN5GS_SUBSCRIBER_COLLECTION=subscribers
LAIN5G_SUBSCRIBER_SECRETS_VISIBLE=false
LAIN5G_SUBSCRIBER_OPERATION_TIMEOUT=15
LAIN5G_OPEN5GS_DOCKER_NETWORK=lain5g-lab-5g-sa-core
LAIN5G_OPEN5GS_DOCKER_IP=10.20.0.250
LAIN5G_MUTATING_OPERATIONS_ENABLED=false
```

When the 5G SA lab is stopped, the application still starts, and
`/api/subscribers/connection` gracefully returns a `disconnected` or `timeout`
status.

When the configured Docker network exists, the backend can connect to it only if
mutations are enabled. The checked-in 5G SA profile reserves `10.20.0.250`
relative to its own subnet and known static services. Custom deployments must
choose an unused address inside their configured subnet and update both network
and IP settings consistently. 5G SA is not started automatically.

## Supported Schema

The schema is based on `deployments/5g-sa/mongo/subscriber-init.js`:

- `imsi`
- `msisdn`, optional
- `security.k`
- `security.op`
- `security.opc`
- `security.amf`
- `security.sqn`
- `slice[0].sst`
- `slice[0].sd`
- `slice[0].session[0].name` as the DNN

The Open5GS AMBR, QoS, `schema_version`, `subscriber_status`, `network_access_mode`, and `access_restriction_data` fields are generated with values from the base deployment.

## Validation

- IMSI: required, digits only, 5 to 15 characters, unique.
- MSISDN: optional, digits only, 5 to 20 characters.
- K, OP, and OPc: 32-character hexadecimal values.
- K with OP or K with OPc is accepted; OP and OPc cannot be provided together.
- AMF: 4-character hexadecimal value.
- SQN: 12-character hexadecimal value; leading zeros are preserved.
- SST: integer from 1 to 255.
- SD: 6-character hexadecimal value.
- DNN: safe name without spaces. The base deployment uses `internet`; `ims` is reserved for future IMS stages.

## Secret Redaction

The list and detail endpoints never return complete `security.k`, `security.op`, or `security.opc` values. They return indicators:

```json
{
  "k_configured": true,
  "op_configured": false,
  "opc_configured": true,
  "amf": "8000",
  "sqn": "************"
}
```

When editing, leaving K, OP, or OPc empty preserves the current value. Masked strings such as `********` or `[REDACTED]` are rejected as new secrets.

## Endpoints

- `GET /api/subscribers/connection`
- `GET /api/subscribers?limit=50&offset=0&search=00101`
- `GET /api/subscribers/{imsi}`
- `POST /api/subscribers/validate`
- `POST /api/subscribers`
- `PATCH /api/subscribers/{imsi}`
- `POST /api/subscribers/{imsi}/clone`
- `DELETE /api/subscribers/{imsi}` with body `{"confirm": true}`

## Operations

Create, edit, clone, and delete operations modify Open5GS MongoDB directly only when `LAIN5G_DRY_RUN=false` and `LAIN5G_MUTATING_OPERATIONS_ENABLED=true`. They do not automatically restart the lab or disconnect UEs.

Cloning copies credentials internally to a new IMSI but does not include them in the response.

Deletion requires explicit confirmation. An active UE session may persist temporarily until it is disconnected or registers again.

## Dry-Run Mode

With `LAIN5G_DRY_RUN=true`, write operations validate the payload but return:

```json
{
  "dry_run": true,
  "persisted": false
}
```

They do not insert, modify, or delete actual documents.

## Tests

```bash
make subscribers-test
```

The unit tests use in-memory collections and do not depend on an actual MongoDB instance.

Live integration testing requires explicit confirmation:

```bash
LAIN5G_ALLOW_INTEGRATION_WRITES=true make subscribers-integration-test
```

The documented workflow validates connection, listing, creation, editing, cloning, deletion, and the subsequent `make validate-5g-sa` command.

## Risks

- The base Compose configuration does not mount `/var/run/docker.sock`; the optional operational override grants control equivalent to root access on the host.
- Do not expose the application outside loopback.
- Do not use real IMSIs or keys without anonymizing them.
- The existence of a document in MongoDB does not demonstrate successful UE authentication.
