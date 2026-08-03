# 5G SA and VoNR Network

This directory retains the internal `5g-vonr-sim` implementation, which
integrates Open5GS 5GC, UERANSIM gNB/UE, internet and IMS DNNs, IMS DNS, and
P/I/S-CSCF. The scientific status is maintained in the
[canonical capability table](../../README.md#canonical-capability-status).

A historical local software validation, `run-20260725-213427`, recorded 25/25
`PASS` checks across the scenario criteria.

The [earlier public run record `run-20260723-055328`](../../results/public/5g-vonr-sim/run-20260723-055328.json)
is retained for historical traceability. This scenario is retained as a
historical implementation rather than part of the current public operational
catalog. RF, commercial UE, call, audio, and RTP evidence use separate
correlated test scopes.

## Operation

```bash
./deployments/5g-vonr/scripts/start.sh
./deployments/5g-vonr/scripts/validate.sh
./deployments/5g-vonr/scripts/stop.sh
```
