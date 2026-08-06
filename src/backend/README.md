# OpenLain5G Backend

FastAPI backend for preparing, operating, and validating the 4G LTE/VoLTE and
5G SA/VoNR lab networks, together with the controlled X-Series RF profiles and
the experimental NSA profile. The API reuses each scenario's version-controlled
scripts under `deployments/` and preserves their security boundaries.

## Development

```bash
make backend-install
make backend-dev
```

## Tests

```bash
make backend-test
make backend-cov
```

The API does not start Docker during startup. Actual operations run only when deployment endpoints are called.

## Open5GS Subscribers

The backend exposes `/api/subscribers` to manage subscriber documents in Open5GS MongoDB using `pymongo`.

Relevant variables:

```env
LAIN5G_OPEN5GS_MONGO_URI=mongodb://mongo:27017/open5gs
LAIN5G_OPEN5GS_MONGO_DATABASE=open5gs
LAIN5G_OPEN5GS_SUBSCRIBER_COLLECTION=subscribers
LAIN5G_SUBSCRIBER_SECRETS_VISIBLE=false
LAIN5G_SUBSCRIBER_OPERATION_TIMEOUT=15
LAIN5G_OPEN5GS_DOCKER_NETWORK=lain5g-lab-5g-sa-core
LAIN5G_OPEN5GS_DOCKER_IP=10.20.0.250
```

These values match the checked-in 5G SA profile. Custom Docker networks must use
an available address from their own subnet and update both network variables
consistently.

The endpoints do not return complete K, OP, or OPc values. See `docs/subscribers.md`.
