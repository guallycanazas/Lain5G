# Changelog

All notable changes to Lain5G-Lab are recorded in this file.

## [1.0.0-rc.1] - Unreleased

### Added

- Root `VERSION` authority for API, frontend, image, and release metadata.
- Offline `make version-check` policy enforcement and focused release tests.
- Reproducibility policy and an evidence-backed dependency/version matrix.
- Hardware-free CI and a unified `make softwarex-check` entry point.
- A schema-validated, sanitized public-result pipeline with three passing
  software-validator summaries and one blocked VoNR attempt.
- English-first release documentation, Spanish overview, citation and community
  policy stubs, legal review, and a partial application dependency SBOM.

### Changed

- Pinned direct Python runtime and development dependencies to the versions
  tested in the release environment, with a complete exact constraints file.
- Switched supported frontend installation commands to `npm ci` while
  preserving `package-lock.json` and its integrity records.
- Pinned source builds to commits resolved from authoritative upstream tags.
- Pinned viable Docker bases and third-party Compose images by verified digest.
- Tagged locally derived Real-IMS images as `1.0.0-rc.1` and synchronized OCI
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

- No RF, hardware, database, or end-to-end scenario run was performed for this
  release-candidate dependency update.
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
- The `1.0.0-rc.1` Real-IMS derived images are local build tags and have not
  been asserted as published registry artifacts.
- Removed private keys remain reachable in pre-remediation Git history; a
  coordinated history and rotation decision is required before final release.
- This is a source-only candidate. Catalogued project image digests lack a
  verifiable source-to-build mapping and are blocked for binary republication.
- The application SBOM is partial and does not inspect final image filesystems.
- A private vulnerability-reporting channel and confirmed author metadata are
  still absent.
