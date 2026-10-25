# 5G VoNR

The `5g-vonr-sim` software scenario is available in the operational catalog. It
integrates 5G SA, two DNNs, and a lab IMS. Validation checks the UE IMS PDU and
authenticated SIP registration, then places a synthetic SIP call through the
lab IMS. Its classification is maintained in the
[canonical capability table](../README.md#canonical-capability-status).

The two synthetic phone endpoints are on the isolated Docker IMS bridge. Their
signaling traverses P-CSCF, I-CSCF, and S-CSCF. The call check verifies SIP
setup/teardown and bidirectional PCMU silence packets; it does not verify
audible speech or RTP through the UERANSIM UE's PDU path.

A historical local software validation, `run-20260725-213427`, recorded 25/25
`PASS` checks for the earlier scenario criteria. It predates the synthetic call
check described above and is not evidence for that newer test.

The [earlier public run record `run-20260723-055328`](../results/public/5g-vonr-sim/run-20260723-055328.json)
is retained for historical traceability. RF, commercial UE, audible voice, and
UE media-path evidence remain separate correlated test scopes.
