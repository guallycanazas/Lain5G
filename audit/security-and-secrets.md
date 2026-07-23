# Lain5G-Lab Security and Secrets Audit

This is a historical audit snapshot of commit
`c3247c99b6c969189efe9e57a46f110c88c26f4d` on 2026-07-22. Words such as
"tracked" and "current" below refer to that snapshot. The release-candidate
branch removed the two key files from the current tree and added runtime key
generation, but the old material remains reachable in Git history. Current
dispositions are recorded in [remediation-report.md](remediation-report.md).

## Handling rule

This report intentionally contains no secret value, subscriber identifier,
private infrastructure address, RF plan value, hardware serial, password,
token, key material, or authorization text. Findings identify only category,
path, approximate location, tracked/ignored state, permissions when observed,
and the required follow-up action.

No finding was remediated during this historical audit because that phase was
read-only except for audit reports.

## Method

The audit used:

- `git ls-files` for the tracked source boundary.
- `git check-ignore -v` for relevant local paths.
- A custom metadata-only regex scanner that emitted paths and line numbers but
  suppressed matched values.
- File mode inspection for selected ignored secret-bearing files.
- Static review of Dockerfiles, Compose, configuration, scripts, and examples.
- Path-scoped Git history review for the tracked private keys.

`gitleaks`, `trufflehog`, and equivalent full history scanners were not
available. The custom scan is not a substitute for a release-grade secret scan.

## Critical findings

| Category | State | Path and location | Risk | Action applied |
| --- | --- | --- | --- | --- |
| Valid private key | Tracked | `images/ims-real-open5gs/roles/udm/curve25519-1.key:1` | Critical: usable private key material is public in Git history | None; read-only audit |
| Valid private key | Tracked | `images/ims-real-open5gs/roles/udm/secp256r1-2.key:4` | Critical: usable private key material is public in Git history | None; read-only audit |
| Key inclusion in image | Tracked | `images/ims-real-open5gs/Dockerfile`, COPY section near line 9 | Critical: both keys enter an image layer | None; read-only audit |
| Key runtime reference | Tracked | `images/ims-real-open5gs/roles/udm/udm.yaml`, near lines 19 and 22 | Critical: runtime configuration directly consumes tracked keys | None; read-only audit |

The key paths entered reachable history in commit `911f146`. Even if the files
are removed in a future commit, rotation and an explicit history decision are
still required. Their apparent upstream/demo origin does not make publication
of valid private keys acceptable.

## High-risk ignored local findings

| Category | State | Path and location | Mode observed | Required action |
| --- | --- | --- | ---: | --- |
| Subscriber identifiers and SIM cryptographic material | Ignored | `config/real-ims-subscriber.json`, fields near lines 2-7 | `0600` | Keep outside repository; use managed secret storage and retention policy |
| SIM material and IMS password | Ignored | `deployments/4g-volte/common/.env`, near lines 6-11 and 24 | `0664` | Restrict to `0600`; rotate if copied; stop backup duplication |
| Simulation subscriber material | Ignored | `deployments/5g-sa/.env`, subscriber section | `0664` | Restrict to `0600`; label test-only data |
| IMS password and subscriber values | Ignored | `deployments/5g-vonr/.env`, subscriber/IMS section | `0600` | Keep owner-only; ensure values are synthetic |
| SDR environment and device settings | Ignored | `deployments/5g-sa-x310/.env` | `0664` | Restrict to `0600`; separate hardware-private overlay |
| SDR environment and device settings | Ignored | `deployments/5g-nsa-x310/.env` | `0664` | Restrict to `0600`; separate hardware-private overlay |
| Generated provisioning token | Ignored | `deployments/ims-real/.runtime/4g/provisioning.key` | `0600` | Rotate per runtime and expire after use |
| Generated provisioning token | Ignored | `deployments/ims-real/.runtime/5g/provisioning.key` | `0600` | Rotate per runtime and expire after use |
| Duplicate runtime tokens | Ignored | `deployments/ims-real/.runtime/*/pyhss/config.yaml`, near token setting | `0600` in inspected runtime | Reference a secret file rather than duplicate the token |
| Secret-bearing backups | Ignored | `.backups/config/**` | Predominantly broader than owner-only | Encrypt or remove; enforce `0600`/`0700` and retention |
| Operational RF plans/manifests | Ignored | X-Series `rf/*.yaml` excluding examples | Broader than owner-only in inspected files | Restrict, expire, and prohibit sensitive free-form notes |
| Run logs with hardware and subscriber metadata | Ignored | `runs/run-*/logs/**`, `preflight.json` | Predominantly broader than owner-only | Redact at collection, restrict permissions, enforce retention |

Git ignore prevents accidental normal staging of these exact paths, but it does
not provide access control, encryption, redaction, or deletion.

## Tracked subscriber and credential-like material

The scanner found static valid-shaped values in simulation, test, and example
contexts. No claim is made that these are live credentials, but their role must
be explicit before release.

| Category | Tracked paths | Assessment |
| --- | --- | --- |
| SIM cryptographic test material | `deployments/4g-lte-sim/ran/ue.conf`, `deployments/4g-volte/sim/ran/ue.conf`, `deployments/5g-sa/ueransim/ue.yaml` | Complete public simulation vectors; currently not clearly labeled everywhere |
| Subscriber identifiers | `config/profiles/*.yaml`, simulation UE files, backend/frontend tests | Valid-shaped public defaults/test data; not evidence of a live subscriber |
| Real IMS example schema | `config/real-ims-subscriber.example.json` | Uses explicit placeholders and is appropriately non-operational |
| Test subscriber fixtures | `backend/tests/**`, `frontend/tests/**` | Synthetic repeated values; redaction scope should be documented |
| Static database URL credentials | Imported Kamailio role configs under `images/ims-real-kamailio/roles/{icscf,pcscf,scscf}` | Upstream/default credentials embedded in URLs; should be runtime-injected |
| Static database password | `images/pyhss-secure/runtime/config.yaml`, near line 113 | Non-empty default; should be runtime-injected |
| Empty database root password mode | 4G VoLTE simulation, X-Series 4G, and VoNR Compose manifests | Internal-only network does not eliminate the risk |

The tracked scanner reported 11 files with SIM-cryptographic assignment shapes
and 15 files with subscriber-identifier assignment shapes. Most are tests or
simulation defaults. Values were suppressed during scanning and are not
reproduced here.

## Tracked RF and infrastructure exposure

| Category | Tracked paths | Risk |
| --- | --- | --- |
| Operational-looking RF profiles | `config/profiles/4g-lte-x310.yaml`, `config/profiles/5g-sa-x310.yaml`, `config/profiles/5g-nsa-x310.yaml` | Publish hardware/network and RF defaults rather than neutral examples |
| Populated SDR RAN settings | `deployments/4g-volte/x310/ran/enb.conf`, `deployments/5g-nsa-x310/ran/enb.conf` | May disclose an executable laboratory configuration |
| Populated NSA channel example | `deployments/5g-nsa-x310/rf/channel-plan.example.yaml` | Despite the example suffix, it represents a complete usable plan |
| Private container topology | Numerous Compose and network-function YAML files | Mostly normal isolated test topology; should be distinguished from physical-lab addressing |

The custom scanner found private-address literals in 114 tracked files and RF
numeric assignments in 15 tracked files. Most are container topology,
simulation, tests, or documentation. The physical-lab subset requires manual
sanitization before a public release.

## `.gitignore` assessment

| Required category | Status | Evidence/gap |
| --- | --- | --- |
| Root `.env` | Covered | `.gitignore:1` |
| Named project/scenario `.env` files | Partially covered | Known files are listed, but generic `.env.*` private variants are not covered |
| Real subscriber file | Covered | `.gitignore:19` |
| RF plans/manifests | Partially covered | Known local files are listed; generic local overlays and one RF marker pattern are incomplete |
| IMS runtime | Covered | `.gitignore:18` |
| Runs | Covered | `.gitignore:31-32` |
| Backups | Covered | `.gitignore:33-34` |
| Python/Node/build artifacts | Covered | `.gitignore:23-27,30,35` |
| Local databases | Partially covered | `.db` and `.sqlite` only; dumps, BSON, and other SQLite suffixes are missing |
| Private keys/certificates/SSH material | Not covered | No generic key/certificate patterns |
| Generic credentials/tokens | Not covered | No broader credential filename protection |
| Logs/packet captures outside `runs/` | Not covered | No generic log or capture patterns |
| IDE/editor files | Not covered | No general IDE/editor section |

Docker context exclusions are also incomplete. Backend and frontend have narrow
`.dockerignore` files, while image build contexts generally have none. The
real-IMS Open5GS image currently copies tracked keys into its build context.

## History and negative findings

| Check | Result |
| --- | --- |
| Current tracked private key blocks | Two files found |
| SSH private/public key material | No finding in current project tree |
| Cloud/Git hosting/provider token shapes | No finding in inspected tree/history |
| JWT-shaped tokens | No finding; generated IMS tokens are separately reported |
| Explicit ICCID literal | No finding in inspected material |
| Tracked real `.env` history | No tracked operational `.env` path found |
| Git remote embedded credentials | No finding |
| Tracked application database files | No finding |

These negative findings are limited by the absence of a dedicated history
scanner and by one unreadable root-owned run metadata file.

## Application security observations

- The web backend has no authentication or authorization.
- The Dockerized backend has the Docker socket and a writable project mount.
- Real-mode operations and image pulls are enabled by default in the app example.
- Loopback port binding reduces network exposure but is not an authorization control.
- Command redaction covers selected authentication fields but not all subscriber
  identifiers, SIP credentials, arbitrary URI credentials, RF values, or notes.
- `LAIN5G_SUBSCRIBER_SECRETS_VISIBLE` is declared but is not consistently used
  as an enforcement boundary in subscriber logic.
- The optional Open5GS WebUI image is unresolved and may expose an additional
  administrative surface when enabled.

## Required security disposition before release

1. Rotate and remove the two tracked private keys, stop copying them into images,
   and decide explicitly how to purge reachable history.
2. Move operational RF values out of tracked profiles/configuration.
3. Restrict secret-bearing ignored files and backups to owner-only access.
4. Replace static database credentials and empty-password modes with runtime secrets.
5. Add generic ignore rules plus pre-commit and CI secret scanning.
6. Add authentication/authorization or document and technically enforce a
   strictly local trusted-operator deployment boundary.
7. Generate public evidence only through an anonymization pipeline.

No item above was applied during this audit phase.
