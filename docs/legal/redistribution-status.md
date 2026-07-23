# Redistribution Status

## Interpretation

This assessment distinguishes publication of the Lain5G-Lab source repository
from conveyance of third-party binaries or container images. It is a technical
release record, not legal advice.

The status terms are:

- **Ready**: the repository contains the identified source and required notice
  for the stated mode of distribution.
- **Conditional**: redistribution is permitted in principle, but a listed
  source, notice, or artifact control must accompany publication.
- **Pull-only**: the repository references an upstream artifact; this review
  does not approve republishing that artifact.
- **Blocked**: evidence needed for a responsible redistribution claim is
  absent or inconsistent.

## Current Assessment

The `1.0.0-rc.1` boundary is source-only. Existing registry artifacts are
catalogued inputs for reproducibility, not binaries approved by this assessment.

| Distribution unit | Current status | Basis | Required action before redistribution |
| --- | --- | --- | --- |
| Lain5G-Lab first-party source | Ready | `LICENSE` contains the MIT grant; third-party configuration is separately identified. | Preserve the MIT notice and `THIRD_PARTY_NOTICES.md` in source distributions. |
| Imported Real-IMS BSD configuration | Ready | Exact upstream commit, per-file hashes, transformations, and full BSD-2-Clause notice are recorded. | Preserve `deployments/ims-real/config-provenance.json` and the complete BSD notice. |
| Open5GS catalogued image | Blocked for binary publication | A registry digest and current source commit are known, but no attestation or archived build record binds those bytes to that source and recipe. | Rebuild from the immutable commit or recover verifiable build provenance, then provide durable Corresponding Source, modifications, license, notices, digest, and final-image SBOM. |
| srsRAN 4G catalogued images | Blocked for binary publication | Registry digests and current source commit are known, but their source-to-binary mapping is unverified. The UHD recipe also changes upstream C++ standard flags. | Establish build provenance; provide Corresponding Source including the C++17 modification, UHD sources, notices, digest, and final-image SBOM. |
| srsRAN Project catalogued image | Blocked for binary publication | Source commit, local patch, UHD commit, and registry digest are known, but no build attestation binds them. | Establish build provenance and publish exact source, patch, UHD material, notices, digest, and final-image SBOM. |
| UERANSIM catalogued image | Blocked for binary publication | A registry digest and source commit are known, but their mapping is unverified and the GPL SPDX suffix is unresolved. | Establish build provenance, provide Corresponding Source and notices, and conservatively resolve the license suffix. |
| Kamailio catalogued image | Blocked for binary publication | A registry digest and source commit are known, but their mapping is unverified. | Establish build provenance, provide Corresponding Source and notices, and review selected modules and linked dependencies. |
| CoreDNS catalogued image | Blocked for binary publication | CoreDNS version, digest, and Apache-2.0 license are known, but the derivative build and complete image package inventory are not attested. | Establish build provenance and include Apache 2.0, change/NOTICE material, digest, and a final-image inventory. |
| Compact SIP catalogued image | Blocked for binary publication | First-party scripts use a Python base, but the catalogued registry digest has no attested source/build mapping or final-image inventory. | Rebuild with recorded provenance, generate a final-image package/license inventory, and carry base-image notices. |
| Backend application image | Conditional | Direct Python pins and licenses are recorded; no public final image digest is recorded. | Build the release image, generate a final-image SBOM, review the Python transitive closure, and include package notices. |
| Frontend application image | Blocked for binary publication | npm closure is locked, but no generated third-party notice bundle is copied into the nginx image. | Generate and ship a notice/license bundle for bundled code, then scan the final image. |
| Real-IMS Open5GS wrapper | Blocked for binary publication | Base digest and imported configuration are known, but embedded application/package versions and a complete image SBOM are absent. | Inspect the final filesystem, reconcile the Open5GS license label, and publish Corresponding Source. |
| Real-IMS Kamailio wrapper | Blocked for binary publication | Base digest is known; image label states `GPL-2.0-only` while exact source headers grant `GPL-2.0-or-later`. | Correct the release metadata in a separately authorised change, inspect the image, and provide Corresponding Source. |
| Secure pyHSS wrapper | Blocked for binary publication | Base digest and local source modification are known; exact AGPL suffix and full image inventory are unresolved. | Resolve the license expression, provide modified source to network users and recipients, and scan the final image. |
| Real-IMS RTPengine wrapper | Blocked for reproducible binary publication | APT channel is moving, package revisions differ by architecture, and no source commit is locked. | Lock a source/package snapshot per architecture, archive license/source material, and scan the final image. |
| Real-IMS MySQL and DNS wrappers | Blocked for binary publication | Base digests are known, but complete package/license inventories and exact MySQL version are not. | Inspect final images and retain all application, OS, and imported BSD notices. |
| MongoDB Official Image | Pull-only | Deployment references an external digest; MongoDB Server is SSPL-1.0 and the exact server tag is not recorded. | Do not republish under this assessment. If republication is intended, identify the exact server version and review SSPL section 13 and all image packages. |
| MariaDB Official Image | Pull-only | Deployment references an external digest captured from major tag `11`; exact patch version is absent. | Do not republish under this assessment. If republication is intended, identify the exact version and provide all GPL and image-package materials. |
| Dockerfile base images | Conditional as derivative inputs | Digests are locked, but each image is a multi-license aggregate. | Generate final-image SBOMs, retain installed package notices, and meet source obligations for every covered package. |
| Partial application SBOM | Ready only for its declared scope | Valid CycloneDX 1.7 source-manifest artifact; prohibited path/value checks passed. | Do not describe it as a complete release or container SBOM. See `docs/release/sbom-status.md`. |

## Release Blockers

The source repository can be distributed with its legal files, but the release
must not make a blanket claim that every catalog or Real-IMS container is
redistribution-complete. The following controls remain open:

1. No final image filesystem has been catalogued for this legal review.
2. No release archive or registry-adjacent mechanism has been demonstrated for
   durable Corresponding Source access for published AGPL/GPL images.
3. The static frontend image has no generated third-party notice bundle.
4. Python transitive licenses and OS package licenses have not received a
   complete component-level review.
5. MongoDB's exact server version, MariaDB's exact patch version, and the
   embedded versions in several Real-IMS GHCR bases are not mapped from their
   digests.
6. RTPengine is not source-snapshot reproducible and differs by architecture.
7. UHD explicitly contains file-level and directory-level license exceptions;
   the compiled host subset has not been audited file by file.
8. Existing Real-IMS OCI labels use `AGPL-3.0-only` for Open5GS and pyHSS,
   `GPL-2.0-only` for Kamailio, and `GPL-3.0-only` for RTPengine. Open5GS and
   Kamailio exact source evidence grants `-or-later`; the pyHSS and RTPengine
   suffixes remain unresolved. Those labels require a separately authorised
   metadata correction before publication.
9. No verifiable source-to-digest build record exists for the catalogued project
   images.
10. BIND 9, Redis, and Docker CLI/Compose are known recipe inputs but do not yet
    have exact final-image version and notice records.

## Minimum Publication Set

Any future binary or image publication should place the following materials
next to the artifact or inside it, as applicable:

- This notice and the exact upstream license texts.
- A machine-readable SBOM generated from the final artifact.
- The exact image digest and platform.
- Corresponding Source, build scripts, local patches, and modification notices
  for copyleft-covered works.
- Package-level copyright and NOTICE files for permissive and operating-system
  components.
- A written mapping from every published image digest to those source and
  notice materials.

Publication should remain blocked if any artifact contains private keys,
credentials, subscriber data, local environment values, runtime captures,
database state, backups, or host-specific paths.
