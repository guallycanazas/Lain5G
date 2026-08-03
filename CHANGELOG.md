# Changelog

All notable changes to OpenLain5G are recorded in this file.

## [Unreleased]

## [1.1.1] - 2026-08-03

### Added

- Added security, contribution, issue-reporting, and pull-request guidance for
  public collaboration.
- Added a documentation index for operators, reviewers, and developers.

### Changed

- Renamed the visible project brand and software metadata from Lain5G-Lab to
  OpenLain5G while preserving existing repository, command, image, and
  configuration identifiers.
- Standardized active technical documentation in English, retaining
  `README.es.md` as the explicit Spanish overview.
- Simplified author, citation, release, and support text to include only current
  project facts and actionable guidance.
- Generalized installation and troubleshooting guidance across supported host
  conditions while labeling concrete addresses as checked-in profile defaults.
- Updated Vitest to `4.1.10`, removing all findings from the locked npm
  dependency audit while preserving the frontend test contract.

### Removed

- Removed superseded pre-release audit reports that contradicted the current
  release, CI, evidence, and metadata state.

## [1.1.0] - 2026-07-30

### Added

- Added a clean-machine installer that provisions required tooling, generates
  private synthetic scenario configuration, and pulls the complete public image
  catalog without compiling images locally.
- Integrated web application and direct software-scenario lifecycle commands
  into the `lain5g` CLI, including an explicit operations mode for software and
  guarded RF workflows.
- Added private local scenario setup with generated synthetic credentials for
  the supported software and guarded RF profiles.
- Added asynchronous component downloads with per-image progress, a confirmed
  download-all action, and download-before-start flows for software and guarded RF.
- Added always-on compact IMS infrastructure to both public X310 profiles,
  with guarded operation and run-scoped evidence capture.
- Made web and interactive CLI starts prepare the selected 4G or 5G software
  environment automatically, without exposing generated credentials.
- Serialized guarded RF starts across profiles and kept emergency-stop access
  available by refusing app shutdown or downgrade during an active RF session.
- Added an evidence-backed scenario panel that distinguishes core readiness,
  RAN setup, UE registration/session, tunnel assignment, and data-plane proof.

### Changed

- Narrowed the public web, preparation, profile, and interactive CLI catalogs to
  4G LTE ZMQ, 5G SA UERANSIM, and the guarded 4G/5G RF profiles. Signaling
  implementations and historical evidence remain internal.
- Reorganized the English and Spanish reviewer path around installation,
  architecture, executable validation, evidence limits, and release scope.

### Fixed

- Rendered the 5G SA UE credentials from the private local environment so
  UERANSIM and the provisioned Open5GS subscriber use the same authentication
  values.
- Closed run metadata only for the scenario being stopped when 4G and 5G run
  records coexist.

## [1.0.0] - 2026-07-27

### Added

- Root `VERSION` authority for API, frontend, image, and release metadata.
- Offline `make version-check` policy enforcement and focused release tests.
- Reproducibility policy and an evidence-backed dependency/version matrix.
- Hardware-free CI and a unified `make softwarex-check` entry point.
- A schema-validated, sanitized public-result pipeline with passing 4G LTE,
  VoLTE/IMS, and 5G SA summaries plus preserved historical VoNR evidence.
- Recorded a local 5G VoNR software validation with 25/25 passing checks and
  retained the earlier public run record for historical traceability.
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

- Public passing summaries cover software 4G LTE/VoLTE and 5G SA. Historical
  VoNR software validation records 25/25 local checks; RF hardware,
  commercial-UE behavior, audio quality, and RTP performance use separate
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
- The complete locked npm dependency tree reports no audit findings.
- The `1.0.0` Real-IMS derived images are local build tags and have not
  been asserted as published registry artifacts.
- Removed private-key paths are absent from the published clean release history;
  material copied from older private clones must still be treated as revoked.
- This is a source-only release. Catalogued project image digests lack a
  verifiable source-to-build mapping and are blocked for binary republication.
- The application SBOM is partial and does not inspect final image filesystems.
- GitHub Private Vulnerability Reporting is enabled.
