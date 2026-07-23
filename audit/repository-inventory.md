# Lain5G-Lab Repository Inventory

This inventory is a historical snapshot of commit
`c3247c99b6c969189efe9e57a46f110c88c26f4d` on 2026-07-22. Counts, missing-file
statements, branch names, and words such as "current" below describe that
snapshot, not the release-candidate branch. See
[remediation-report.md](remediation-report.md) for current dispositions.

## Audit scope

This was a read-only technical inventory of the repository state observed on
2026-07-22. No source, configuration, runtime, RF, firmware, database, or
container state was changed. The six files under `audit/` are the only files
created by this audit.

| Item | Observed value |
| --- | --- |
| Repository | `guallycanazas/Lain5g-lab` |
| Working directory | `/home/gually/Lain5G-Lab` |
| Branch | `main` |
| Audited `HEAD` | `c3247c99b6c969189efe9e57a46f110c88c26f4d` |
| Last commit | `docs: record final lab validation status` |
| Upstream | `origin/main` |
| Ahead/behind before audit | `+0/-0` |
| Remote | `git@github.com:guallycanazas/Lain5g-lab.git` |
| Submodules | None |
| Untracked files before audit | None |
| Pre-existing tracked change | `README.md`, 4 insertions and 4 deletions |

The pre-existing `README.md` change strengthens the 5G NSA conclusion relative
to `HEAD`. It was not created, changed, staged, or reverted by this audit. The
scientific claim review covers both committed `HEAD` and that working-tree text.

## Tags

The following tags exist locally:

| Tag | Release role |
| --- | --- |
| `v0.3.0-dockerized-ui` | Historical pre-1.0 tag |
| `v0.4.0-subscribers` | Historical pre-1.0 tag |
| `v0.5.0-volte-signaling` | Historical pre-1.0 tag |
| `v0.6.0-vonr-signaling` | Historical pre-1.0 tag |
| `v0.7.0-multi-scenario-app` | Latest local tag |

There is no `v1.0.0` tag.

## Repository size

Sizes are working-tree disk usage and include ignored local state.

| Path | Approximate size | Interpretation |
| --- | ---: | --- |
| Repository total | 6.3 GB | Source plus local dependencies and evidence |
| `runs/` | 6.0 GB | Ignored operational and experimental evidence |
| `frontend/` | 180 MB | Source, `node_modules`, and build output |
| `.venv/` | 69 MB | Ignored Python environment |
| `.git/` | 6.5 MB | Git database and loose objects |
| `deployments/` | 1.9 MB | Scenario source plus small ignored runtime files |
| `backend/` | 1.9 MB | Application, tests, and caches |
| `images/` | 980 KB | Docker build contexts and imported configuration |
| `.backups/` | 192 KB | Ignored local configuration backups |
| `docs/` | 92 KB | Versioned documentation |

Git reports 512 tracked files, no ordinary untracked files, and 14,424 ignored
file entries. The repository has no tracked binary archives, packet captures,
images, PDFs, shared objects, executables, or Git LFS pointers.

## Complete logical tree

The exact tracked manifest was inspected with `git ls-files`. The tree below
records every logical source area and its tracked-file count. Generated and
ignored subtrees are recorded separately.

```text
Lain5G-Lab/                         512 tracked files
|-- .backups/                         1 (.gitkeep only)
|-- backend/                         80
|   |-- app/
|   |   |-- api/                     FastAPI route modules
|   |   |-- models/                  Pydantic API/domain models
|   |   `-- services/                orchestration and validation services
|   |-- tests/                       21 test modules plus fixtures
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- requirements-dev.txt
|-- config/                           8
|   |-- profiles/                     7 declarative scenario profiles
|   `-- real-ims-subscriber.example.json
|-- deployments/                    168
|   |-- 4g-lte-sim/                  18
|   |-- 4g-volte/                    62
|   |   |-- common/
|   |   |-- sim/
|   |   `-- x310/
|   |-- 5g-nsa-x310/                 16
|   |-- 5g-sa/                       19
|   |-- 5g-sa-x310/                  17
|   |-- 5g-vonr/                     29
|   `-- ims-real/                     7
|-- docs/                            21
|-- frontend/                        98
|   |-- src/
|   |   |-- components/
|   |   |-- hooks/
|   |   |-- pages/
|   |   |-- services/
|   |   |-- types/
|   |   `-- utils/
|   |-- tests/                       11 test modules plus support files
|   |-- Dockerfile
|   |-- package.json
|   `-- package-lock.json
|-- images/                         125
|   |-- ims-dns/                      1
|   |-- ims-real-dns/                 8
|   |-- ims-real-kamailio/           38
|   |-- ims-real-mysql/               3
|   |-- ims-real-open5gs/            48
|   |-- ims-real-rtpengine/           3
|   |-- ims-sip/                      3
|   |-- kamailio/                     1
|   |-- open5gs/                      2
|   |-- pyhss-secure/                 7
|   |-- srsran4g-sim/                 2
|   |-- srsran4g-uhd/                 3
|   |-- srsranproject-uhd/            4
|   `-- ueransim/                     2
|-- runs/                             1 (.gitkeep only)
|-- scripts/                          1 (real IMS CLI)
|-- .env.app.example
|-- .env.example
|-- .gitignore
|-- LICENSE
|-- Makefile
|-- README.md
|-- THIRD_PARTY_NOTICES.md
|-- docker-compose.app.yml
`-- lain5g
```

Tracked file types at audit start:

| Type | Count |
| --- | ---: |
| Python modules | 63 |
| Python CLI without `.py` suffix | 1 |
| TypeScript | 31 |
| TSX | 57 |
| Shell | 97 |
| YAML/YML | 87 |
| JSON | 14 |
| Dockerfiles | 20 |
| Markdown | 32 |
| Compose manifests | 10 |

## Root and documentation inventory

Root operational files are `README.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`,
`Makefile`, `lain5g`, `docker-compose.app.yml`, `.gitignore`, `.env.example`, and
`.env.app.example`.

Versioned documentation consists of:

- `docs/4g_simulation.md`
- `docs/4g_volte.md`
- `docs/5g_sa.md`
- `docs/5g_vonr.md`
- `docs/5g_x310_cots_ue_checklist.md`
- `docs/architecture.md`
- `docs/backend.md`
- `docs/configuration.md`
- `docs/dockerized_app.md`
- `docs/frontend.md`
- `docs/ims.md`
- `docs/installation.md`
- `docs/real_ims.md`
- `docs/rf_safety.md`
- `docs/subscribers.md`
- `docs/third_party.md`
- `docs/troubleshooting.md`
- `docs/validation.md`
- `docs/versions.md`
- `docs/volte_validation.md`
- `docs/x310_lte.md`

No `.github/` tree, continuous-integration workflow, paper directory, public
results directory, citation metadata, changelog, SBOM, or release metadata is
present.

## Backend

The backend is a FastAPI application under `backend/app`. It exposes health,
deployment, preparation, profile, real IMS, run, subscriber, and validation
routes. The service layer controls command execution, scenario dispatch,
profile generation, image preparation, Open5GS MongoDB access, pyHSS access,
run parsing, and real IMS operation.

Important trust boundaries:

- The application has no authentication or authorization layer.
- The Dockerized backend mounts the repository and Docker socket.
- Subscriber APIs can mutate Open5GS MongoDB when real execution is enabled.
- Profile APIs can update profiles and effective scenario files.
- Preparation APIs can pull and retag images.
- RF control is separately guarded and disabled by default in the app example.

The backend API version in `backend/app/main.py` is `0.1.0`, which is not
consistent with the target project version `1.0.0`.

## Frontend

The frontend is a React and TypeScript single-page application built with Vite
and served by Nginx. It contains pages for scenarios, validation, logs, runs,
metrics, topology, preparation, configuration, real IMS, RF safety, subscriber
management, and settings. API access is through relative routes or
`VITE_API_BASE_URL`.

`frontend/package.json` also declares version `0.1.0`. The production container
uses `node:22-alpine` for the build stage and `nginx:1.27-alpine` for runtime;
neither base is digest pinned.

## Compose manifests and scenarios

| Manifest | Purpose |
| --- | --- |
| `docker-compose.app.yml` | FastAPI plus React/Nginx application |
| `deployments/5g-sa/docker-compose.yml` | Open5GS plus UERANSIM 5G SA simulation |
| `deployments/4g-lte-sim/docker-compose.yml` | Open5GS EPC plus srsRAN ZMQ LTE simulation |
| `deployments/4g-volte/sim/docker-compose.yml` | LTE simulation plus laboratory IMS signaling |
| `deployments/4g-volte/x310/docker-compose.yml` | LTE/IMS core plus guarded SDR eNB profile |
| `deployments/5g-sa-x310/docker-compose.yml` | 5GC plus guarded SDR gNB profile |
| `deployments/5g-nsa-x310/docker-compose.yml` | Experimental guarded EN-DC RF access |
| `deployments/5g-vonr/docker-compose.yml` | 5G SA simulation plus IMS signaling |
| `deployments/ims-real/compose.4g.yaml` | Standalone 4G core and real IMS package |
| `deployments/ims-real/compose.5g.yaml` | Standalone 5G core and real IMS package, without RAN |

The RF services are in explicit Compose profiles and use finite timeout logic.
No RF service was started by this audit. Existing RF containers were observed
in an exited state; app and non-RF core/IMS containers pre-dated the audit.

## Scripts and tests

There are 97 tracked shell files. Scenario operation scripts provide variants
of start, stop, restart, status, logs, validate, static test, preflight,
hardware check, and emergency stop. Image runtime scripts initialize or run
Open5GS, Kamailio, pyHSS, DNS, MySQL, RTPengine, UERANSIM, srsRAN, or UHD.

The test suites are:

- Backend: 21 modules, 149 collected pytest cases.
- Frontend: 11 test modules, 42 Vitest cases.
- Static scenario subset: 34 pytest cases within the backend suite.
- Root `tests/`: empty and untracked; project tests live under backend/frontend.

## First-party and upstream code

Project-owned integration code includes the backend, frontend, CLI programs,
Makefile, orchestration and validation scripts, scenario composition, central
profile handling, small SIP laboratory utilities, and project documentation.

Upstream source is normally downloaded during image builds rather than stored
as source in this repository. A notable exception is imported real-IMS
configuration under the `images/ims-real-*` and `images/pyhss-secure/runtime`
trees. `deployments/ims-real/config-provenance.json` records 100 imported files,
their hashes, and upstream commit
`3685b58aa0c7c28b2fecc6b9533f128285bf8dda`. The corresponding BSD-2-Clause
text is retained in `deployments/ims-real/UPSTREAM-BSD-2-CLAUSE.txt`.

No Git submodule is used. No compiled binary is tracked. Generated tracked
artifacts are limited to lock/provenance data, test fixtures, XSD text, and a
source patch. Ignored generated artifacts include caches, bytecode,
`node_modules`, frontend build output, coverage data, runtime configuration,
and run evidence.

## Dependency and version inventory

| Component | Detected version/reference | Reproducibility state |
| --- | --- | --- |
| Open5GS | `v2.7.5` | Tag set; commit argument empty |
| UERANSIM | `v3.2.6` | Tag set; commit argument empty |
| srsRAN 4G | `release_23_11` | Tag set; commit argument empty |
| srsRAN Project | `release_24_10_1`, commit `ef4b0749a12a3b1a8347ae01c937a621603b4069` | Commit pinned |
| UHD | `v4.10.0.0` | Tag set; commit not pinned |
| Kamailio | `5.8.8` | Tag set; commit not pinned |
| CoreDNS | `1.11.3` | Version tag, no digest |
| MongoDB | `7.0` in standard scenarios | Mutable tag |
| MariaDB | `11` | Mutable tag |
| Backend Python image | `python:3.12-slim` | Mutable tag |
| Frontend Node image | `node:22-alpine` | Mutable tag |
| Frontend Nginx image | `nginx:1.27-alpine` | Mutable tag |
| Python dependencies | Nine direct runtime/dev names | Entirely unpinned; no lockfile |
| npm dependencies | Exact transitive lock in lockfile v3 | Direct declarations use ranges |
| Real IMS bases | Seven base images | Digest pinned in `images.lock.yaml` |
| Real IMS derived images | Six local version tags | Not digest pinned after build |

The standard image catalog maps eight local tags to versioned `gually/*` tags,
but the references are not immutable digests. A mutable `latest` repository URL
is used while installing the RTPengine repository keyring.

Locked direct frontend versions include React `19.2.7`, React DOM `19.2.7`,
React Router `7.18.1`, Vite `6.4.3`, TypeScript `5.9.3`, and Vitest `2.1.9`.
`package-lock.json` is present with integrity hashes.

## Licensing inventory

Present legal/provenance files:

- `LICENSE`: MIT for first-party project code.
- `THIRD_PARTY_NOTICES.md`: partial dependency notice.
- `deployments/ims-real/UPSTREAM-BSD-2-CLAUSE.txt`: imported configuration license.
- `deployments/ims-real/config-provenance.json`: imported file provenance and hashes.

Missing or incomplete items:

- `Licence.txt` is absent.
- Dependency licenses are incomplete for Python, npm, images, and build tools.
- No SBOM exists.
- Open5GS license wording is inconsistent between one OCI label and the notice.
- Provenance is incomplete for non-real-IMS configuration templates and the UHD patch.
- Two valid private keys from imported content are tracked and included in an image.

## Relevant ignored/local files

The following categories exist and are ignored:

| Category | Relevant paths | Audit interpretation |
| --- | --- | --- |
| Subscriber secrets | `config/real-ims-subscriber.json` | Real-looking local credentials; owner-only |
| Environment files | Scenario `.env` files and `.env.app` | Some contain sensitive values |
| RF operation | Local channel plans, safety manifests, runtime directories | Private operational material |
| IMS runtime | `deployments/ims-real/.runtime/` | Generated topology, keys, and tokens |
| Runs | `runs/run-*` | Approximately 6 GB; private evidence and logs |
| Backups | `.backups/config/` | Copies include sensitive configuration |
| Dependencies/builds | `.venv/`, `frontend/node_modules/`, `frontend/dist/` | Generated local state |
| Caches | pytest caches, bytecode, coverage, TypeScript build state | Generated local state |

Ignored evidence inventory at audit time:

| Artifact | Count |
| --- | ---: |
| `metadata.json` | 130 |
| `validation.json` | 55 |
| `preflight.json` | 84 |
| `metrics.json` | 45 |
| Log files | 389 |

One run metadata file is owned by `root`, mode `0600`, and was not readable by
the audit user. This is an explicit evidence audit gap.

## Inventory conclusion

The repository is a substantial orchestration and validation layer around
upstream mobile-network components. It has broad scenario and test coverage,
but its scientific release structure, immutable dependency control, public
evidence package, security posture, and release metadata are incomplete. This
inventory does not declare release readiness.
