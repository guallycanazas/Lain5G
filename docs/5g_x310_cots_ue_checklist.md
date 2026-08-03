# 5G SA X310 COTS UE Checklist

Use this checklist before any RF transmission with `5g-sa-x310`. Do not commit actual IMSI, K, OPc, Ki, AMF, SQN, or password values to Git.

## Equipment

- A handset that supports 5G SA (standalone), not only NSA.
- An NR band supported by the handset, the X-Series hardware, the installed
  daughterboards, and the local authorization.
- A compatible USRP X300/X310 connected over Ethernet and detected by UHD 4.10.0.0.
- Attenuators, cables, and a shielded enclosure as specified in the local safety manifest.
- Handset Wi-Fi disabled during the test.

## SIM and Subscriber

- A programmable SIM configured with an MCC/MNC matching `001/01` or the authorized local PLMN.
- IMSI/SUPI, K/Ki, OPc, AMF, and SQN matching the subscriber in Open5GS.
- Do not store the actual IMSI or keys in shared logs; redact identifiers before reporting.
- Roaming enabled if the lab PLMN does not match the profile expected by the handset.
- The `internet` APN configured on the handset.
- The Open5GS subscriber provisioned before starting RF.
- SUCI/SUPI verified in AMF logs with identifiers redacted.

## Radio

- 5G SA mode available and selected on the handset.
- Manual network selection available for the lab PLMN.
- `DL_ARFCN`, `NR_BAND`, `TX_GAIN`, and `RX_GAIN` populated only with locally authorized values.
- `rf/channel-plan.yaml` created from the example and validated by the operator.
- `rf/safety-manifest.yaml` created from the example with `authorization_confirmed: true`, a finite duration, `auto_stop: true`, and an operator note.

## Minimum Logs

- AMF: `SERVICE=amf make logs-5g-x310`.
- gNB: `SERVICE=gnb-x310 make logs-5g-x310` or `deployments/5g-sa-x310/gnb/.runtime/gnb-x310.log`.
- Record evidence of NG Setup, Registration Request/Accept, and the PDU session without exposing keys or the full IMSI.

## Safe Workflow

- Prepare the synthetic IMS secret with `./lain5g scenario setup 5g-sa-x310`.
- Run `make check-5g-x310`.
- Run `make preflight-5g-x310`.
- Run `make dry-run-5g-x310`.
- Start the 5GC and IMS infrastructure without RF by running `make start-5g-x310-core`.
- Do not run `make start-5g-x310-rf` until local authorization is in place and `LAIN5G_ALLOW_5G_RF_START=true` is set in the operator's environment.
- Alternatively, run `./lain5g app start --operations --open` and open
  `http://localhost:8080/scenarios/5g-sa-x310`; `5GC + IMS, no RF` does not
  transmit, and `Start core + RF` requires all safeguards.

Retain NG setup and any separately collected, redacted UE-registration and PDU
session evidence under the same `run-id`. When IMS registration, VoNR calls, and
RTP are evaluated, correlate them through a dedicated IMS/media evidence scope.
