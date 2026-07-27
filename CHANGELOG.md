# Changelog

All notable changes to Lain5G-Lab are recorded in this file.

## [Unreleased]

### Added

- Integrated web application and direct software-scenario lifecycle commands
  into the `lain5g` CLI, including an explicit software-operations mode that
  keeps RF control disabled.

### Fixed

- Exposed VoLTE and VoNR profiles in the interactive CLI and connected their
  start, status, validation, logs, and stop workflows.

## [1.0.0] - 2026-07-27

### Added

- Root `VERSION` authority for API, frontend, image, and release metadata.
- Offline `make version-check` policy enforcement and focused release tests.
- Reproducibility policy and an evidence-backed dependency/version matrix.
- Hardware-free CI and a unified `make softwarex-check` entry point.
- A schema-validated, sanitized public-result pipeline with passing 4G LTE,
  VoLTE/IMS, and 5G SA summaries plus preserved historical VoNR evidence.
- Validated 5G VoNR software operation with 25/25 passing 5GC, UE, dual-PDU,
  user-plane, IMS-path, and authenticated SIP checks.
- Validated 4G VoLTE software operation with 22/22 passing LTE, EPC, data, IMS,
  DNS, subscriber-provisioning, and authenticated SIP checks.
- English-first release documentation, Spanish overview, citation and community
  policy stubs, legal review, and a partial application dependency SBOM.

### Changed

- Pinned direct Python runtime and development dependencies to the versions
  tested in the release environment, with a complete exact constraints file.
- Switched supported frontend installation commands to `npm ci` while
  preserving `package-lock.json` and its integrity records.
- Pinned source builds to commits resolved from authoritative upstream tags.
- Pinned viable Docker bases and third-party Compose images by verified digest.
- Tagged locally derived Real-IMS images as `1.0.0` and synchronized OCI
  version labels on first-party build definitions.
- Made the base web application observation-only and moved Docker/project
  mutation behind a separate opt-in override and runtime flag.
- Standardized the operator frontend and API-owned catalog/preparation text on
  English, removed the persisted Spanish language option, and fixed the HTML
  document language to `en`.

### Fixed

- Removed empty source commit defaults that allowed tag movement to change a
  build silently.
- Replaced RTPengine's mutable `latest` bootstrap URL with its verified `26.0`
  release channel and added verification of the published keyring checksum.
- Replaced local-file `ADD` with `COPY` in the imported Real-IMS MySQL runtime
  Dockerfile and refreshed its transformation provenance.
- Enforced side-effect-free RF dry-run contracts with regression tests.
- Removed two versioned UDM private keys and generate replacements at runtime
  with owner-only permissions.

### Security

- Kept dependency verification offline by default; the version check neither
  starts services nor accesses hardware, RF, scenario state, or databases.
- Preserved the existing Real-IMS provenance record while identifying each
  release-specific transformation of imported Dockerfiles.
- Restricted the repository-root backend build context to `VERSION` and the
  runtime backend files so local secrets and development artifacts are omitted.
- Added current-tree sensitive-file checks and owner-only defaults for generated
  key material.

### Known Limitations

- Software 4G LTE/VoLTE, 5G SA, and VoNR scenarios were validated. RF hardware,
  commercial-UE behavior, audio quality, and RTP performance remain separate
  experimental scopes.
- Debian and Ubuntu package repositories used inside image builds are not
  snapshot repositories, so `apt-get` package closure remains time-dependent.
- The RTPengine `26.0` repository is a moving release channel, and its observed
  Bookworm package revision differs between amd64 and arm64.
- Published `gually/lain5g-*` catalog images and the locked upstream Real-IMS
  application images currently expose Linux/amd64 manifests only. Source-build
  portability to other architectures is not asserted.
- Python package artifacts are exact-version constrained but do not have a
  generated hash lock; no unverified hashes were added.
- `npm audit --omit=dev` reports no production findings. The full locked tree
  reports five test-tool findings (three moderate, one high, and one critical)
  through Vitest/Vite; npm's available fix requires a Vitest major upgrade.
- The `1.0.0` Real-IMS derived images are local build tags and have not
  been asserted as published registry artifacts.
- Removed private-key paths are absent from the published clean release history;
  material copied from older private clones must still be treated as revoked.
- This is a source-only release. Catalogued project image digests lack a
  verifiable source-to-build mapping and are blocked for binary republication.
- The application SBOM is partial and does not inspect final image filesystems.
- GitHub Private Vulnerability Reporting is enabled. Article-specific ORCIDs,
  corresponding-author details, and declarations remain manuscript metadata.
