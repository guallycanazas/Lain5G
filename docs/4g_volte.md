# 4G LTE and VoLTE Network

The `deployments/4g-volte` scenario adds a 4G path isolated from the `5g-sa` deployment. It does not reuse 5G SA networks, volumes, or Compose project names.

The scientific status is maintained exclusively in the
[canonical capability table](../README.md#canonical-capability-status).
This guide describes the composition, operation, and VoLTE signaling evidence
for the software scenario.

Available profiles:

- `4g-lte-sim`: EPC + srsENB + srsUE over ZMQ, without IMS services.
- `4g-volte-sim`: EPC + IMS + srsRAN 4G in software mode.
- `4g-lte-x310`: EPC + srsRAN 4G eNB for compatible USRP X-Series hardware,
  compact always-on IMS infrastructure, and RF disabled by default. The
  historical profile name is retained.

The [current public LTE result](../results/public/4g-lte-sim/run-20260730-021702.json)
records 14/14 `PASS` checks for source commit
`59471947da95783c1a85a4d18284360e4b6d898b` on a clean Ubuntu 24.04 VM. The
[public 4G IMS result](../results/public/4g-ims-sim/run-20260723-055149.json)
is historical and records 22/22. Both are `SIMULATION_ONLY`. The latter
corresponds to the `4g-volte-sim` profile and validates LTE, EPC, data, IMS
services, DNS, provisioning, and authenticated lab SIP registration.

## Current Scope

- Open5GS `v2.7.5`-based 4G EPC.
- Minimal IMS with Kamailio `5.8.8` and an initial SQL database.
- Provisioning of the `internet` and `ims` APNs for a lab subscriber.
- Static validations, operational scripts, and guided workspaces in the API/frontend.

## Validation Scope

- The software VoLTE network records 22/22 `PASS` checks.
- The evidence includes LTE registration, bearer/APN, connectivity, IMS, and an
  authenticated REGISTER through 200 OK.
- RF does not start without a real manifest, real channel plan, and explicit authorization.
- The USRP path does not update firmware or FPGA images automatically.
- The `4g-lte-x310` validator records IMS-service availability and eNB/S1
  evidence. IMS registration, call signaling, and media require separately
  collected, correlated operator evidence and are not retained automatically.

Audio metrics, the call dialog, and RTP performance are treated as separate
media tests and do not change the validated classification of the software
VoLTE network and signaling.

## Setup

```bash
cp deployments/4g-volte/common/.env.example deployments/4g-volte/common/.env
```

Edit the copied file with an editor of your choice. Set lab keys for
`SUBSCRIBER_KEY` and `SUBSCRIBER_OPC`. Do not use real IMSI, Ki, OPc, or MSISDN
values without anonymizing them.

## Main Commands

```bash
make build-4g-lte-sim
make start-4g-lte-sim
make validate-4g-lte-sim
make stop-4g-lte-sim
```

The VoLTE scenario is retained as a historical implementation and evidence,
but it is not part of the public operational interface.

```bash
make build-4g-lte-x310
make check-x310
make preflight-4g-lte-x310
make start-4g-lte-x310-epc
```

Actual RF startup uses `make start-4g-lte-x310-rf` and is documented in
[X310 LTE](x310_lte.md) and [RF safety](rf_safety.md).
