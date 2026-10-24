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

The backend defaults to the 4G LTE X310 database. The Subscribers screen has an
explicit network-profile selector and sends that profile with each list,
connection, detail, create, edit, clone, and delete request. The API accepts
only the supported profile identifiers; it never accepts an arbitrary MongoDB
URI or Docker network from the browser.

Profile routing is fixed:

| UI profile | Open5GS database | Notes |
| --- | --- | --- |
| `4g-lte-x310` | `lain5g-lab-4g-lte-x310-mongo` | LTE EPC |
| `5g-nsa-x310` | `lain5g-lab-4g-lte-x310-mongo` | NSA uses the shared LTE EPC |
| `5g-sa-x310` | `lain5g-lab-5g-sa-x310-mongo` | 5G standalone core |

The selected X310 core must be running before the corresponding database can
connect. Selecting a UI profile does not start its containers or the RAN.

The backend uses these fallback variables when a custom deployment is used:

```env
LAIN5G_OPEN5GS_MONGO_URI=mongodb://mongo:27017/open5gs
LAIN5G_OPEN5GS_MONGO_DATABASE=open5gs
LAIN5G_OPEN5GS_SUBSCRIBER_COLLECTION=subscribers
LAIN5G_SUBSCRIBER_SECRETS_VISIBLE=false
LAIN5G_SUBSCRIBER_OPERATION_TIMEOUT=15
LAIN5G_OPEN5GS_DOCKER_NETWORK=lain5g-lab-5g-sa-x310-core
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
- `slice[0].session[*].name` as subscribed DNNs

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
- The subscriber form offers `Voice + data` (default) and `Data only` presets. The voice preset provisions `internet` with QCI/5QI 9 and `ims` with QCI/5QI 5, plus the example voice/video policy rules (1 and 2) used by the IMS profile. Data-only provisions `internet` only. For 5G SA, the IMS DNN uses the separate `10.46.0.0/16` pool and UPF tunnel; the internet DNN remains on `10.45.0.0/16`.
- AMF defaults to `8000`; SQN defaults to `000000000001` on creation and is hidden under advanced settings. Leave SQN alone unless the SIM is out of sync. Ki and OP/OPc remain SIM-specific and must match the programmed SIM.
- The default DNN is `internet`. IMS provisioning separately reconciles the `internet` and `ims` sessions and pyHSS APN records. For authenticated IMS registration, provision or sync the same IMSI in the IMS view as well; the IMS packet session alone does not create an IMS identity.

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

## One logical subscriber and service records

Use the same IMSI for one person across packet-core and IMS provisioning. The
IMS view is a synchronization/status view, not a second human identity: the
selected IMS runtime stores an Open5GS packet record and a pyHSS/AuC IMS record
because those services use different databases and protocols. `internet` and
`ims` APNs are shared network profiles; provisioning an IMSI reconciles those
profiles rather than creating a second user. The standalone real-IMS package
has its own isolated Open5GS MongoDB, separate from each X310 scenario's core
database, as described in [`real_ims.md`](real_ims.md).

When both local IMS modes are running, use **Sync to 5G** or **Sync to 4G** on
the existing IMS identity to provision it in the other mode. The backend reads
authentication data from the source mode's local Open5GS database and sends it
only to the selected local target. The operation reconciles the target's
Open5GS subscriber, pyHSS/AuC records, and preconfigured `internet` and `ims`
APNs; it does not create another human identity.

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
