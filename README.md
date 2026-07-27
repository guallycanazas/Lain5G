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
> workflows pass their complete validation suites: 4G LTE (14/14), 4G
> VoLTE/IMS (22/22), 5G SA (15/15), and 5G VoNR/IMS (25/25). The repository-wide
> `make softwarex-check` also passes 280 backend tests, 48 frontend tests, the
> production build, source and Compose verification, release metadata checks,
> and sensitive-file controls.

## Key features

- Isolated Docker Compose scenarios for software and controlled SDR workflows.
- Validated software-only 4G LTE/VoLTE and 5G SA/VoNR signaling networks.
- LTE/5G registration, user-plane, IMS, DNS, and authenticated SIP validation.
- Declarative profiles with local, ignored files for operational values.
- FastAPI and React tools for local observation and guarded operations.
- Scenario validators and sanitized public result records.
- RF safeguards with explicit authorization, finite duration, and emergency stop.

## Quick start

Requirements: GNU/Linux x86_64, Docker Engine, Docker Compose v2, Git, GNU Make,
SCTP support, and `/dev/net/tun`.

This example runs Open5GS and UERANSIM entirely in software and does not use RF:

```bash
git clone https://github.com/guallycanazas/Lain5G.git
cd Lain5G

cp deployments/5g-sa/.env.example deployments/5g-sa/.env
# Add laboratory-only subscriber values to the ignored local .env file.

./lain5g images pull 5g-sa
./lain5g scenario start 5g-sa
./lain5g scenario validate 5g-sa
./lain5g scenario stop 5g-sa
```

Run `./lain5g` without arguments for the interactive console. It checks the
host, downloads images, configures profiles,
starts/validates/stops scenarios, and manages the web application. It can also
start the operational app directly, enabling software image downloads and
scenario control while keeping RF disabled:

```bash
./lain5g app start --operations --open
```

Use `./lain5g profile wizard 5g-sa` for guided profile configuration. Start the
safe observation-only app with
`./lain5g app start --open`.

Use only synthetic or laboratory subscriber values. See
[Installation](docs/installation.md) and [5G SA](docs/5g_sa.md) for details.

<a id="canonical-capability-status"></a>

## Validated software networks

| Scenario | Purpose | Validation |
| --- | --- | --- |
| `4g-lte-sim` | Open5GS EPC + srsRAN ZMQ LTE data | **PASS (14/14)** |
| `4g-volte-sim` | 4G LTE + EPC + IMS/VoLTE signaling | **PASS (22/22)** |
| `5g-sa-sim` | Open5GS 5GC + UERANSIM 5G SA data | **PASS (15/15)** |
| `5g-vonr-sim` | 5G SA + dual PDU sessions + IMS/VoNR signaling | **PASS (25/25)** |

The public `4g-ims-sim` result corresponds to the `4g-volte-sim` operational
profile and validates LTE, EPC, IMS, and authenticated SIP registration. The
latest `5g-vonr-sim` operational validation covers the 5GC, NG setup, UE
registration, internet and IMS PDU sessions, both UE tunnels, data connectivity,
IMS DNS, P-CSCF reachability, and authenticated SIP registration. See
[Validation](docs/validation.md) and [Public results](results/public/README.md)
for the evidence model.

### Guarded hardware and experimental profiles

| Profile | Purpose | Availability |
| --- | --- | --- |
| `4g-lte-x310` | 4G EPC/IMS with a compatible X300/X310 eNB | Core and IMS functional; RF requires authorized hardware |
| `5g-sa-x310` | 5G SA with a compatible X300/X310 gNB | Guarded RF workflow available; hardware-dependent |
| `5g-nsa-x310` | Experimental LTE + NR EN-DC | Guarded experimental profile available |
| `ims-real` | Separate Open5GS, pyHSS, and Kamailio runtime | Operational package; environment-dependent |

## Reproducibility and testing

```bash
make test
make verify
make softwarex-check
```

`make softwarex-check` is the single release-verification command used by CI. It
passes 280 backend tests with 77% line coverage and 48 frontend tests, followed
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
- The validated VoLTE and VoNR scope covers network registration, data sessions,
  IMS reachability, and authenticated SIP signaling. Audio quality, RTP media
  performance, commercial-UE behavior, and RF results are separate experiments.
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
