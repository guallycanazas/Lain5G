# Proposed Changes After the Read-Only Audit

This is the remediation plan written for audited commit
`c3247c99b6c969189efe9e57a46f110c88c26f4d` on 2026-07-22. It intentionally
retains the original future-tense actions. Several items were subsequently
completed or partially completed; their current dispositions are recorded in
[remediation-report.md](remediation-report.md). This file is not a current
release checklist.

## Constraint

No change in this plan was applied during the historical audit. The order is
intentional: security and scientific-claim integrity must be resolved before
editorial packaging or a `v1.0.0` tag.

## P0: Release blockers

| Order | Proposed change | Acceptance criterion |
| ---: | --- | --- |
| 1 | Rotate the two tracked UDM private keys, remove them from source and image layers, generate/mount per-deployment keys, and decide with the maintainer whether reachable Git history must be rewritten | No private-key block in current tree, build context, image history, or approved release history; replacement keys are never committed |
| 2 | Restrict all ignored secret/RF files and backups to owner-only modes; define encrypted backup and retention policy | Automated permission check passes; no secret-bearing `0664` file remains |
| 3 | Replace tracked operational RF/device defaults with neutral examples and ignored local overlays | Versioned files cannot be used as an operational RF plan; static tests still pass |
| 4 | Reconcile README scientific claims with `audit/scenario-status.md` | Every claim has a public artifact reference or is explicitly marked partial/not validated |
| 5 | Add a release-grade secret scanner for current tree and history | Gitleaks-equivalent scan passes with reviewed synthetic-test allowlist |
| 6 | Fix the NSA RF start path so dry-run is enforced before any RF-capable action | Unit/static test proves `LAIN5G_DRY_RUN=true` cannot reach RF start |

The history decision for leaked keys is potentially disruptive and must be
explicitly approved. It must not be performed automatically on a shared branch.

## P1: Stabilization and reproducibility

1. Add a single authoritative version source set to `1.0.0` and derive or
   validate backend, frontend, citation, CodeMeta, docs, and release metadata.
2. Pin Python dependencies with a lockfile and hashes; retain a human-readable
   top-level dependency declaration.
3. Pin standard base images and scenario images by digest where operationally
   reasonable.
4. Pin Open5GS, UERANSIM, srsRAN 4G, UHD, and Kamailio to exact commits and
   record source licenses.
5. Remove the mutable RTPengine `latest` repository reference.
6. Preserve `package-lock.json`; align direct dependency ranges with the
   release policy and use `npm ci` in CI.
7. Add a coverage threshold, prioritizing real IMS, deployment operation,
   Open5GS connection, and subscriber safety paths with mocks/fakes only.
8. Resolve the Starlette/httpx deprecation warning with a compatible pinned
   dependency set and regression tests.
9. Clarify or remove the unresolved optional Open5GS WebUI image path.
10. Ensure all dry-run paths are side-effect free; add tests for run-directory,
    marker-file, Docker, and hardware side effects.

## P1: Continuous integration

Create `.github/workflows/ci.yml` with no RF or hardware access. Pin actions to
reviewed stable releases or commits. Required jobs:

| Job | Required checks |
| --- | --- |
| Metadata | Required files, version consistency, CFF, CodeMeta, JSON/YAML |
| Backend | Locked install, 149+ tests, coverage threshold |
| Frontend | `npm ci`, tests, type check, production build |
| Static source | ShellCheck, Hadolint, internal links, Makefile dry-run |
| Compose | All ten source manifests with safe example environments |
| Security | Secret history scan and dependency vulnerability report |
| SBOM | Generate/validate CycloneDX or SPDX artifacts |
| SoftwareX | Run `make softwarex-check` and validate public results |

The workflow must not mount a Docker socket from a privileged runner, access
laboratory networks, start RF services, or consume subscriber/RF secrets.

## P2: Scientific evidence and public results

1. Define a versioned run schema requiring run ID, timestamps, exact Git
   commit, project version, scenario, command, immutable image identifiers,
   public configuration hash, environment, success criteria, result, and
   limitations.
2. Add an anonymizer that removes subscriber identifiers, SIM cryptographic
   fields, credentials, private addresses, RF plans, operator notes, hardware
   serials, and protocol payloads before export.
3. Add automated tests with synthetic fixtures for both positive redaction and
   leak rejection.
4. Create `results/public/` with README, environment, simulation, LTE, IMS,
   VoLTE, 5G SA, 5G NSA, tables, and figures subdirectories.
5. Re-run software-only 5G SA, LTE, IMS signaling, and VoNR scenarios at the
   final release commit in a clean environment. These runs do not require RF.
6. Publish negative and incomplete outcomes with the same schema as passing
   outcomes.
7. For existing SDR evidence, export only sanitized summaries and minimal log
   excerpts after independent review. Do not copy raw logs.
8. Do not upgrade the VoLTE claim unless one run proves authenticated
   registration, complete SIP dialog, successful INVITE response, ACK/BYE or
   equivalent termination, and bidirectional RTP.
9. Do not upgrade NSA beyond partial validation without one correlated run
   proving secondary NR activation and stable user-plane traffic.
10. Record source-code drift between an evidence commit and the release commit;
    preferably regenerate evidence at the exact release commit.

No new RF run is required merely to prepare the repository. Any future RF work
must remain separately authorized and outside automated release tooling.

## P2: Unified verification

Add a side-effect-free `make softwarex-check` target. It should fail on any
unmet mandatory release gate and emit explicit `PASS`, `FAIL`, `WARNING`,
`SKIPPED`, or `NOT_TESTED` states.

Minimum checks:

- Mandatory editorial and governance files.
- Version consistency.
- CFF and CodeMeta schema validation.
- Known-secret and private-key scan.
- Internal links and referenced files.
- Backend tests and coverage.
- Frontend tests, type check, and build.
- Shell, Dockerfile, YAML, and JSON checks.
- All source Compose models.
- Public-result schema and anonymization checks.
- SBOM presence and freshness.
- Explicit `NOT_TESTED` status for unavailable hardware validation.

The intentionally invalid JSON fixture needs an explicit exclusion or expected
failure assertion rather than weakening JSON validation globally.

## P3: Public documentation

1. Preserve the current Spanish README as `README.es.md` after correcting its
   claims.
2. Create an English `README.md` organized for a reviewer: purpose, scientific
   problem, original integration contribution, upstream boundary, architecture,
   scenarios, scientific status, requirements, quick start, software-only
   example, validation, demonstrated/not-demonstrated results,
   reproducibility, RF safety, docs, citation, license, dependencies, support,
   and article link placeholder.
3. Add `Licence.txt` with the exact MIT text from `LICENSE`.
4. Add `CITATION.cff` and `codemeta.json` with confirmed authors only. Keep
   ORCID and DOI as explicit `TODO` values until supplied/created.
5. Add `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`,
   `CODE_OF_CONDUCT.md`, `AUTHORS.md`, and a concise governance policy.
6. Update `THIRD_PARTY_NOTICES.md` with component, exact version/commit,
   upstream URL, license, use, redistribution mode, and open legal questions.
7. Reconcile stale architecture, configuration, VoNR, backend, frontend,
   third-party, and UHD-version documentation.
8. Add architecture, API, developer, user, reproducibility, experimental
   protocol, environment, compatibility, scenario, limitations, RF safety, and
   artifact inventory documents without duplicating the README.

## P3: SBOM and provenance

1. Install a pinned SBOM generator in CI.
2. Generate CycloneDX or SPDX documents for Python, npm, first-party images,
   and combined release artifacts.
3. Record the command, tool version, source commit, and generation timestamp.
4. Validate that generated SBOMs do not contain local paths, secrets, private
   addresses, or runtime configuration.
5. Complete provenance records for non-real-IMS configuration and the UHD patch.
6. Document unresolved AGPL/GPL redistribution questions rather than assuming
   compatibility.

## P4: SoftwareX article package

Create `paper/softwarex/` using the official Original Software Publication
template dated 2026-03-06. The package should contain the manuscript, metadata
table C1-C8, highlights, cover letter, declarations, author information,
submission checklist, reviewer self-assessment, verified references, figures,
tables, supplementary material, and optional video planning documents.

Editorial constraints to enforce automatically where possible:

- English manuscript.
- Approximately 100-word abstract.
- No more than six keywords.
- No more than 4,000 words in the main body.
- Five mandatory main sections.
- No more than six main figures.
- Three to five highlights, each no more than 85 characters.
- No invented author, affiliation, ORCID, DOI, funding, adoption, performance,
  or experimental result.

The manuscript must identify Lain5G-Lab as an orchestration, integration,
validation, and evidence environment. It must not present it as a new mobile
core, RAN, 3GPP implementation, certification system, or replacement for
Open5GS, srsRAN, UERANSIM, Kamailio, pyHSS, RTPengine, or UHD.

## P4: Figures and optional video

Prepare at most six reproducible figures from editable, versioned sources:

1. System architecture and upstream boundaries.
2. Deployment and validation flow.
3. Simulation, SDR, and commercial-UE scenario relationship.
4. Validated LTE/EPC/IMS signaling flow with limitations.
5. Quantitative software-only results, only after public data exist.
6. Final capability/limitation matrix.

Create a script, source, caption, and data dependency for each figure. Do not
include private identifiers, addresses, RF plans, or invented metrics.

For the optional video, create only a script, storyboard, and privacy/safety
checklist. Do not create a placeholder video file and do not demonstrate live RF.

## Release sequence after all gates pass

The future release sequence should be prepared but not executed automatically:

```bash
git status --short --branch
make softwarex-check
git diff --check
git diff --stat
git diff
git add <reviewed-release-files>
git commit -m "release: prepare Lain5G-Lab v1.0.0"
git tag -a v1.0.0 -m "Lain5G-Lab v1.0.0"
```

Only after maintainer review should remote publication commands be considered:

```bash
git push origin main
git push origin v1.0.0
gh release create v1.0.0 --verify-tag --title "Lain5G-Lab v1.0.0" --notes-file docs/release/v1.0.0.md
```

Zenodo archival must follow the public GitHub release. The resulting DOI then
needs to be added to citation metadata, CodeMeta, the SoftwareX metadata table,
and release documentation in a subsequent reviewed update. No DOI may be
invented in advance.

## Release gates

The project must not be marked ready until all conditions below are true:

- All available tests and builds pass at the target commit.
- All source Compose manifests pass in a clean checkout.
- The tracked tree and approved history contain no known secrets or private keys.
- Main documentation is English-first with a Spanish copy.
- `README.md`, `LICENSE`, and `Licence.txt` exist.
- Citation and CodeMeta files validate and share version `1.0.0`.
- CI is green without RF or laboratory secrets.
- Dependencies and image references meet the documented reproducibility policy.
- Public results are anonymized and schema-valid.
- Every scientific assertion links to evidence or states its limitation.
- The manuscript has all five mandatory sections and metadata C1-C8.
- DOI and submission steps have explicit pending/completed status.
- Authors approve identities, affiliations, contributions, funding,
  declarations, and final submission.

Until then, the repository remains in audit and release-preparation state.
