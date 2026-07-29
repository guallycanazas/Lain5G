# Lain5G-Lab

[![CI](https://github.com/guallycanazas/Lain5G/actions/workflows/ci.yml/badge.svg)](https://github.com/guallycanazas/Lain5G/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](VERSION)

[Spanish translation](README.es.md)

Lain5G-Lab is a reproducible environment for deploying, operating, and
validating integrated 4G LTE/VoLTE and 5G SA/VoNR laboratory networks, plus an
experimental 5G non-standalone (NSA) profile. It combines established
open-source network components with Docker Compose isolation, declarative
configuration, a FastAPI backend, a React interface, and traceable validation
records.

Lain5G-Lab does not implement a mobile core or RAN from scratch. Its contribution
is the reproducible integration, orchestration, validation, and traceability of
Open5GS, UERANSIM, srsRAN, Kamailio, pyHSS, UHD, and related components. The
current stable version is the source-only release [`1.0.0`](VERSION).

> **Tested and functional software release.** All supported software-only network
> workflows pass their complete validation suites: 4G LTE (14/14) and 5G SA
> (15/15). The repository-wide
> `make softwarex-check` also passes 314 backend tests, 50 frontend tests, the
> production build, source and Compose verification, release metadata checks,
> and sensitive-file controls.

## Key features

- Isolated Docker Compose scenarios for software and controlled SDR workflows.
- Validated software-only 4G LTE and 5G SA data networks.
- LTE/5G registration, user-plane, tunnel, and connectivity validation.
- Declarative profiles with local, ignored files for operational values.
- FastAPI and React tools for local observation and guarded operations.
- Scenario validators and sanitized public result records.
- RF safeguards with explicit authorization, finite duration, and emergency stop.

## SoftwareX reviewer quick path

The safe review gate requires Git, GNU Make, Python 3.12, Node.js 22, and the
Docker Compose v2 parser. It does not start telecom containers, access SDR
hardware, or transmit RF.

```bash
git clone https://github.com/guallycanazas/Lain5G.git
cd Lain5G
make softwarex-check
```

Expected result: 314 backend tests, 50 frontend tests, 78% backend line
coverage, a production frontend build, safe rendering of every Compose model,
and successful profile, metadata, link, public-result, and secret checks. CI
runs this exact command on Ubuntu 24.04. Reviewed evidence is under
[`results/public/`](results/public/README.md).

## Run the laboratory

Operational requirements: GNU/Linux x86_64, Docker Engine, Docker Compose v2,
Git, GNU Make, util-linux `flock`, SCTP support, and `/dev/net/tun`.

On a clean GNU/Linux machine, run the guided installer first:

```bash
./install.sh
```

It installs missing Python, Python venv support, Git, Make, Docker, Compose, and
util-linux packages using the detected `apt-get`, `dnf`, `pacman`, or `zypper`
manager; enables Docker; prepares private configuration; and downloads every
published component. All system changes are shown before execution. Use
`./install.sh --dry-run` to print the plan without changing the machine.

If requested after installation, run `newgrp docker` before starting the web
application so the current terminal can access the Docker socket.

### Web application

Launch the operational interface:

```bash
./lain5g app start --operations --open
```

In the app, choose software-only 4G LTE or 5G SA, or one of the guarded 4G/5G RF
profiles. **Preparation** downloads missing components, while
**Scenarios** operates the selected network. Simulations create or preserve
private synthetic credentials. RF transmission requires preflight, an authorized
profile, the safety checklist, exact confirmation phrase, finite duration, and
emergency stop. Stop the interface with `./lain5g app stop` after any active RF
session has ended.

### Interactive CLI

```bash
./lain5g
```

The interactive console offers 4G LTE ZMQ, 5G SA UERANSIM, and the guarded 4G/5G
RF profiles. It downloads components and runs the available actions. Starting a simulation
automatically prepares its private synthetic credentials; RF profiles retain all
mandatory safety controls.

The safe observation-only app is available through `./lain5g app start --open`.
Credentials are stored in ignored local files with `0600` permissions; they are
never printed or committed. See [Installation](docs/installation.md),
[software 4G](docs/4g_simulation.md), and [5G SA](docs/5g_sa.md).

<a id="canonical-capability-status"></a>

## Validated software networks

| Scenario | Purpose | Validation |
| --- | --- | --- |
| `4g-lte-sim` | Open5GS EPC + srsRAN ZMQ LTE data | **PASS (14/14)** |
| `5g-sa-sim` | Open5GS 5GC + UERANSIM 5G SA data | **PASS (15/15)** |

Historical end-to-end signaling evidence remains available under `results/public/`,
but those complete signaling scenarios are not part of the public launch catalog. See
[Validation](docs/validation.md) and [Public results](results/public/README.md).

### Guarded hardware profiles

| Profile | Purpose | Availability |
| --- | --- | --- |
| `4g-lte-x310` | 4G LTE plus always-on compact IMS infrastructure with a compatible X300/X310 eNB | Guarded RF workflow with run-scoped evidence capture |
| `5g-sa-x310` | 5G SA plus always-on compact IMS infrastructure with a compatible X300/X310 gNB | Guarded RF workflow with run-scoped evidence capture |

## Reproducibility and testing

```bash
make test
make verify
make softwarex-check
```

`make softwarex-check` is the single release-verification command used by CI. It
passes 314 backend tests with 78% line coverage and 50 frontend tests, followed
by TypeScript checking, the production build, Compose and profile validation,
metadata verification, internal-link checks, public-result verification, and
sensitive-file controls.

## Architecture

- `backend/`: local FastAPI control and observation API.
- `frontend/`: React operator interface.
- `deployments/`: scenario-specific Compose files, configurations, and scripts.
- `config/profiles/`: declarative scenario and safety profiles.
- `results/public/`: reviewed and sanitized result summaries.
- `runs/`: ignored local run records that may contain sensitive information.

See [Architecture](docs/architecture.md) for the complete component model.

## Documentation

- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)
- [Validation](docs/validation.md)
- [Public results](results/public/README.md)
- [Reproducibility](docs/reproducibility/dependency-policy.md)
- [Version matrix](docs/reproducibility/version-matrix.md)
- [RF safety](docs/rf_safety.md)
- [Secure local deployment](docs/security/local-deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

Detailed audit, security, legal, and evidence records remain in `audit/`,
`docs/security/`, `docs/legal/`, and `results/public/` rather than this overview.

## Limitations

- Lain5G-Lab is a research and education environment, not a production network,
  a 3GPP reference implementation, or a conformance platform.
- Software-simulation results must not be extrapolated to SDR or commercial UEs.
- Commercial-UE behavior and RF results require separate authorized experiments.
- Public artifacts are sanitized validator summaries, not raw protocol traces.

## Authors

- **Willian Roy Canazas Rosas**
- **Manuel Ismael Prieto Tito**

Affiliation: **National University of San Agustin of Arequipa**.

## Citation

Citation metadata is available in [CITATION.cff](CITATION.cff). A software DOI
and SoftwareX article citation will be added only after archival publication.
No DOI or published SoftwareX article is currently claimed.

## License

Project-authored code is available under the [MIT License](LICENSE). Integrated
upstream components retain their own licenses and redistribution terms; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Support and security

Use GitHub Issues for reproducible, non-sensitive bugs. Do not publish secrets,
subscriber identifiers, RF plans, tokens, or private logs. See
[SUPPORT.md](SUPPORT.md) for support and sensitive-reporting guidance.
