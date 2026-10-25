# 5G SA and VoNR Network

The `5g-vonr-sim` profile is available from the operational catalog. It
integrates Open5GS 5GC, UERANSIM gNB/UE, internet and IMS DNNs, IMS DNS, and
P/I/S-CSCF. Validation checks the UE IMS PDU and authenticated SIP registration,
then runs two synthetic SIP phones through INVITE/180/200/ACK/BYE and a
bidirectional PCMU silence-packet check.

The virtual phones use the isolated Docker IMS bridge and traverse P-CSCF,
I-CSCF, and S-CSCF. Their call and RTP test does not establish a call from the
UERANSIM UE, traverse the UE media path, or contain audible speech. UE IMS PDU
and SIP registration are separate checks.
The scientific evidence boundary is maintained in the
[canonical capability table](../../README.md#canonical-capability-status).

A historical local software validation, `run-20260725-213427`, recorded 25/25
`PASS` checks for the earlier scenario criteria. It predates the synthetic call
check described above and is not evidence for that newer test.

The [earlier public run record `run-20260723-055328`](../../results/public/5g-vonr-sim/run-20260723-055328.json)
is retained for historical traceability. RF, commercial UE, audible voice, and
UE media-path evidence use separate correlated test scopes.

## Operation

```bash
./deployments/5g-vonr/scripts/start.sh
./deployments/5g-vonr/scripts/validate.sh
./deployments/5g-vonr/scripts/stop.sh
```
