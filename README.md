# Lain5G-Lab

[![CI](https://github.com/guallycanazas/Lain5G/actions/workflows/ci.yml/badge.svg)](https://github.com/guallycanazas/Lain5G/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0--rc.1-blue.svg)](VERSION)

[Spanish translation](README.es.md)

Lain5G-Lab is a reproducible environment for deploying, operating, and
validating experimental 4G LTE/EPC/IMS, 5G standalone (SA), and experimental 5G
non-standalone (NSA) scenarios. It combines established open-source network
components with Docker Compose isolation, declarative configuration, a FastAPI
backend, a React interface, and traceable validation records.

Lain5G-Lab does not implement a mobile core or RAN from scratch. Its contribution
is the reproducible integration, orchestration, validation, and traceability of
Open5GS, UERANSIM, srsRAN, Kamailio, pyHSS, UHD, and related components. The
current version is the source-only release candidate [`1.0.0-rc.1`](VERSION).

## Key features

- Isolated Docker Compose scenarios for software and controlled SDR workflows.
- Software-only 4G LTE, 4G IMS registration, and 5G SA examples.
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
make start-5g-sa
make validate-5g-sa
make stop-5g-sa
```

Use only synthetic or laboratory subscriber values. See
[Installation](docs/installation.md) and [5G SA](docs/5g_sa.md) for details.

<a id="canonical-capability-status"></a>

## Scenarios

| Scenario | Purpose | Current status |
| --- | --- | --- |
| `5g-sa-sim` | Open5GS + UERANSIM software 5G SA | Validated in simulation |
| `4g-lte-sim` | Open5GS + srsRAN ZMQ LTE data | Validated in simulation |
| `4g-ims-sim` | Software LTE + laboratory IMS registration | Validated in simulation |
| `5g-vonr-sim` | Software 5G SA + laboratory IMS | Not validated |
| `4g-lte-x310` | LTE with compatible X300/X310 hardware | Partially validated |
| `5g-sa-x310` | 5G SA with compatible X300/X310 hardware | Not validated |
| `5g-nsa-x310` | Experimental LTE + NR EN-DC | Partially validated |
| `ims-real` | Separate Open5GS, pyHSS, and Kamailio package | Partial / dry-run dependent |

The status applies only to the stated scope. `5g-sa-sim` uses the `5g-sa`
deployment, and the `4g-ims-sim` public result uses the `4g-volte-sim`
operational profile. See [Validation](docs/validation.md) and
[Public results](results/public/README.md) for evidence and exact boundaries.

## Testing

```bash
make test
make verify
make softwarex-check
```

The current release candidate passes 262 backend tests with 77% backend line
coverage and 42 frontend tests. TypeScript checking, the frontend production
build, Compose validation, profile validation, metadata checks, and sensitive
file checks also pass locally. These software checks do not validate RF or
commercial-UE operation.

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
- A complete VoLTE call and bidirectional RTP have not been demonstrated.
- VoNR, commercial-UE 5G SA registration and data, and a stable NR user plane
  have not been validated.
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
[SUPPORT.md](SUPPORT.md) and [SECURITY.md](SECURITY.md).
