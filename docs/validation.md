# Validation

This guide defines criteria and outputs and indexes public artifacts without
creating a second normative matrix. See the
[canonical capability table](../README.md#canonical-capability-status), which
separates public, private, and historical evidence. The current LTE and 5G SA
results evaluate source commit `59471947da95783c1a85a4d18284360e4b6d898b`
on a clean Ubuntu 24.04 VM. The July 23 artifacts retain their historical commit
and pre-release version.

Public evidence for the stable `1.1.0` release includes:

- [5G SA software](../results/public/5g-sa-sim/run-20260730-021914.json):
  15/15 checks `PASS`, `SIMULATION_ONLY`.
- [LTE software](../results/public/4g-lte-sim/run-20260730-021702.json):
  14/14 checks `PASS`, `SIMULATION_ONLY`.
- [4G VoLTE/IMS software](../results/public/4g-ims-sim/run-20260723-055149.json):
  historical result with 22/22 checks `PASS`, `SIMULATION_ONLY`; validates LTE,
  EPC, IMS, data, and authenticated lab SIP registration.
- [VoNR software](../results/public/5g-vonr-sim/run-20260723-055328.json):
  `BLOCKED` and `NOT_VALIDATED` attempt; a later local run was reported as
  25/25, but it has no publicly reviewable artifact.

Automated validation is located at `deployments/5g-sa/scripts/validate.sh` and runs with:

```bash
make validate-5g-sa
```

Each check returns one of these states:

- `PASS`
- `FAIL`
- `WARNING`
- `NOT_TESTED`

The application groups these checks into a visual evidence chain. In simulation,
the stages are core, RAN link, UE registration/session, interface/IP, and a ping
bound to the UE tunnel. A stage appears green only when all of its required
checks have `PASS` evidence; a running container is not interpreted as UE
registration or user traffic. The overall status is also derived from the checks
and does not trust a `PASS` recorded by an old script.

For USRP profiles, the chain separates UHD detection, preflight, core, RAN
process, S1/NG link, and over-the-air UE testing. Running the eNB/gNB alone does
not demonstrate RF transmission or reception. The UE stage remains `NOT_TESTED`
until correlated evidence from external equipment is available for the
authorized session.

## 5G SA checks

- MongoDB running.
- NRF running.
- AMF running.
- SMF running.
- UPF running.
- AUSF running.
- UDM running.
- UDR running.
- PCF running.
- NG connection between the gNB and AMF.
- UE registration.
- PDU session establishment.
- `uesimtun0` TUN interface.
- IP assigned to the UE.
- ping from the UE to `PING_TARGET`.

The result is saved to `runs/<run-id>/validation.json`.

## 4G LTE checks

```bash
make validate-4g-lte-sim
make validate-4g-lte-x310
```

The `4g-lte-sim` path checks the EPC, S1 markers, srsUE registration, bearer, UE
interface, and data ping without starting IMS. The historical `4g-volte-sim`
evidence, whose public artifact uses the `4g-ims-sim` scope name, adds IMS
services, DNS, and lab SIP registration evidence.

The X310 path separates hardware, UHD, FPGA, EPC, IMS infrastructure
availability, RF preflight, auto-stop, and eNB log checks. Additional
end-to-end evidence must be collected separately and correlated with the
operator's `run-id`; it is not retained automatically. Dry-run mode does not
start RF.

`5g-sa-x310` likewise records its local evidence and correlated logs in `runs/`.

Current VoLTE validation covers LTE registration, bearer/APN, data, IMS
services, DNS, and the authenticated REGISTER exchange through 200 OK. Audio,
call-dialog, and RTP performance criteria are handled as separate media tests;
see [VoLTE criteria](volte_validation.md).
