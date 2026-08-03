# Configuration

## Editable sources

- `config/profiles/*.yaml` contains versioned profiles. Simulation identifiers
  are synthetic vectors; RF profiles do not constitute operational
  authorization.
- Scenario `.env` files are local and ignored by Git.
- Files under `deployments/*` are effective outputs or templates that must be
  reviewed after applying a profile.

## System-generated files

- `runs/<run-id>/metadata.json`
- `runs/<run-id>/validation.json`
- `runs/<run-id>/metrics.json`
- `runs/<run-id>/logs/docker-compose.log` when `make logs-5g-sa` is run.

## Common changes

The CLI and API can validate and apply profiles to keep values shared across
`.env`, Open5GS, and RAN/UE consistent. First review the planned changes and inspect
the diff before applying changes. Manual editing remains possible, but it must
maintain the same consistency across all files.

To change a synthetic simulation identifier, preferably use the corresponding
profile. If editing manually, keep the following consistent:

- `SUBSCRIBER_IMSI`, `SUBSCRIBER_KEY`, and `SUBSCRIBER_OPC` in each simulation's
  private `.env` file.
- The `deployments/5g-sa/ueransim/ue.yaml` template, which receives those
  credential values when creating the runtime configuration inside the UE
  container.
- The `deployments/4g-lte-sim/ran/ue.conf` template, which receives the same
  credentials used by the Open5GS provisioner before starting srsUE.
