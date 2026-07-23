# Lain5G-Lab Scenario and Scientific Claim Status

This document is a historical audit snapshot of commit
`c3247c99b6c969189efe9e57a46f110c88c26f4d` on 2026-07-22. Its local runs and
runtime observations are private evidence, not current candidate-commit or
public evidence. The repository maintains one current capability matrix only:
the [canonical capability table](../README.md#canonical-capability-status).

Post-audit note: sanitized software-scenario results now evaluate source commit
`12c4a38404bbaf240c698a056e3f47182081ab5c` and were initially versioned by
artifact publication commit `060e669d3f65e1844a702b1b5264be6933ef45c2`.
The current candidate later corrects the VoNR completion outcome without a
rerun. These artifacts postdate this snapshot. The historical inventory and
findings below have not been rewritten as current results.

## Classification rules

| Classification | Audit meaning |
| --- | --- |
| `VALIDATED` | Reproducible evidence supports the capability with adequate provenance |
| `PARTIALLY_VALIDATED` | Some required evidence exists, but important criteria or provenance are missing |
| `NOT_VALIDATED` | The required outcome is not demonstrated |
| `SIMULATION_ONLY` | Demonstrated only with software UE/RAN or synthetic signaling |
| `DRY_RUN_ONLY` | Only source, static, Compose, preflight, or non-executing plan evidence exists |

Container health, a passing preflight, static tests, or a single signaling
marker are not treated as end-to-end scientific validation.

## Canonical classifications

The evidence inventory below is the basis of the audit decisions, but this
snapshot does not maintain a second scenario matrix. Use the
[canonical capability table](../README.md#canonical-capability-status) for
current classifications and retain the provenance limitations recorded here.

## Evidence inventory

### 5G SA software

Strongest preserved runs:

| Run | Commit | Status | Validation |
| --- | --- | --- | --- |
| `run-20260716-141148` | `d624d07` | stopped | 15 `PASS`, 0 `FAIL` |
| `run-20260710-021716` | `45e1434` | stopped | 15 `PASS`, 0 `FAIL` |

Both commits are ancestors of audited `HEAD`. Since the later run, these files
changed:

- `deployments/5g-sa/open5gs/amf.yaml`
- `deployments/5g-sa/scripts/start.sh`
- `deployments/5g-sa/scripts/stop.sh`

Therefore the result demonstrates the scenario lineage, but not the exact
audited source tree or any later candidate.

### 4G LTE simulation

`run-20260716-130523` has 14 `PASS` checks. It covers all criteria claimed for
the software LTE path, including data ping. Its metadata records the run as
started and omits the Git commit, so it is not publication-grade provenance.

### 4G IMS simulation

`run-20260710-105048` has 22 `PASS` checks. The versioned validation script and
logs support initial REGISTER, challenge, authenticated REGISTER, final
success, and traversal through the laboratory IMS services. This is synthetic
laboratory IMS signaling and is not proof of real AKA/Cx/Rx or a VoLTE call.

### 5G VoNR simulation

All-pass runs are:

| Run | Checks | Recorded commit |
| --- | ---: | --- |
| `run-20260710-133622` | 25 | `1b0bbab` |
| `run-20260710-140222` | 25 | Missing |
| `run-20260710-141028` | 25 | Missing |

Commit `1b0bbab` is not an ancestor of audited `HEAD`, and the versioned VoNR
Compose file did not exist at that recorded commit. The runtime result cannot
be tied reliably to the versioned implementation.

### Commercial UE LTE/IMS

`run-20260721-174218` is identified as a non-dry-run `4g-lte-x310` execution and
has a 15/15 preflight. Its eNB log has markers consistent with S1 setup, RRC
completion, context/bearer setup, and a connected user. It has no Git commit,
terminal status, formal validation, metrics, or correlated data-plane record.

The real-IMS 4G stack running at audit time was inspected without mutation. Its
audit-time status was:

| Check | Status |
| --- | --- |
| Services | `PASS` |
| pyHSS API | `PASS` |
| P/I/S-CSCF listeners | `PASS` |
| Diameter Cx | `PASS` |
| Diameter Rx | `PASS` |
| Authenticated registration, recent log window | `WARNING` |

A metadata-only scan of the full container log history found all parser markers
for REGISTER, challenge, authorization, Cx, and registration success. It also
found SUBSCRIBE, NOTIFY, and INVITE markers, but not MESSAGE. These observations
are not stored as a versioned, anonymized, time-correlated result and therefore
remain partial evidence.

### 5G NSA

Relevant local logs include:

- `runs/run-20260715-231642/logs/enb-nsa-x310.log`
- `runs/run-20260721-004018/logs/enb-nsa-x310.log`
- `runs/run-20260721-164408/logs/enb-nsa-x310.log`
- `deployments/5g-nsa-x310/ran/.runtime/enb_report.json`

The logs support S1 and EN-DC-related control-plane observations, RRC
reconfiguration, connected-user state, and instability. The runtime report has
a `.json` suffix but is not valid JSON and contains sensitive protocol output.

All examined NSA evidence lacks normal `metadata.json`, `validation.json`, and
`metrics.json`. No common run proves dual-chain readiness, LTE attachment,
secondary NR activation, and stable NR user-plane traffic at one Git revision.

## Historical README assertion audit

This section records the assertions encountered during the audit. It is not a
current capability matrix.

| README assertion | Audit status | Finding |
| --- | --- | --- |
| LTE B7 S1 connection | Verified observation | Versioned scenario and local SDR logs support S1 |
| Commercial UE attach | Partial | RRC/context/connected-user markers exist, but no correlated formal validation |
| Active LTE data bearer | Partial | Bearer-related markers exist; no durable ping/throughput evidence in the same traceable run |
| Internet and IMS bearers | Partial | Configuration and local logs support the path; publication-grade correlated evidence is absent |
| Rx authorization | Partial | Audit-time IMS status reported Rx established; result was not archived with commit provenance |
| AKA/Cx authenticated registration | Partial | Full live log history satisfies parser markers; recent status is `WARNING`; no immutable result bundle |
| SUBSCRIBE, NOTIFY, MESSAGE, and INVITE after registration | Not verified as stated | SUBSCRIBE, NOTIFY, and INVITE markers were found; MESSAGE was not found; no correlated public artifact exists |
| Complete VoLTE call | Correctly disclaimed | No complete SIP dialog or bidirectional RTP evidence |
| 5G SA software registration/session/ping | Verified as simulation | Strong 15/15 runs exist, with current-source drift noted |
| 5G NSA connected UE and EN-DC reconfiguration | Partial | Control-plane markers exist; secondary NR user-plane activation and stability are unproven |
| 149 backend tests | Verified for audited commit | Audit execution at `c3247c99b6c9`: 149 passed |
| 42 frontend tests | Verified for audited commit | Audit execution at `c3247c99b6c9`: 42 passed |
| Frontend production build | Verified for audited commit | Audit build at `c3247c99b6c9` succeeded |

At audit time, the committed README at audited `HEAD` was more conservative
about NSA secondary-cell activation than the pre-existing working-tree edit.
That wording was not publication-ready without one correlated, anonymized,
commit-linked NSA result.

## VoLTE call criteria

The audit explicitly checked the available local IMS logs for the required
call sequence. Results:

| Criterion | Result |
| --- | --- |
| Authenticated registration markers | Present in full local history, not archived |
| INVITE request | Present |
| Provisional 180/183 response | Not found |
| Correlated final 200 for INVITE | Not found |
| ACK | Not found |
| BYE/termination | Not found |
| Bidirectional RTP metric/equivalent | Not found |
| Common run ID and Git revision | Missing |
| Anonymized public artifact | Missing |

The end-to-end VoLTE call limitation must remain.

## Evidence quality limitations

- Only 14 of the parseable metadata records contain a Git commit.
- X310 metadata generally lacks commit and terminal status.
- NSA log directories do not use the normal run metadata schema.
- One root-owned metadata file was not readable by the audit user.
- Most evidence is ignored and may contain private identifiers, addresses,
  hardware serials, RF parameters, or operational details.
- Existing evidence has not been processed into a public anonymized dataset.
- Docker logs observed at audit time are mutable operational state, not archival evidence.

## Scenario conclusion

At the audited commit, software-only 5G SA, LTE, and laboratory IMS signaling
had historical demonstrations. SDR LTE/IMS and NSA had meaningful but
incomplete private observations. End-to-end VoLTE, commercial-UE 5G SA, stable
NR user plane, and real-radio VoNR were not validated. This is a historical
audit conclusion, not current candidate evidence or a release-readiness
statement.
