# VoLTE Validation

The current status is defined in the
[canonical capability table](../README.md#canonical-capability-status): the
software VoLTE network and signaling are validated.

The [public 4G IMS result](../results/public/4g-ims-sim/run-20260723-055149.json)
for source commit `12c4a38404bbaf240c698a056e3f47182081ab5c` records
22/22 `PASS` checks and is classified as `SIMULATION_ONLY`. It covers LTE,
EPC, bearer/APN, data, IMS, DNS, and authenticated SIP Digest registration. The
artifact was added by publication commit
`060e669d3f65e1844a702b1b5264be6933ef45c2`.

## Validated VoLTE Evidence

The validation retains evidence of:

- UE LTE registration.
- Data bearer and provisioned `ims` APN.
- Successful `SIP REGISTER`.
- EPC, IMS, eNB, and UE logs associated with the same `run-id`.

The `INVITE`/`ACK`/`BYE` dialog, bidirectional RTP, and audio metrics are
evaluated in a separate media test when that scope is required.

## SIP REGISTER

To declare `sip_register PASS`, the validation requires actual evidence of:

- Initial REGISTER from the SIP client.
- `401 Unauthorized` challenge or equivalent.
- Authenticated REGISTER.
- Final `200 OK` response.
- Correlated SIP client, P-CSCF, I-CSCF, and S-CSCF logs.

Finding only the word `REGISTER` in logs is not sufficient.

## Validation States

- `PASS`: evidence found.
- `FAIL`: required evidence is missing or a critical service is down.
- `WARNING`: partial or inconclusive evidence.
- `NOT_TESTED`: the test does not apply or was not run.

## Outputs

Validations write JSON to `runs/<run-id>/`. These files are private operational
evidence, do not replace a complete SIP/RTP capture, and do not become public
evidence without anonymization, an exact commit, and verifiable correlation.
