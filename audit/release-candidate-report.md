# Release-Candidate Report

## Candidate Identity

| Item | Value |
| --- | --- |
| Branch | `release/softwarex-v1.0.0` |
| Version | `1.0.0-rc.1` |
| Historical audit base | `c3247c99b6c969189efe9e57a46f110c88c26f4d` |
| Public-result source commit | `12c4a38404bbaf240c698a056e3f47182081ab5c` |
| Initial public-result artifact commit | `060e669d3f65e1844a702b1b5264be6933ef45c2` |
| Distribution boundary | Source-only candidate; no binary/image approval |
| Final tag, release, DOI, or article | Not created |

The initial public-result artifact commit is the direct child of the source
commit. It adds sanitized reports and does not represent another scenario
execution. The current candidate corrects the VoNR completion criterion from
`NOT_ASSESSED` to `NOT_MET` and refreshes the support-artifact hash; it does not
represent a rerun.

## Verdict

**Not ready for final or public release.** The current source candidate has
substantial security, reproducibility, test, CI-definition, and documentation
improvements. Final release remains blocked by reachable historical key
material, incomplete identity/contact metadata, absence of a hosted CI result,
and unresolved binary redistribution controls.

The branch may be reviewed locally as a source-only release candidate. It must
not be represented as `v1.0.0`, a SoftwareX publication, a complete SBOM, a
container redistribution approval, or end-to-end cellular/RF validation.

## Local Verification Evidence

Safe local checks executed during candidate preparation report:

| Check | Result | Scope boundary |
| --- | --- | --- |
| Backend tests | 262 passed, 1 dependency deprecation warning | Local candidate worktree; no RF, scenario start, hardware, or database integration |
| Backend line coverage | 77%: 2,989 statements, 692 missed | No configured minimum threshold |
| Frontend tests | 42 passed | Frontend coverage is not configured |
| Frontend type check | Passed | Static TypeScript scope |
| Frontend production build | Passed | Build success is not deployment validation |
| Unified safe checks | `make softwarex-check` passed | Hardware-free; offline where supported; no scenario or RF start |

The dependency warning is the documented Starlette `TestClient`/HTTPX
deprecation. It does not fail the current tests but remains technical debt.
Hosted GitHub Actions evidence does not exist for this unpushed local branch.

The unified run also passed 81 Python, 99 shell, 89 YAML, and 26 JSON source
format checks; 11 safe Compose models; four software profiles; three expected
fail-closed RF profiles; 121 local links across 59 Markdown files; current-tree
sensitive-file checks; version, citation, CodeMeta, and partial-SBOM checks; and
all four public-result records plus their support artifacts.

## Release Gates

| Gate | State | Evidence or reason |
| --- | --- | --- |
| Single version `1.0.0-rc.1` | `PASS` locally | `VERSION` and release metadata verifier |
| Current-tree key removal/runtime generation | `PASS` locally | Security commit and regression tests |
| Approved history without known keys | `FAIL` | Removed keys remain in reachable pre-remediation commits |
| Current-tree sensitive-file scan | `PASS` locally | Custom scanner; not a full-history substitute |
| Non-mutating RF dry run | `PASS` locally | Static and sandbox regression tests |
| Base application least privilege | `PASS` locally | Loopback/read-only/no-socket default and two-part mutation opt-in |
| Backend/frontend checks | `PASS` locally | Counts and coverage above |
| Hosted CI at candidate commit | `PENDING` | Workflow exists, but branch was not pushed |
| Compose/profile/source-format checks | `PASS` in latest local unified run | Parsing and static behavior only |
| Public-result schema and redaction | `PASS` locally | Three passing summaries and one blocked attempt |
| Independently reviewable scenario evidence | `PARTIAL` | Public artifacts omit raw correlated evidence and complete runtime context |
| First-party/source legal files | `PASS` for source scope | MIT and imported BSD provenance retained |
| Binary/container redistribution | `FAIL` | Build provenance, final-image SBOMs, notices, and source delivery are incomplete |
| Complete release SBOM | `FAIL` | Current CycloneDX artifact is intentionally partial |
| Confirmed author/publication metadata | `FAIL` | Identities and declarations require direct confirmation |
| Private security and conduct channels | `FAIL` | Maintainer-owned channels and targets are absent |
| SoftwareX article package | `FAIL` | Manuscript and submission package do not exist |
| RF/hardware validation | `NOT_TESTED` | Deliberately outside this source-candidate task |

## Public Scenario Boundary

The [canonical capability table](../README.md#canonical-capability-status) is
the sole current scenario classification matrix. This report does not restate
it. The public set consists of three passing software-validator summaries and
one blocked VoNR attempt. Those reports do not claim independent protocol-trace
review, RF behavior, commercial-UE behavior, conformance, performance,
multi-host reproducibility, or production suitability.

## Blocking Findings

1. **Known keys in history:** final publication requires an approved history
   and rotation decision. Rewriting a shared history changes every descendant
   commit identifier and requires coordinated remapping of evidence.
2. **Binary provenance and compliance:** catalogued registry digests are not
   bound to current source by build attestations. Final-image inventories,
   notices, Corresponding Source delivery, and several license details remain
   incomplete.
3. **Unconfirmed governance metadata:** authors, affiliations, ORCIDs, contact,
   support ownership, funding, conflicts, and publication roles cannot be
   inferred from Git activity.
4. **No private reporting channel:** vulnerability and conduct policies have no
   monitored private destination or confirmed response target.
5. **No hosted candidate CI:** a safe workflow exists, but this local branch has
   not produced an independently visible CI run.
6. **Scientific evidence boundary:** public summaries are useful regression
   artifacts but omit the correlated sanitized evidence needed for stronger
   protocol or end-to-end claims.
7. **Incomplete SBOM/reproducibility:** image filesystems, OS packages, Python
   transitive artifacts/hashes, and snapshot-pinned APT inputs are absent.
8. **VoNR remains blocked:** no positive VoNR software or RF conclusion follows
   from the timed-out attempt or historical containers.

## Prohibited Release Claims

Until the blocking findings are resolved, do not claim:

- final `v1.0.0`, DOI-backed archival release, or SoftwareX publication;
- secret-free approved Git history;
- reproducible or legally complete project container images;
- a complete release/container SBOM;
- end-to-end VoLTE or VoNR, stable NR user plane, commercial-UE 5G SA, or RF
  validation;
- performance, conformance, production readiness, or multi-host reproduction.

## Decision

Keep `1.0.0-rc.1` unreleased and local until maintainer review. The next safe
work is administrative, documentary, CI, history, and legal provenance work.
No RF execution, hardware access, firmware/FPGA operation, final tag, push, or
publication is authorized by this report.
