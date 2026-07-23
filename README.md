# Lain5G-Lab

[Leer en español](README.es.md)

Lain5G-Lab is a reproducible research environment for assembling, operating,
and evaluating laboratory 4G LTE/EPC/IMS, 5G standalone (SA), and experimental
5G non-standalone (NSA) scenarios. It integrates established upstream projects
with scenario isolation, declarative configuration, operational safeguards,
validation records, and a FastAPI/React interface.

## Release state

The repository version is **`1.0.0-rc.1`**, as defined in [VERSION](VERSION).
This is a release candidate, and [CHANGELOG.md](CHANGELOG.md) still marks it as
unreleased. It is not a final release, a production mobile network, a 3GPP
reference implementation, a conformance result, or a SoftwareX publication.

The release-candidate artifacts support narrowly stated software-validator
summaries. They are not independently reviewable protocol traces. Hardware and
commercial-UE observations remain non-public and partial, and several radio and
voice outcomes remain unvalidated. The
[canonical capability status](#canonical-capability-status) is the sole current
classification table for the repository.

This is a **source-only candidate**. The legal and SBOM review does not approve
publication or republication of project container images; see
[Redistribution Status](docs/legal/redistribution-status.md).

## Scientific problem and contribution

Reproducing a cellular-network experiment requires more than starting a mobile
core. Core, RAN, IMS, subscriber, container-network, host-network, and radio
parameters must remain mutually consistent; the exact software revisions and
execution environment must be recoverable; and operational readiness must not
be confused with an end-to-end scientific result.

Lain5G-Lab addresses this integration problem by providing:

- isolated Docker Compose scenarios for software-only and controlled SDR paths;
- versioned profiles and local, ignored files for sensitive or site-specific
  values;
- common terminal, FastAPI, and React workflows instead of separate deployment
  implementations;
- validation scripts and run records with explicit outcomes and provenance;
- a sanitized public-results boundary for schema-validated summaries; and
- RF controls for explicit authorization, finite duration, auto-stop, logging,
  and emergency stop.

The project contribution is orchestration, integration, configuration,
validation, and traceability. Open5GS, UERANSIM, srsRAN, UHD, Kamailio, pyHSS,
RTPengine, CoreDNS, MongoDB, and MariaDB provide the underlying core, RAN, IMS,
media, DNS, and database functions. Lain5G-Lab does not certify those upstream
projects, implement a core or RAN from first principles, or certify compliance
with 3GPP specifications.

## Canonical capability status

This is the repository's single canonical capability table. Classifications
have deliberately narrow meanings:

- `VALIDATED`: reproducible evidence is adequate for the explicitly stated
  scope, not for adjacent hardware or protocol claims.
- `PARTIALLY_VALIDATED`: relevant observations exist, but criteria, correlation,
  provenance, or public reproducibility are incomplete.
- `NOT_VALIDATED`: the required outcome has not been demonstrated.
- `SIMULATION_ONLY`: the reported result is limited to software UE/RAN or
  synthetic laboratory signalling; it does not imply independent protocol
  evidence.
- `DRY_RUN_ONLY`: evidence is limited to source, static checks, Compose
  rendering, preflight, or a non-executing plan.

Container health, a passing preflight, one signalling marker, or a successful
process exit is not by itself end-to-end validation.

### Evidence provenance

- **Source commit:** all four new public scenario attempts identify
  `12c4a38404bbaf240c698a056e3f47182081ab5c` as the exact source under test.
- **Initial public result artifact commit:** the sanitized JSON results and
  summaries were added by the direct child commit
  `060e669d3f65e1844a702b1b5264be6933ef45c2`. The current candidate corrects
  the blocked VoNR completion outcome and its support-artifact hash without a
  new scenario execution.
- **Public evidence:** files under [results/public](results/public/) are
  sanitized, versioned, schema-conforming validator summaries. They contain no
  raw logs, packet captures, subscriber credentials, private addresses, serial
  numbers, or operational RF settings. Because that material is excluded, the
  summaries are not independently sufficient to reconstruct protocol events.
- **Private evidence:** ignored run directories and mutable operational logs may
  contain sensitive laboratory information. They are observations, not public
  artifacts reproducible by a third party.
- **Historical evidence:** runs or audit observations tied to an ancestor,
  another revision, or no recorded revision establish context only. The
  [2026-07-22 audit](audit/scenario-status.md), including its 149-backend-test
  baseline, is a historical snapshot and is not current candidate evidence.

Local non-RF checks on the candidate worktree report **262 backend tests
passing, 77% backend line coverage, 42 frontend tests passing, and a passing
frontend production build**. Frontend coverage is not configured. These local
checks establish software-test and build status only; no hosted CI result is
claimed.

### Private laboratory observations

One non-public X-Series observation session used two UHD-visible RF chains.
That observation identifies the tested hardware class only; it is not a public,
commit-linked, or release-reproducible result.

- Commercial LTE logs contain markers consistent with S1, RRC, context/bearer
  setup, and a connected UE. A correlated, persisted data-bearer result is
  absent, so complete attach with active data is not claimed.
- Private 4G IMS observations contain markers compatible with `internet` and
  `ims` bearers, Rx, AKA/Cx, authenticated registration, `SUBSCRIBE`, `NOTIFY`,
  and `INVITE`. No `MESSAGE` marker was found or is claimed. The markers are not
  preserved as one anonymized, commit-linked result.
- Private NSA observations include two active RF chains, accepted S1,
  LTE-attach markers, UE-indicated EN-DC capability, completed RRC
  reconfiguration, and connected-user state. They also include DRB1 RLC
  warnings and radio-link-failure events. They do not demonstrate stable NR
  user-plane traffic or performance.

| Scenario or capability | Classification | Strongest available evidence | Conservative boundary |
| --- | --- | --- | --- |
| `5g-sa-sim` with Open5GS and UERANSIM | `SIMULATION_ONLY` | Public [run `run-20260723-054913`](results/public/5g-sa-sim/run-20260723-054913.json): validator summary reports 15/15 checks `PASS` at the source commit above | Reports software UE registration, PDU session, interface/address, and ping checks on one host; no raw correlated protocol evidence, SDR, commercial UE, IMS, voice, or RF claim |
| `4g-lte-sim` | `SIMULATION_ONLY` | Public [run `run-20260723-055025`](results/public/4g-lte-sim/run-20260723-055025.json): validator summary reports 14/14 checks `PASS` at the source commit above | Reports software EPC, S1, software UE registration, default-bearer, interface/address, and ping checks; no raw correlated protocol evidence, IMS, voice, SDR, or commercial UE claim |
| `4g-ims-sim` (`4g-volte-sim` profile) | `SIMULATION_ONLY` | Public [run `run-20260723-055149`](results/public/4g-ims-sim/run-20260723-055149.json): validator summary reports 22/22 checks `PASS` at the source commit above | Reports laboratory Digest SIP registration and LTE software checks; no raw correlated protocol evidence, AKA, Cx, Rx, completed call, bidirectional media, SDR, or commercial UE claim |
| `5g-vonr-sim` | `NOT_VALIDATED` | Public [run `run-20260723-055328`](results/public/5g-vonr-sim/run-20260723-055328.json): `BLOCKED` by timeout, with no scenario criterion assessed | The validator hit its six-minute limit; the artifact records 413 seconds for the full attempt. Running containers and historical private runs do not establish VoNR |
| Commercial-UE LTE on the X-Series path | `PARTIALLY_VALIDATED` | Private S1, RRC, context/bearer, and connected-user markers | Missing one commit-linked, anonymized, correlated run with a persisted data-plane result |
| `ims-real` 4G registration path | `PARTIALLY_VALIDATED` | Private service/Cx/Rx status and historical mutable authentication and registration markers | Missing one public, anonymized, commit-linked result; no complete call or media evidence, and no `MESSAGE` claim |
| `5g-nsa-x310` path | `PARTIALLY_VALIDATED` | Private S1/LTE attach, EN-DC capability, RRC reconfiguration, and connected-user markers, together with RLC/RLF instability | Missing a commit-linked result that demonstrates NR activation and stable, quantified NR traffic |
| `5g-sa-x310` with a commercial UE: registration, PDU session, and data | `NOT_VALIDATED` | Packaging, safeguards, and historical gNB runtime do not establish the UE outcome | Missing correlated successful registration, PDU session, and data connectivity |
| Stable NR user plane | `NOT_VALIDATED` | No stable NR bearer or correlated performance record | Missing declared-duration stability, throughput, latency, and loss evidence |
| `ims-real` 5G mode | `DRY_RUN_ONLY` | Source, Compose, preflight, and non-executing plans | No RAN execution, UE registration, IMS registration, voice dialogue, or media result |
| End-to-end VoLTE call | `NOT_VALIDATED` | One private, uncorrelated `INVITE` marker | Missing a correlated final successful response to that `INVITE`, `ACK`, `BYE`, and bidirectional RTP |
| VoNR over RF | `NOT_VALIDATED` | No real-radio execution artifact | Missing commercial-UE 5G/IMS registration, a complete correlated SIP dialogue, and bidirectional media |

The detailed acceptance criteria and evidence format are defined in
[docs/validation.md](docs/validation.md) and
[docs/volte_validation.md](docs/volte_validation.md). The table above takes
precedence if another document contains stale status wording.

## Architecture

Lain5G-Lab separates control, scenario, and evidence concerns:

- `backend/` provides a local FastAPI control and observation API.
- `frontend/` provides the React operator interface.
- `config/profiles/` defines scenario-level configuration and safety state.
- `deployments/` contains scenario-specific Compose, configuration, and
  operational scripts.
- Docker Compose project names, networks, and volumes isolate scenarios.
- `runs/` stores local operational records and is excluded from Git because it
  may contain sensitive information.
- `results/public/` stores only reviewed, sanitized result summaries.

Open5GS provides EPC/5GC functions; UERANSIM provides the software gNB and UE;
srsRAN 4G provides LTE ZMQ and LTE SDR paths; srsRAN Project provides the 5G SDR
gNB path; UHD provides USRP access; and Kamailio, pyHSS, CoreDNS, RTPengine, and
the selected databases support the IMS packages. See
[docs/architecture.md](docs/architecture.md) for component relationships and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the upstream boundary.

## Scenarios

- `5g-sa` / `5g-sa-sim`: Open5GS plus UERANSIM software 5G SA.
- `4g-lte-sim`: Open5GS EPC plus srsRAN 4G over ZMQ, without IMS.
- `4g-volte-sim`: software LTE plus compact laboratory IMS; its public result is
  named `4g-ims-sim` to describe the measured scope accurately.
- `5g-vonr-sim`: packaged 5G SA plus laboratory IMS; the current public attempt
  is blocked and not validated.
- `4g-lte-x310`: LTE SDR path with RF disabled by default. The historical name
  is retained although compatible profiles can also target an X300.
- `5g-sa-x310`: controlled 5G SA SDR preparation and gNB path.
- `5g-nsa-x310`: experimental LTE B7 plus NR n3 EN-DC path.
- `ims-real`: separate 4G or 5G core/IMS package without a supplied RAN or UE.

Simulation, SDR, and commercial-UE outcomes are distinct experimental scopes.
Evidence from one scope must not be extrapolated to another.

## Requirements

### Software scenarios

- A GNU/Linux x86_64 host with Docker Engine and Docker Compose v2.
- Git, GNU Make, Internet access for the first image pull or build, and
  sufficient disk space for images and volumes.
- Kernel SCTP support and an available `/dev/net/tun` device.
- Python and Node.js/npm only when running the backend, frontend, or development
  checks outside containers.

Exact upstream and package revisions are documented in
[docs/reproducibility/version-matrix.md](docs/reproducibility/version-matrix.md).
The release does not assert equivalent behavior on untested architectures or
with substituted dependency revisions.

### SDR scenarios

SDR work additionally requires an authorized X300/X310-class device, compatible
firmware/FPGA and daughterboards, a dedicated and correctly configured Ethernet
path, host permissions and scheduling appropriate for UHD, and a conducted,
shielded, or formally authorized RF environment. A local safety manifest,
channel plan, finite duration, attenuation plan, and operator authorization are
required before transmission.

## Secure quick start

### Observation-only application default

The base application is observation-only by default. It binds to loopback,
mounts the repository read-only, does not mount the Docker socket, and keeps
mutating operations, image pulls, and web RF control disabled.

```bash
cp .env.app.example .env.app
# Set LAIN5G_PROJECT_ROOT to this repository's absolute host path.
# Keep LAIN5G_MUTATING_OPERATIONS_ENABLED=false.
make app-up
```

Open `http://127.0.0.1:8080`. For the strongest non-operational behavior, also
set `LAIN5G_DRY_RUN=true`. Stop the base application with `make app-down`.

Operational Docker control is an explicit two-part opt-in on a dedicated,
trusted workstation. Set `LAIN5G_MUTATING_OPERATIONS_ENABLED=true` in
`.env.app` **and** apply the operations override:

```bash
docker compose --env-file .env.app \
  -f docker-compose.app.yml \
  -f docker-compose.app-operations.yml \
  up -d --build
```

The override makes the project mount writable and mounts
`/var/run/docker.sock`, which is equivalent to host-root control. The override
alone does not enable mutation routes, and the mutation flag alone does not
provide Docker or project-write access. Neither mechanism authorizes RF. Use
the same two Compose files with `down` to remove the operational stack. See
[Secure Local Deployment](docs/security/local-deployment.md).

### Minimal software example

The following example starts Docker resources but does not use SDR or RF. Use
only non-sensitive laboratory subscriber values in the ignored local `.env`
file.

```bash
cp deployments/5g-sa/.env.example deployments/5g-sa/.env
# Set laboratory-only SUBSCRIBER_KEY and SUBSCRIBER_OPC values locally.
./lain5g images pull 5g-sa
make start-5g-sa
make validate-5g-sa
make stop-5g-sa
```

Do not use subscriber keys, IMSI/MSISDN values, private infrastructure
addresses, or RF plans from a real network. See
[docs/5g_sa.md](docs/5g_sa.md) and
[docs/installation.md](docs/installation.md).

## Validation

Scenario validators report `PASS`, `FAIL`, `WARNING`, or `NOT_TESTED` for
individual checks and write local records under `runs/<run-id>/`. A release
claim additionally requires an exact source revision, command scope,
environment, non-sensitive configuration, success criteria, terminal status,
and correlated evidence. Public summaries must pass the schema and sensitive
content controls documented under [results/public](results/public/).

For an end-to-end voice claim, IMS registration is insufficient. The evidence
must correlate the originating `INVITE` with a final successful response,
`ACK`, termination by `BYE`, and bidirectional RTP. None of the current public
or private evidence satisfies all of these criteria.

The current non-RF software checks can be repeated with:

```bash
make backend-cov
make frontend-test
make frontend-build
```

The recorded 262 backend and 42 frontend passing tests, 77% backend line
coverage, and frontend build do not establish frontend coverage or hosted-CI
status. No RF, hardware, or cellular capability follows from these software
checks.

## Reported and not demonstrated

Within the public evidence scope, the release candidate publishes three passing
software-validator summaries: 5G SA, LTE, and laboratory 4G IMS registration.
They are schema-valid, sanitized reports rather than independently reviewable
protocol evidence. The 5G VoNR simulation attempt is publicly documented as
blocked rather than converted into a positive result.

Private LTE, real-IMS, and NSA observations are useful experimental context but
remain `PARTIALLY_VALIDATED`. They are not public demonstrations. A complete
VoLTE call, commercial-UE 5G SA registration/data, a stable NR user plane,
`ims-real` 5G execution, and RF VoNR have not been demonstrated at their stated
scopes. No latency, throughput, packet-loss, RF-stability, multi-host
reproducibility, or 3GPP-conformance result is claimed.

## Reproducibility

To reproduce or compare an experiment:

1. Record the exact Git revision and release version.
2. Use the locked versions and image digests in the reproducibility documents.
3. Record the host OS, CPU, memory, Docker/Compose versions, NIC/MTU, and, when
   relevant, non-sensitive SDR model/FPGA/daughterboard information.
4. Preserve the command scope, terminal status, sanitized configuration,
   validation JSON, and correlated logs under one run identifier.
5. Publish only reviewed summaries; never publish raw local runs by default.

The public artifacts identify the tested source commit separately from the
artifact publication commit so that adding evidence does not imply a rerun.
Dependency policy is documented in
[docs/reproducibility/dependency-policy.md](docs/reproducibility/dependency-policy.md).

## RF safety

RF paths are disabled by default and are intentionally absent from the quick
start. Do not transmit in licensed spectrum without legal, technical, and
institutional authorization. Prefer conducted or shielded setups with adequate
attenuation; enforce finite duration and auto-stop; keep an emergency-stop path
available; and do not update device firmware or FPGA images automatically.

Application mutation access and Docker-socket access are not RF authorization.
RF execution has additional independent gates and still requires the physical
and regulatory controls above. Follow [docs/rf_safety.md](docs/rf_safety.md) and
the scenario-specific checklist before any hardware work.

## Documentation

- [Installation](docs/installation.md) and
  [configuration](docs/configuration.md)
- [Architecture](docs/architecture.md) and
  [validation](docs/validation.md)
- [4G LTE/IMS](docs/4g_volte.md),
  [real IMS](docs/real_ims.md), and
  [VoLTE criteria](docs/volte_validation.md)
- [5G SA](docs/5g_sa.md), [5G VoNR](docs/5g_vonr.md), and the
  [commercial-UE checklist](docs/5g_x310_cots_ue_checklist.md)
- [Secure local deployment](docs/security/local-deployment.md),
  [threat model](docs/security/threat-model.md), and
  [RF safety](docs/rf_safety.md)
- [Troubleshooting](docs/troubleshooting.md),
  [version matrix](docs/reproducibility/version-matrix.md), and
  [third-party guidance](docs/third_party.md)

## Citation and future SoftwareX article

[CITATION.cff](CITATION.cff) contains release-candidate software metadata only.
It does not advertise a preferred article citation. No article has been
submitted, accepted, or published, and no DOI exists. The collective contributor
label is not a final scientific author list; author names,
affiliations, ORCIDs, order, and corresponding contact remain subject to direct
confirmation as described in [AUTHORS.md](AUTHORS.md).

If an archival software DOI or an article is created later, update the citation
metadata only from the issued record.

## License and third parties

Project-authored code is distributed under the [MIT License](LICENSE). This
license does not relicense integrated upstream software, container contents, or
imported configuration. Each third-party component retains its own license and
redistribution conditions. Review [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
and the documented SBOM limitations before redistribution. This source-only
candidate does not approve binary or container-image publication.

## Support

Support for `1.0.0-rc.1` is community-based and best effort, with no service
level agreement or RF-operational support. Use the process in
[SUPPORT.md](SUPPORT.md), report only reproducible non-sensitive information,
and follow [SECURITY.md](SECURITY.md) for security-sensitive matters. No support
email or institutional help desk is asserted. A private vulnerability-reporting
channel is still a final-release blocker.
