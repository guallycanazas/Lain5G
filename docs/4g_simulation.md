# 4G Software Simulation

The public catalog provides `4g-lte-sim`: Open5GS EPC, srsENB, and srsUE
connected over ZMQ, without IMS.

## Usage

```bash
cp deployments/4g-volte/common/.env.example deployments/4g-volte/common/.env
make build-4g-lte-sim
make start-4g-lte-sim
make status-4g-lte-sim
make validate-4g-lte-sim
make logs-4g-lte-sim
make stop-4g-lte-sim
```

Before starting the scenario, edit the copied `.env` file with an editor of your
choice and keep only synthetic lab credentials in it.

## Validation

`make validate-4g-lte-sim` checks EPC services, S1 Setup, srsUE attach, the
default bearer, TUN interface, IP, and data ping. It does not start or validate
IMS components.

Possible states: `PASS`, `FAIL`, `WARNING`, `NOT_TESTED`.

The result is saved to `runs/<run-id>/validation.json`.

## Notes

- `pgwc` and `pgwu` are Compose service names. In Open5GS `v2.7.5`, they run
  `open5gs-smfd` and `open5gs-upfd` because that version does not install the
  `open5gs-pgwcd` or `open5gs-pgwud` binaries.
- `4g-lte-sim` uses its own project, `10.43.0.0/24` network, volume, and
  container names.
- Verify that `10.43.0.0/24` does not overlap the LAN, VPN, or administrative
  SSH route; an overlap can temporarily disrupt API access.
- Stopping the scenario stops the 4G containers without affecting `5g-sa`.
