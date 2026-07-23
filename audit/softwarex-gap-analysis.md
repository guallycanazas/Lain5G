# SoftwareX and v1.0.0 Gap Analysis

This gap analysis is a historical snapshot of audited commit
`c3247c99b6c969189efe9e57a46f110c88c26f4d` on 2026-07-22. References to the
"current" state below mean that audit snapshot, not the release candidate. Use
the [canonical capability table](../README.md#canonical-capability-status)
for current scientific classifications.

Post-audit note: sanitized scenario artifacts now evaluate source commit
`12c4a38404bbaf240c698a056e3f47182081ab5c` and are versioned by publication
commit `060e669d3f65e1844a702b1b5264be6933ef45c2`. They include three passing
software-only results and one blocked VoNR attempt. This later work resolves
some snapshot gaps but does not rewrite the historical findings below.
Current dispositions are recorded in
[remediation-report.md](remediation-report.md).

## Audit conclusion

This repository is not being declared ready. The current output is an audit
only. Critical security, scientific provenance, reproducibility, release, and
editorial gaps prevent a defensible `v1.0.0` or SoftwareX submission.

## Critical blockers

| Priority | Blocker | Evidence | Release consequence |
| --- | --- | --- | --- |
| Critical | Two valid private keys are tracked and included in an image | `audit/security-and-secrets.md` | Public release would redistribute usable key material |
| Critical | Main README contains scientific claims not fully supported by archival evidence | `audit/scenario-status.md` | Manuscript and README claims are not traceable |
| Critical | No public anonymized evidence package exists | Only ignored `runs/` and live container logs exist | Reviewers cannot reproduce or inspect evidence safely |
| Critical | Main README is Spanish-only | `README.md` | Does not satisfy the requested English-first SoftwareX repository structure |
| High | No CI exists | No `.github/` tree | Passing local tests are not independently reproducible |
| High | No release metadata or single version source exists | Backend/frontend are `0.1.0`; latest tag is `v0.7.0-*` | `v1.0.0` cannot be asserted consistently |
| High | Python dependencies are unpinned | `backend/requirements*.txt` | Clean-environment reproduction is not deterministic |
| High | Most base and scenario images are not digest pinned | Dockerfiles, Compose, image catalog | Image rebuilds/pulls are mutable |
| High | No SBOM or complete license inventory exists | Only partial notices and real-IMS provenance | Redistribution and dependency review are incomplete |
| High | No manuscript or March 2026 template work product exists | No `paper/softwarex/` | Submission package is absent |

## Release v1.0.0 gaps

| Requirement | Current state | Status |
| --- | --- | --- |
| Clean release tree | Pre-existing modified `README.md`; new audit files after this phase | `FAIL` |
| Semantic version source | No project-level source; backend/frontend `0.1.0` | `FAIL` |
| `v1.0.0` tag | Absent | `FAIL` |
| Changelog | Absent | `FAIL` |
| Release notes | Absent | `FAIL` |
| Release policy | Absent | `FAIL` |
| Signed/annotated tag procedure | Absent | `FAIL` |
| CI at target commit | Absent | `FAIL` |
| All available local tests | Passing in this audit | `PASS` |
| Compose validation | 10 source manifests and 2 local overlays pass | `PASS` |
| Secret-free tracked tree | Two private keys and operational-looking values found | `FAIL` |
| Immutable dependencies | Partial only | `FAIL` |
| Public evidence | Absent | `FAIL` |

## Required public repository structure

| File/document | Current state |
| --- | --- |
| English `README.md` | Missing; current README is Spanish |
| `README.es.md` | Missing |
| `LICENSE` | Present, MIT |
| `Licence.txt` | Missing |
| `CITATION.cff` | Missing |
| `codemeta.json` | Missing |
| `CHANGELOG.md` | Missing |
| `CONTRIBUTING.md` | Missing |
| `SECURITY.md` | Missing |
| `SUPPORT.md` | Missing |
| `CODE_OF_CONDUCT.md` | Missing |
| `GOVERNANCE.md` | Missing |
| `AUTHORS.md` | Missing |
| `THIRD_PARTY_NOTICES.md` | Present but incomplete |
| Safe environment examples | Present, but some public defaults need clearer labeling |
| Versioning policy | Missing |
| Release policy | Missing |
| Installation guide | Present, Spanish and partially stale |
| User guide | Distributed across Spanish docs; incomplete |
| Developer guide | Missing as a coherent document |
| Experimental reproduction guide | Partial; no public dataset/protocol bundle |
| Troubleshooting guide | Present |
| API documentation | Partial and stale |
| Architecture documentation | Present but stale |
| Compatibility matrix | Missing |
| Scenario matrix | README only; evidence/provenance incomplete |
| Limitations statement | Present in README, but mixed with unsupported claims |
| RF safety guide | Present |
| Artifact inventory | This audit is the first explicit inventory |

## Scientific evidence gaps

| Scientific claim | Evidence state | SoftwareX gap |
| --- | --- | --- |
| 5G SA software | Strong simulation evidence at ancestor commits | Re-run exact release commit and publish sanitized artifacts |
| LTE software | Passing evidence without commit | Re-run with complete provenance |
| IMS simulation | Passing signaling evidence without commit | Re-run with complete provenance and clarify Digest vs AKA/Cx |
| 5G VoNR simulation | Passing runs have invalid/missing commit provenance | Re-run and publish exact release evidence |
| Commercial UE LTE/data | Partial local logs | Create one correlated, anonymized run with commit and metrics |
| Real IMS AKA/Cx/Rx registration | Markers exist only in mutable live logs; recent status is warning | Persist a correlated validation artifact or narrow the claim |
| Post-registration SIP methods | Required set not found; no archival artifact | Remove/narrow claim unless new evidence is preserved |
| 5G NSA | Control-plane observations, no stable NR user plane | Keep partial status; publish sanitized control-plane evidence and negative outcomes |
| Complete VoLTE call | Not demonstrated | Preserve limitation; do not imply successful call |
| Commercial UE 5G SA | Not demonstrated | Preserve limitation |
| Real-radio VoNR | Not demonstrated | Preserve limitation |

There are no quantitative public results for latency, throughput, packet loss,
stability, deployment duration, or reproducibility across hosts. Such metrics
must not be invented. Existing private logs may be used only after controlled
anonymization and provenance review.

## Reproducibility gaps

- Python packages have no versions, hashes, or lockfile.
- Standard Docker base images use mutable tags.
- Open5GS, UERANSIM, srsRAN 4G, UHD, and Kamailio use source tags without fixed commits.
- APT package versions and repository snapshots are not pinned.
- Standard scenario MongoDB and MariaDB images are mutable tags.
- Published `gually/*` image references use tags, not digests.
- Real IMS base images are digest pinned, but derived outputs are not.
- RTPengine setup downloads from a mutable `latest` repository path.
- No authoritative environment specification exists for release experiments.
- Most run records omit commit, environment, command, or terminal status.
- Generated real-IMS runtime overlays are not reconstructable from static
  source alone without running preparation code.
- No clean-clone CI verifies documented installation and commands.

## Licensing and SBOM gaps

The project MIT license is present. Imported real-IMS configuration has a
recorded BSD-2-Clause provenance chain. These are positive foundations, but the
release audit remains incomplete:

- `Licence.txt` required by the target submission package is absent.
- Python and npm dependency licenses are not inventoried.
- Base image and OS package licenses are not inventoried.
- Notices omit license details for several named dependencies.
- One Open5GS OCI label conflicts with the aggregate notice wording.
- Non-real-IMS templates and the UHD patch lack a comparable provenance record.
- Two tracked upstream private keys must be removed and rotated.
- No CycloneDX or SPDX SBOM exists.
- `syft`, `trivy`, and equivalent generation tools were unavailable in this audit.

License compatibility for redistributed AGPL/GPL images and combined artifacts
requires explicit legal review. This audit does not infer compatibility.

## CI gaps

No GitHub Actions workflow exists. A release CI must be entirely hardware-free
and must not receive laboratory secrets. Missing automated gates include:

- Backend tests and coverage threshold.
- Frontend tests, type checking, and production build.
- Shell and Dockerfile lint.
- YAML/JSON validation with an explicit exception for the malformed fixture.
- All source Compose model checks using example environments.
- Internal-link and required-file checks.
- `CITATION.cff`, CodeMeta, and version consistency validation.
- Secret scanning of the current tree and history.
- Dependency/SBOM generation or verification.
- Public result schema and anonymization validation.
- One unified `make softwarex-check` entry point.

## SoftwareX package gaps

The requested SoftwareX package does not exist. Missing artifacts include:

- `paper/softwarex/manuscript.md` using the five mandatory sections.
- Official metadata table C1-C8.
- Approximately 100-word abstract and no more than six keywords.
- Three to five highlights within 85 characters each.
- Cover letter.
- Declarations and author information.
- Submission checklist and reviewer self-assessment.
- Verified bibliography.
- Reproducible figures, captions, and editable sources.
- Supplementary materials.
- Optional video script/storyboard/checklist.

Author names, affiliations, corresponding email, ORCID, funding, conflicts,
acknowledgements, CRediT roles, and DOI are not inferable and must remain
explicit placeholders until confirmed by the authors.

The README references general SoftwareX guidance but does not establish that
the official Original Software Publication template dated 2026-03-06 has been
used. Its own summary of abstract and keyword limits may not match the target
template supplied in the release brief and requires source verification.

## Metadata and DOI gaps

| Metadata item | State |
| --- | --- |
| C1 current code version | Inconsistent (`0.1.0` in app metadata; target `1.0.0`) |
| C2 permanent GitHub version link | Provisional URL possible, but tag absent |
| C3 legal code license | MIT present |
| C4 version control | Git present |
| C5 languages/tools/services | Can be derived; not in official table |
| C6 environment/dependencies | Partial and not immutable |
| C7 developer documentation/manual | Partial |
| C8 support email | Unknown |
| `CITATION.cff` | Missing |
| CodeMeta | Missing |
| GitHub release | Not created |
| Zenodo deposit | Not created |
| DOI | Not created and must not be invented |

A definitive DOI requires a public immutable release followed by archival
deposit. It cannot be completed during repository preparation alone.

## Documentation quality gaps

Several documents predate implemented functionality. Examples include VoNR,
configuration generation, the web application, backend/frontend surface, and
one UHD version. The README also states that versioned configuration does not
publish subscriber/network/RF values, while tracked profiles contain concrete
valid-shaped values. Documentation must be reconciled with implementation and
the security audit before translation.

## Gap-analysis result

The repository has a functioning and tested software base, but the scientific
release and journal package are incomplete. The project must remain in an
audit/preparation state until the critical blockers and explicit release gates
in `audit/proposed-changes.md` are resolved.
