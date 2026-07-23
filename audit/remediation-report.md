# Release-Candidate Remediation Report

## Scope

This report maps the historical 2026-07-22 audit of commit
`c3247c99b6c969189efe9e57a46f110c88c26f4d` to the local
`release/softwarex-v1.0.0` branch. It records remediation state without
declaring a final release, publication, DOI, or SoftwareX submission.

Status terms:

- `COMPLETED`: the stated current-tree change and its local regression checks
  are present.
- `PARTIAL`: meaningful remediation exists, but the original gate is not fully
  satisfied.
- `OPEN`: no sufficient remediation is present.
- `BLOCKED`: maintainer authority, external infrastructure, legal review, or
  information not inferable from the repository is required.

## Remediation Commits

| Commit | Purpose |
| --- | --- |
| `ae59c435d91860d1ec70e7bba5f7df2673302e36` | Preserve the read-only audit snapshot |
| `84e461aa3ea1f1a26f069755d9ec76238ca091c9` | Remove versioned UDM keys from the current tree and harden sensitive-file handling |
| `0b4212f4fb4e7a19ebc8562046d139a44d9c3a3c` | Enforce non-mutating RF dry-run contracts |
| `217d41a8c788057d6b7eb7324c3d480ac895454e` | Make the base application observation-only and gate mutation |
| `a5f4625f50f1772d1a6352011991b15091f0a4b9` | Establish version and dependency reproducibility policy |
| `d5e84247ee48d22181cee9ac18aa43326a7f1a4e` | Add hardware-free CI and unified safe verification |
| `12c4a38404bbaf240c698a056e3f47182081ab5c` | Add the public-result schema, exporter, verifier, and tests |
| `060e669d3f65e1844a702b1b5264be6933ef45c2` | Add the initial sanitized software-validator summaries; the candidate documentation set later corrects the VoNR completion outcome without a rerun |

## Security Disposition

| Audit item | Status | Current disposition | Remaining gate |
| --- | --- | --- | --- |
| Two tracked UDM private keys | `PARTIAL` | Files are absent from the current tree; replacements are generated at runtime with owner-only directory/file modes and tmpfs-backed runtime use. | The old key material remains in reachable history. Any environment that consumed it needs explicit rotation, and the maintainer must approve a coordinated history decision. |
| Key inclusion in image layers | `COMPLETED` for current recipes | Current build context no longer copies the removed key files. Regression tests cover runtime generation and modes. | Previously published or locally retained image layers were not audited or revoked by this branch. |
| Ignored sensitive-file permissions | `PARTIAL` | A local permission pass corrected 796 entries without reading their contents. | 84 root-owned entries could not be changed by the audit user; administrative authorization and a retention review are required. |
| Current-tree sensitive-file detection | `COMPLETED` for the custom gate | `scripts/security/check-sensitive-files.sh` and CI reject known sensitive paths and key material in the current tree. | This custom gate is not a full-history scanner; the known historical keys remain a deliberate failure condition for final release. |
| RF dry-run side effects | `COMPLETED` | Regression tests require dry-run paths to avoid Docker, UHD, RF, marker mutation, run creation, and destructive cleanup. | Real RF behavior remains outside automated validation and requires separate authorization. |
| Local application privilege | `COMPLETED` for the default | Base Compose binds to loopback, mounts source read-only, omits the Docker socket, and disables mutation. A separate override plus runtime flag is required for operations. | The opt-in Docker socket grants host-root-equivalent control and is suitable only for a dedicated trusted workstation. No user authentication layer was added. |
| Static simulation identifiers | `PARTIAL` | Documentation labels committed simulation identities as synthetic test vectors. | A future data review should replace any unnecessary valid-shaped defaults and move operational RF/device values to ignored overlays. |

## Reproducibility and CI Disposition

| Audit item | Status | Current disposition | Remaining gate |
| --- | --- | --- | --- |
| Single version authority | `COMPLETED` | Root `VERSION` is `1.0.0-rc.1`; backend, frontend, image, citation, and CodeMeta values are checked against it. | Change to `1.0.0` only during a separately reviewed final release. |
| Python dependency control | `PARTIAL` | Direct requirements and the tested closure are exact-version constrained. | Artifact hashes are absent, the closure was captured on CPython 3.14 while the image targets 3.12, and APT is not snapshotted. |
| npm dependency control | `PARTIAL` | `package-lock.json` and `npm ci` define the tested closure; production audit reports no finding. | Five development-tool findings remain and require a reviewed Vitest/Vite major upgrade. |
| Source-build revisions | `COMPLETED` for source selection | Open5GS, UERANSIM, both srsRAN variants, UHD, and Kamailio use exact commits. | Exact source selection does not establish bit-reproducible APT closure or provenance of old registry images. |
| Registry/image inputs | `PARTIAL` | External inputs are digest-addressed and platform scope is documented. | Catalogued project image digests have no attested source-to-build mapping; final-image SBOMs and notice bundles are absent. Binary republication is blocked. |
| Hardware-free CI definition | `COMPLETED` locally | `.github/workflows/ci.yml` uses SHA-pinned actions and invokes `make softwarex-check` without RF or laboratory secrets. | No hosted run for this local candidate exists until a maintainer publishes the branch and reviews the resulting run. |
| Unified local verification | `COMPLETED` | Make targets cover backend coverage, frontend tests/typecheck/build, source formats, Compose, profiles, versions, links, current-tree secrets, release files, and public results. | The current gate has no minimum coverage threshold and no standard full-history secret scanner. |

## Scientific Evidence Disposition

| Audit item | Status | Current disposition | Remaining gate |
| --- | --- | --- | --- |
| Public result contract | `COMPLETED` | A schema, exporter, redaction tests, configuration hashes, and public verifier are versioned. | The exporter validates field format and hashes, not clean-checkout execution provenance. |
| 5G SA software summary | `PARTIAL` | Public artifact reports 15/15 validator checks passing at source commit `12c4a38...`; classification is `SIMULATION_ONLY`. | No raw sanitized protocol excerpts, runtime image digests, or independently reviewable event correlation are included. |
| LTE software summary | `PARTIAL` | Public artifact reports 14/14 validator checks passing at the same source commit; classification is `SIMULATION_ONLY`. | The same public-evidence limitations apply. |
| Laboratory 4G IMS summary | `PARTIAL` | Public artifact reports 22/22 validator checks and Digest SIP registration; classification is `SIMULATION_ONLY`. | It does not establish AKA, Cx, Rx, a complete call, media, SDR, or commercial-UE behavior. One validator check is configuration-derived rather than an observed protocol event. |
| VoNR software attempt | `OPEN` | The attempt is honestly published as `BLOCKED` and `NOT_VALIDATED`; no scenario criterion was assessed. | Diagnose and rerun only in an authorized software-only environment if VoNR simulation evidence is required. Do not convert container health or historical runs into a positive claim. |
| LTE/IMS/NSA hardware observations | `PARTIAL` | README language preserves the observations as non-public context and records negative/unstable outcomes. | No commit-linked, anonymized, correlated public result supports a hardware claim. |
| Complete VoLTE, stable NR data, commercial-UE 5G SA, and RF VoNR | `OPEN` | All remain explicitly `NOT_VALIDATED`. | New evidence would require separately authorized experiments and the complete acceptance criteria; no such experiment is required to prepare this source candidate. |

The three passing public artifacts are sanitized validator summaries. They are
useful, versioned regression evidence, but exclusion of raw logs, captures,
protocol messages, and runtime configuration means they are not independently
reviewable protocol traces.

## Documentation, Metadata, and Legal Disposition

| Audit item | Status | Current disposition | Remaining gate |
| --- | --- | --- | --- |
| English-first documentation | `COMPLETED` for the root overview | `README.md` is English-first and `README.es.md` provides a Spanish overview linked to one canonical status table. | Most detailed scenario guides remain Spanish and should be translated or clearly labelled for an English journal package. |
| Citation and CodeMeta syntax | `PARTIAL` | CFF and CodeMeta identify the source-only candidate and do not advertise a fictitious article. | Confirmed people, order, affiliations, ORCIDs, corresponding contact, funding, conflicts, release date, and DOI remain unavailable. |
| Security/conduct contacts | `BLOCKED` | Policies explicitly prohibit public sensitive reports. | A monitored private vulnerability channel, private conduct channel, owners, and response targets require maintainer action. |
| Source licensing | `COMPLETED` for the stated scope | `LICENSE` covers first-party MIT source; imported BSD configuration has exact provenance and notice. | This conclusion does not cover third-party binaries as one aggregate work. |
| Binary/container redistribution | `BLOCKED` | Exact known limitations and component licenses are documented. | Source-to-digest attestations, final-image inventories/SBOMs, notices, Corresponding Source delivery, and several license details are incomplete. |
| Application SBOM | `PARTIAL` | A network-isolated CycloneDX 1.7 source-manifest artifact inventories 260 npm and 9 direct PyPI entries. | It omits final images, OS packages, Python transitive packages, C/C++ closure, and an internally complete dependency graph. |
| SoftwareX manuscript package | `OPEN` | No article, DOI, submission, or acceptance is claimed. | Confirm authors and target template, then create and review the manuscript, C1-C8 metadata, declarations, highlights, cover letter, figures, and supplement. |

## Current Decision

The branch is suitable for continued **local source-only release-candidate
review** after final checks. It is not ready for a final `v1.0.0` tag, remote
release, DOI deposit, SoftwareX submission, or binary/container republication.
No RF or hardware run is required to resolve the documentation, history,
metadata, CI, and legal gates above.
