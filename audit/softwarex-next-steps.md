# SoftwareX and Release Next Steps

## Boundary

This plan starts from local source candidate `1.0.0-rc.1`. It does not authorize
RF, hardware access, firmware/FPGA changes, history rewriting, a final tag,
remote publication, DOI creation, or journal submission. Maintainer approval is
required at each publication boundary.

## 1. Resolve Source-Release Blockers

1. Decide whether the repository will be made public from a rewritten history,
   a new clean repository, or an explicitly documented non-public lineage.
   Coordinate any rewrite with all collaborators; do not rewrite the shared
   branch automatically.
2. Rotate any historical key that may have been used outside disposable test
   contexts. Verify that retained local/registry image layers do not contain it.
3. Correct the remaining root-owned sensitive-file permissions with explicit
   administrative authorization, then apply a retention policy to runs and
   backups without publishing their contents.
4. Move unnecessary operational-looking RF/device defaults out of tracked
   profiles. Keep only neutral, non-authorizing examples and synthetic
   simulation vectors.
5. Enable GitHub private vulnerability reporting or publish another verified,
   monitored private security contact. Assign owners and realistic response
   targets.
6. Designate a private conduct-reporting channel and confirmed project
   maintainers.

Acceptance condition: the approved release history and current tree have no
known key material, security/contact policies have real owners, and all
remaining exceptions are reviewed rather than silently ignored.

## 2. Confirm Identity and Publication Metadata

Obtain direct approval for:

- software author names and order;
- article author names and order, if different;
- affiliations and ORCIDs;
- corresponding author and public contact;
- CRediT roles;
- funding and acknowledgements;
- conflict-of-interest and data/code availability declarations;
- maintainer, support, and governance ownership.

Then replace collective placeholders in `AUTHORS.md`, `CITATION.cff`, and
`codemeta.json`. Do not add a DOI, release date, journal citation, or article
status until an issuing service or journal supplies it.

## 3. Establish Exact Candidate Verification

1. Freeze the reviewed source tree after the history decision.
2. Run `make softwarex-check` from a clean checkout with no laboratory secrets,
   Docker socket, RF device, or private run corpus.
3. Publish the branch only after maintainer review, then require the SHA-pinned
   GitHub Actions workflow to pass at the exact candidate commit.
4. Record the exact commit, toolchain, duration, test counts, coverage, skipped
   checks, and warnings in the release record.
5. Add a reviewed backend coverage threshold and frontend coverage tooling if
   coverage is a release criterion.
6. Upgrade the Vitest/Vite development toolchain in a separate tested change to
   resolve the five known development audit findings.

Acceptance condition: local and hosted checks pass at the same reviewed commit,
and every skipped hardware/integration check is explicit.

## 4. Improve Public Scientific Evidence

No RF rerun is required for source publication. For stronger software-only
claims:

1. Run from a clean checkout at the exact candidate commit in an isolated,
   recorded software environment.
2. Record immutable image digests, Docker/Compose versions, host resource
   summary, effective non-sensitive configuration hashes, command scope, and
   terminal status.
3. Export minimal sanitized event excerpts or structured observations that
   correlate each criterion without exposing subscriber data, addresses,
   credentials, paths, or protocol payloads.
4. Bind exported evidence cryptographically to the private source record while
   retaining the private record under controlled access.
5. Replace configuration-derived unconditional checks with observed criteria or
   label them explicitly as static configuration checks.
6. Diagnose the VoNR timeout in software-only isolation. Publish another
   `BLOCKED`/`FAIL` record if it still does not complete; do not suppress a
   negative result.

Any future SDR/commercial-UE evidence requires separate legal, technical, and
institutional authorization. It must use the same provenance and anonymization
standard and must preserve negative outcomes.

## 5. Complete Reproducibility and Binary Compliance

Treat binary publication as a separate release project:

1. Build every intended image from immutable source in a recorded clean
   environment and produce source-to-image attestations.
2. Snapshot APT inputs or archive exact package artifacts and source packages.
3. Generate final-image CycloneDX/SPDX SBOMs from immutable registry digests or
   hashed archives without exposing the Docker socket to an untrusted scanner.
4. Generate and ship frontend, Python, OS-package, and permissive-license notice
   bundles.
5. Provide durable Corresponding Source, build scripts, local patches, and
   modification notices for every GPL/AGPL-covered binary.
6. Resolve UERANSIM, pyHSS, RTPengine, and Real-IMS label suffix questions with
   qualified legal review.
7. Map exact MongoDB, MariaDB, MySQL, BIND, Redis, Docker CLI/Compose, and other
   embedded versions from each final digest.
8. Re-run secret, path, subscriber-data, and runtime-state scans against every
   final image and archive.

Acceptance condition: every published digest has a reviewed source/build/SBOM/
notice mapping and no unresolved `Blocked` row in
`docs/legal/redistribution-status.md`.

## 6. Prepare the SoftwareX Package

Only after authors and the target template are confirmed:

1. Obtain the current official Original Software Publication template and
   author instructions directly from the journal.
2. Create the five required manuscript sections without inventing adoption,
   performance, validation, or reproducibility claims.
3. Complete metadata C1-C8, abstract, keywords, highlights, declarations,
   author contributions, cover letter, and submission checklist.
4. Build figures from versioned editable sources and public data only. Keep raw
   private logs, RF plans, subscriber material, and hardware identifiers out of
   the package.
5. Cite upstream projects and methods from verified primary sources. Distinguish
   Lain5G-Lab orchestration/integration contributions from upstream core, RAN,
   IMS, media, DNS, database, and hardware software.
6. Have all authors approve the exact manuscript, metadata, evidence claims,
   funding, conflicts, and repository commit before submission.

Acceptance condition: the manuscript claims are a strict subset of the
canonical capability table and public evidence, and every required declaration
has an approved human owner.

## 7. Controlled Publication Sequence

After every applicable gate above passes:

1. Review a clean status, complete diff, local verification report, hosted CI,
   legal disposition, and evidence inventory.
2. Change version/release metadata from the release candidate only in a
   dedicated reviewed release commit.
3. Create an annotated final tag locally and verify its target and contents.
4. Obtain maintainer approval before any push or remote release creation.
5. Archive the immutable release, obtain the issued DOI, and then update citation
   metadata in a subsequent reviewed commit.
6. Submit to SoftwareX only after the repository URL, release artifact, DOI,
   author metadata, and declarations are final and mutually consistent.

No command in this sequence should be automated across the approval boundaries.
