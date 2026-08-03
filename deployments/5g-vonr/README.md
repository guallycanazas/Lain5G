# 5G SA and VoNR Network

This directory retains the internal `5g-vonr-sim` implementation, which
integrates Open5GS 5GC, UERANSIM gNB/UE, internet and IMS DNNs, IMS DNS, and
P/I/S-CSCF. The scientific status is maintained in the
[canonical capability table](../../README.md#canonical-capability-status).

A local run, `run-20260725-213427`, was reported with 25/25 `PASS` checks, but
no public artifact exists for independent review.

The [previous public artifact `run-20260723-055328`](../../results/public/5g-vonr-sim/run-20260723-055328.json)
is the only available public evidence and remains `BLOCKED` and `NOT_VALIDATED`.
This scenario is not in the current public operational catalog. RF, commercial
UEs, audio, and RTP performance are not publicly validated.

## Operation

```bash
./deployments/5g-vonr/scripts/start.sh
./deployments/5g-vonr/scripts/validate.sh
./deployments/5g-vonr/scripts/stop.sh
```
