# Dependency Provenance

## Purpose and Scope

This document records how Lain5G-Lab release `1.0.0-rc.1` identifies the
origin and version of third-party inputs. It covers source-built network
components, registry images, application package manifests, base images, and
imported configuration. It does not claim that a digest, lock file, or SBOM is
by itself evidence of license compliance.

The normative release values are in `docs/reproducibility/version-matrix.md`.
Detailed license findings are in `THIRD_PARTY_NOTICES.md`, and redistribution
decisions are in `docs/legal/redistribution-status.md`.

## Evidence Hierarchy

Provenance conclusions use the following evidence in descending order:

1. An exact commit or immutable OCI digest recorded in a checked-in build or
   lock file.
2. An exact package version and integrity value recorded in a package lock.
3. Upstream license or copyright material at the exact commit, tag, or package
   version.
4. Maintainer-controlled registry metadata for the exact package release.
5. Upstream project documentation when no immutable license document for the
   consumed artifact is available.

Mutable tags, current default branches, image labels, and third-party license
scanners are corroborating evidence only. License identifiers are not inferred
from project type, programming language, or historical reputation.

## Source-Built Components

| Component | Selected ref | Exact commit | Acquisition authority | Integrity control |
| --- | --- | --- | --- | --- |
| Open5GS | `v2.7.5` | `7dfd9a39649700c24c22f1978ed7a35541a72cca` | `https://github.com/open5gs/open5gs.git` | Dockerfile fetches and detaches the commit, then asserts `HEAD`. |
| UERANSIM | `v3.2.6` | `384636f4fcf46b8c86109790ff3e2cd242b53556` | `https://github.com/aligungr/UERANSIM.git` | Dockerfile fetches and detaches the commit, then asserts `HEAD`. |
| srsRAN 4G | `release_23_11` | `eea87b1d893ae58e0b08bc381730c502024ae71f` | `https://github.com/srsran/srsRAN_4G.git` | Both simulation and UHD recipes assert `HEAD`. |
| UHD | `v4.10.0.0` | `2af4ddb96219a99d2300804830e0971f79557b23` | `https://github.com/EttusResearch/uhd.git` | Both UHD recipes assert `HEAD`. |
| Kamailio | `5.8.8` | `053181eb9c3136836cb272584b582484a9a11b48` | `https://github.com/kamailio/kamailio.git` | Dockerfile fetches and detaches the commit, then asserts `HEAD`. |
| srsRAN Project | `release_24_10_1` | `ef4b0749a12a3b1a8347ae01c937a621603b4069` | `https://github.com/srsran/srsRAN_Project.git` | Dockerfile asserts `HEAD` before applying the tracked UHD compatibility patch. |
| pyHSS | `1.0.2` | `71a91f6d9e6b910a74750e266edb7642ca8f9971` | `https://github.com/nickvsnetworking/pyhss.git` | Tag commit resolved from the authoritative remote; active consumption is through a locked GHCR image. |

The first six commits were resolved from upstream tag refs and are repeated in
the version matrix. Annotated tags use their peeled commit. The pyHSS tag is
used by the checked-in upstream-derived reference Dockerfile; the active image
is independently locked by OCI digest.

RTPengine is an exception. The image consumes signed packages from release
channel `26.0`. The repository keyring is checksum-pinned, but the package
channel can move and currently resolves to different package revisions by
architecture. No RTPengine source commit or repository snapshot date is
locked, so this source chain is incomplete.

## OCI Inputs

All active external images are addressed by an OCI index or manifest digest.
The complete values and verified platforms are in the version matrix. The
principal classes are:

- Docker Official Images for Python, Node.js, nginx, Ubuntu, Debian, MongoDB,
  and MariaDB.
- The upstream-publisher `coredns/coredns` image.
- GHCR images from `herlesupreeth` for Real-IMS Open5GS, Kamailio, pyHSS, and
  MySQL.
- Public project catalog images for the locally aliased Open5GS, UERANSIM,
  srsRAN, Kamailio, DNS, and SIP roles.

Registry inspection proves that a digest exists and identifies its manifest
bytes. It does not bind a catalogued project image to the current Dockerfile or
source commit. No build attestation or equivalent archived build record was
available for those mappings, so they are not approved binary provenance.

An OCI digest authenticates bytes obtained from a registry; it does not reveal
the human version of every installed package and does not establish the
license of the aggregate. For MongoDB and the Real-IMS GHCR bases, the release
records do not map every digest to an exact embedded application version.

`deployments/ims-real/images.lock.yaml` is the specific authority for the
Real-IMS base images. Local `:local` tags are convenience aliases and are not
provenance identifiers.

## Python Packages

`backend/requirements.txt` and `backend/requirements-dev.txt` define the nine
direct packages. Every direct requirement is exactly pinned. The tested
transitive environment is frozen in `backend/constraints.txt` with 29 package
versions, including pip.

The constraints file was captured from CPython 3.14.4, whereas the backend
container targets CPython 3.12. It is therefore evidence of the tested host
closure, not proof that every wheel selected in a future 3.12 image build will
have identical provenance. No Python wheel or source archive is stored in the
repository, and the constraints file does not contain distribution hashes.

Direct-package licenses were verified from exact-version PyPI metadata and the
maintainer-controlled source projects. Transitive Python licenses remain a
separate review item.

## npm Packages

`frontend/package-lock.json` is a lockfile version 3 record for frontend
version `1.0.0-rc.1`. It provides the exact resolved version, registry tarball,
and Subresource Integrity value for the npm closure. The semver ranges in
`frontend/package.json` are declarations, not the final version authority.

The direct set consists of seven packages in `dependencies` and eight packages
in `devDependencies`. Some entries under `dependencies`, notably Vite and the
React Vite plug-in, are build tools and are not intended to survive the
multi-stage image build. The lock nevertheless records both production and
development closure. No npm tarball or `node_modules` directory is stored in
the repository.

Direct-package licenses were verified against each exact npm registry record
and its maintainer-controlled repository. The registry's package metadata is
authoritative for the published tarball, while the integrity field binds the
lock entry to that tarball.

## Imported Configuration

The Real-IMS package vendors selected files from
`herlesupreeth/docker_open5gs` commit
`3685b58aa0c7c28b2fecc6b9533f128285bf8dda`. The upstream commit is recorded
as signature-verified in the version matrix.

`deployments/ims-real/config-provenance.json` records each imported path, its
local SHA-256, and an upstream SHA-256 where a transformation occurred. The
documented transformations are limited to newline normalisation, digest
pinning, safer `COPY` use, release-channel pinning, keyring verification, and
replacement of copied private-key material with runtime generation. The
upstream BSD-2-Clause notice is reproduced in `THIRD_PARTY_NOTICES.md`.

This provenance record covers only the listed files. A file absent from the
record must not be represented as imported from that upstream commit.

## SBOM Provenance

`sbom/lain5g-lab-application.cdx.json` was generated from the checked-in source
manifests with the pinned Syft container documented in
`docs/release/sbom-status.md`. The scanner was network-isolated and all ignored
or potentially private paths were explicitly excluded. npm development
dependencies were enabled; file metadata was disabled to avoid recording
host filesystem metadata. Syft still records normalized repository-relative
manifest locations; validation confirmed that no host path or scan-root path is
present.

The SBOM is deliberately labelled partial. It inventories the npm lock closure
and the nine direct Python requirement entries. It does not inspect final image
filesystems, operating-system packages, source-built C/C++ dependency
closures, the Python constraints closure, firmware, FPGA images, local runtime
state, or database contents.

## Update Procedure

For a future dependency update, the release custodian should:

1. Resolve tags from the authoritative remote and record the peeled commit.
2. Pin every base or deployment image by digest and record its platform set.
3. Verify license material at the consumed commit or exact package version.
4. Update imported-file hashes and document every transformation.
5. Regenerate the source SBOM with ignored/private paths excluded.
6. Generate final-image SBOMs and source-offer material before publishing
   copyleft-covered binaries.
7. Reassess `docs/legal/redistribution-status.md`; a version bump must not
   inherit a prior release's legal conclusion without review.
