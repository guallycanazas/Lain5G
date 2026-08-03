# 4G LTE and VoLTE Network

This directory retains two implementations:

- `4g-volte-sim`: historical implementation with EPC, IMS, srsENB, and srsUE;
  it is not part of the public operational interface.
- `4g-lte-x310`: controlled public RF path with EPC and srsENB for USRP X310.

The RF path does not start automatically and requires preflight, a safety manifest, and `LAIN5G_ALLOW_RF_START=true`.

The software VoLTE validation covers LTE, EPC, bearer/APN, data connectivity,
IMS services, DNS, subscriber provisioning, and authenticated SIP registration.
The [public result `run-20260723-055149`](../../results/public/4g-ims-sim/run-20260723-055149.json)
records 22/22 `PASS` checks and a `SIMULATION_ONLY` classification.

## Setup

```bash
cp deployments/4g-volte/common/.env.example deployments/4g-volte/common/.env
```

Edit `deployments/4g-volte/common/.env` and use lab keys, never real credentials.

## Historical Software Simulation

The VoLTE manifests and results are retained for traceability and static tests,
without a public launcher.

The `sip-register` evidence verifies the REGISTER exchange, 401 challenge,
authenticated REGISTER, and final 200 OK response. Together with the LTE/EPC/IMS
checks, it establishes the software-validated VoLTE signaling flow. Audio, voice
quality, and RTP performance belong to a separate media test.

## X300/X310 Profile: Core Only (No RF)

```bash
make build-4g-lte-x310
make check-x310
make preflight-4g-lte-x310
make start-4g-lte-x310-epc
make stop-4g-lte-x310
```

## X300/X310 Profile: RF Operation

RF operation requires `safety-manifest.yaml`, `channel-plan.yaml`, `LAIN5G_ALLOW_RF_START=true`, actual authorization, and a finite duration. See `docs/rf_safety.md` before using `make start-4g-lte-x310-rf`.
