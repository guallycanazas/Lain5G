# 5G SA

5G SA is the project's initial focus.

The scientific status is maintained in the
[canonical capability table](../README.md#canonical-capability-status). The
[public run `run-20260730-021914`](../results/public/5g-sa-sim/run-20260730-021914.json)
records 15/15 `PASS` checks and a `SIMULATION_ONLY` classification for source
commit `59471947da95783c1a85a4d18284360e4b6d898b`, run on a clean Ubuntu 24.04
VM. The July 23 result remains as a historical record.

## Commands

```bash
./lain5g scenario setup 5g-sa
./lain5g images pull 5g-sa
./lain5g scenario start 5g-sa
./lain5g scenario status 5g-sa
./lain5g scenario validate 5g-sa
./lain5g scenario logs 5g-sa
./lain5g scenario stop 5g-sa
```

## Editable files

- `deployments/5g-sa/open5gs/amf.yaml`
- `deployments/5g-sa/open5gs/smf.yaml`
- `deployments/5g-sa/open5gs/upf.yaml`
- `deployments/5g-sa/ueransim/gnb.yaml`
- `deployments/5g-sa/ueransim/ue.yaml` (secret-free template)
- `deployments/5g-sa/.env`

The profile can be applied through the CLI or API to generate a consistent
configuration. The files can also be edited manually, but the two methods should
not be mixed without reviewing the resulting diff. `.env` is local and remains
outside Git.

At startup, Compose renders a temporary copy of the UE YAML using the IMSI, K,
OPc, AMF, and SQN from `.env`. The runtime copy is not written to the repository.

## Expected evidence

The public summary reports 15 checks passed by the validator, including the
following. Software validation should be considered complete for that scope and
commit only when there is correlated evidence of:

- Open5GS started.
- gNB connected to the AMF.
- UE registered.
- PDU session established.
- `uesimtun0` interface created.
- IP assigned to the UE.
- successful ping from the UE.

Running containers alone do not validate the scenario.

UERANSIM simulation does not extrapolate to real radio operation. Registration,
the PDU session, and 5G SA data with a commercial UE remain `NOT_VALIDATED`.
