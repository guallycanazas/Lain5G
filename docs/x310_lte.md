# X310 LTE

`4g-lte-x310` prepares an LTE eNB with srsRAN 4G and UHD for compatible USRP
X-Series hardware. The historical profile name is retained. The EPC and IMS can
be started without RF; the RF eNB is in a separate Compose profile named `rf`.

## Commands Without RF

```bash
./lain5g scenario setup 4g-lte-x310
make build-4g-lte-x310
make check-x310
make preflight-4g-lte-x310
make start-4g-lte-x310-epc
make status-4g-lte-x310
make stop-4g-lte-x310
```

## Starting RF

Do not start RF operation until you have met the requirements in `docs/rf_safety.md`.

Minimum requirements:

- `deployments/4g-volte/x310/rf/channel-plan.yaml` created from the example and reviewed.
- `deployments/4g-volte/x310/rf/safety-manifest.yaml` created from the example and set to `authorization_confirmed: true`.
- `LAIN5G_ALLOW_RF_START=true` set only for the authorized operation.
- A finite duration specified by `maximum_duration_seconds`.

Command:

```bash
LAIN5G_ALLOW_RF_START=true make start-4g-lte-x310-rf
```

The script runs the preflight checks, starts only `enb-x310`, waits for the specified duration, and performs an automatic stop.

## Starting from the Interface

Run `./lain5g app start --operations --open` and open
`http://localhost:8080/scenarios/4g-lte-x310`.
Use `EPC + IMS, no RF` to verify the infrastructure without transmitting.
`Start core + RF` displays the effective channel plan, downloads missing
components after confirmation, and requires all safeguards to be completed. The
`Emergency stop` button remains available in the workspace.

## Scope of Observations

Host-side discovery depends on the installed UHD tools, network and device
availability, and the current run. Use the current hardware check and preflight
results rather than inferring readiness from another host or session. No public
release artifact establishes end-to-end RF operation; consult the
[canonical table](../README.md#canonical-capability-status) for the supported
evidence boundary.

The UHD image does not update FPGA images or firmware at startup.
