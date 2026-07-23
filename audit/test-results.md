# Lain5G-Lab Audit Test Results

This is a historical test report for audited commit
`c3247c99b6c969189efe9e57a46f110c88c26f4d` on 2026-07-22. The 149 backend and
42 frontend results below must not be presented as current candidate-commit
evidence. Current classifications and evidence scopes are maintained in the
[canonical capability table](../README.md#canonical-capability-status).

Post-audit note: the new public scenario artifacts evaluate source commit
`12c4a38404bbaf240c698a056e3f47182081ab5c` and were initially added in
artifact publication commit `060e669d3f65e1844a702b1b5264be6933ef45c2`.
The current candidate later corrects the VoNR completion outcome without a
rerun. A later local candidate-worktree run reports 262 backend tests, 77%
backend line coverage, 42 frontend tests, and a passing frontend build. Hosted
CI and frontend coverage are not claimed. See
[release-candidate-report.md](release-candidate-report.md). These later facts do
not alter the commands or findings recorded in this historical report.

## Scope and safety controls

All executed checks were non-transmitting and non-destructive. No scenario was
started, no RF command was executed, no firmware or FPGA operation was run, no
MongoDB write was performed, and no Git or publication operation was performed.
Coverage and frontend build output were redirected under `/tmp/opencode`.

Status vocabulary:

| Status | Meaning |
| --- | --- |
| `PASS` | The command ran and met its stated criterion |
| `FAIL` | The command ran and did not meet its criterion |
| `WARNING` | The check completed but exposed a limitation or non-release condition |
| `SKIPPED` | The check was intentionally not run |
| `NOT_TESTED` | No suitable safe automated check was available |

## Environment

| Tool/environment | Detected version |
| --- | --- |
| Operating system | Ubuntu 26.04 LTS |
| Kernel | Linux 7.0.0-27-generic, x86_64 |
| Logical CPUs | 8 |
| RAM | 9.6 GiB |
| Git | 2.53.0 |
| Bash | 5.3.9 |
| GNU Make | 4.4.1 |
| Python | 3.14.4 from `.venv` |
| pytest | 9.1.1 |
| Node.js | 22.22.1 |
| npm | 9.2.0 |
| Docker client/server | 29.1.3 |
| Docker Compose | 2.40.3 |
| jq | 1.8.1 |

`shellcheck`, `hadolint`, `yamllint`, `gitleaks`, `trivy`, and `syft` were not
installed.

## Result summary

| Check | Status | Exact result |
| --- | --- | --- |
| Backend baseline | `PASS` | 149 passed, 1 warning, 5.10 s |
| Backend coverage run | `PASS` | 149 passed, 1 warning, 5.91 s; 77% total |
| Frontend tests | `PASS` | 11 files, 42 tests, 14.30 s |
| Frontend type check | `PASS` | `tsc --noEmit --incremental false` |
| Frontend production build | `PASS` | 1,700 modules; 5.40 s |
| Shell syntax | `PASS` | 97 tracked shell files |
| Python syntax | `PASS` | 63 modules plus `lain5g` |
| JavaScript syntax | `PASS` | 4 tracked JavaScript files |
| YAML syntax | `PASS` | 87 tracked YAML/YML files |
| JSON syntax, production/examples | `PASS` | 13 files |
| Expected-invalid JSON fixture | `WARNING` | One deliberate malformed test fixture |
| Source Compose models | `PASS` | 10 of 10 |
| Existing real-IMS runtime overlays | `PASS` | 2 of 2 |
| Non-RF profile validation | `PASS` | 4 of 4 |
| RF guard rejection | `PASS` | 3 of 3 rejected as expected |
| Static scenario tests | `PASS` | 34 cases included in backend result |
| Real IMS source preflight | `PASS` | 4G and 5G, 5 checks each |
| Real IMS start plans | `PASS` | 4G/5G returned `DRY_RUN`, no RF |
| Real IMS image plan | `PASS` | Six commands planned, none executed |
| Internal Markdown links | `PASS` | 32 tracked Markdown files, zero broken |
| README file references | `PASS` | 35 checked, zero missing |
| External SoftwareX URL | `WARNING` | HTTP 403 from automated request |
| Dockerfile lint | `SKIPPED` | `hadolint` unavailable |
| Shell lint | `SKIPPED` | `shellcheck` unavailable |
| YAML style lint | `SKIPPED` | `yamllint` unavailable |
| Standard secret scanner | `SKIPPED` | `gitleaks` unavailable; safe custom scan used |
| SBOM generation | `SKIPPED` | `syft` and `trivy` unavailable |
| RF/hardware tests | `SKIPPED` | Explicitly prohibited for this audit |
| Real database integration | `SKIPPED` | Would mutate MongoDB/IMS state |

## Backend baseline

Command pattern:

```bash
audit_tmp=$(mktemp -d "/tmp/opencode/lain5g-backend.XXXXXX")
HOME="$audit_tmp/home" \
XDG_CACHE_HOME="$audit_tmp/cache" \
TMPDIR="$audit_tmp" \
PYTHONDONTWRITEBYTECODE=1 \
.venv/bin/pytest \
  -p no:cacheprovider \
  --basetemp="$audit_tmp/pytest" \
  backend/tests
```

Result:

```text
collected 149 items
149 passed, 1 warning in 5.10s
```

The warning is a `StarletteDeprecationWarning` stating that the current use of
`httpx` with `starlette.testclient` is deprecated and recommending `httpx2`.

The 34 static scenario/package cases all passed. They cover LTE simulation,
4G VoLTE packaging, 5G VoNR packaging, 5G X-Series safeguards, 5G NSA
safeguards, and real IMS provenance/packaging.

## Backend coverage

Command pattern:

```bash
audit_tmp=$(mktemp -d "/tmp/opencode/lain5g-coverage.XXXXXX")
HOME="$audit_tmp/home" \
XDG_CACHE_HOME="$audit_tmp/cache" \
TMPDIR="$audit_tmp" \
PYTHONDONTWRITEBYTECODE=1 \
COVERAGE_FILE="$audit_tmp/.coverage" \
.venv/bin/pytest \
  -p no:cacheprovider \
  --basetemp="$audit_tmp/pytest" \
  --cov=backend/app \
  --cov-report=term-missing \
  backend/tests
```

Exact total:

```text
TOTAL 2739 statements, 636 missed, 77% coverage
149 passed, 1 warning in 5.91s
```

Lowest major service coverage:

| Module | Coverage |
| --- | ---: |
| `real_ims_service.py` | 39% |
| `open5gs_connection_service.py` | 59% |
| `deployment_service.py` | 60% |
| `dependencies.py` | 71% |
| `pyhss_service.py` | 73% |
| `preparation_service.py` | 75% |
| `subscriber_service.py` | 76% |

There is no configured minimum coverage threshold.

## Frontend tests and build

Tests used the installed lockfile-resolved dependencies and disabled Vitest
cache. TypeScript and Vite output were directed away from the repository.

Command pattern:

```bash
audit_tmp=$(mktemp -d "/tmp/opencode/lain5g-frontend.XXXXXX")
HOME="$audit_tmp/home" XDG_CACHE_HOME="$audit_tmp/cache" TMPDIR="$audit_tmp" \
  ./node_modules/.bin/vitest run --environment jsdom --no-cache

./node_modules/.bin/tsc \
  --project tsconfig.json \
  --noEmit \
  --incremental false
```

The production build was invoked through Vite's programmatic API with
`configFile: false`, a temporary cache, and a temporary output directory.

Exact results:

```text
Test Files  11 passed (11)
Tests       42 passed (42)
Duration    14.30s

vite v6.4.3 building for production
1700 modules transformed
index.html                 0.40 kB, gzip 0.27 kB
main CSS                  55.46 kB, gzip 11.70 kB
main JavaScript          485.07 kB, gzip 142.91 kB
built in 5.40s
```

No frontend coverage plugin or coverage command is configured.

## Syntax validation

Shell syntax:

```bash
git ls-files -z -- '*.sh' |
  while IFS= read -r -d '' file; do
    bash -n "$file" || exit
  done
```

Result: 97 of 97 tracked shell files passed Bash parsing.

Python syntax was checked with `ast.parse` and
`PYTHONDONTWRITEBYTECODE=1`. Result: 64 of 64 files passed.

JavaScript syntax was checked with `node --check`. Result: 4 of 4 files passed.

YAML was parsed with `yaml.safe_load_all`. Result: 87 of 87 files passed.

JSON was parsed with Python's standard parser. Thirteen production, example,
lock, and provenance JSON files passed. The following file failed by design:

```text
backend/tests/fixtures/runs/run-invalid/metadata.json:4:1
```

It is an intentionally malformed fixture used to test invalid run handling,
not a production configuration defect.

## Docker Compose validation

All source manifests were checked with `docker compose config --quiet
--no-env-resolution` and safe example/default environment files. This avoided
printing or resolving private service environment values.

| Manifest | Profiles | Status |
| --- | --- | --- |
| `docker-compose.app.yml` | default | `PASS` |
| `deployments/4g-lte-sim/docker-compose.yml` | default | `PASS` |
| `deployments/4g-volte/sim/docker-compose.yml` | `sip` | `PASS` |
| `deployments/4g-volte/x310/docker-compose.yml` | `rf`, `webui` | `PASS` |
| `deployments/5g-sa/docker-compose.yml` | default | `PASS` |
| `deployments/5g-sa-x310/docker-compose.yml` | `rf` | `PASS` |
| `deployments/5g-nsa-x310/docker-compose.yml` | `rf` | `PASS` |
| `deployments/5g-vonr/docker-compose.yml` | `sip` | `PASS` |
| `deployments/ims-real/compose.4g.yaml` | default | `PASS` |
| `deployments/ims-real/compose.5g.yaml` | default | `PASS` |

The two existing ignored real-IMS runtime override combinations also passed.
Those generated layers are host-specific and are not available in a clean
checkout until runtime preparation occurs.

Compose parsing does not semantically validate Open5GS, srsRAN, Kamailio,
CoreDNS, SQL, UHD, network timing, or RF behavior.

## Profile and dry-run validation

These non-RF profiles passed `./lain5g profile validate`:

- `4g-lte-sim`
- `4g-volte-sim`
- `5g-sa`
- `5g-vonr`

These RF profiles failed validation as expected because committed safety state
does not authorize operation:

- `4g-lte-x310`
- `5g-sa-x310`
- `5g-nsa-x310`

The common failures require explicit authorization and an operator note. The
NSA profile additionally requires explicit declarations for its second RF path
and authorized laboratory frequencies. No operational value was printed.

GNU Make's own `--dry-run` safely confirmed recipe routing for software starts,
RF starts, and application start without executing recipes. It printed only
the selected script or Compose command.

Real IMS checks returned:

| Command | Result |
| --- | --- |
| `scripts/ims_real.py preflight --mode 4g` | 5 of 5 checks `PASS` |
| `scripts/ims_real.py preflight --mode 5g` | 5 of 5 checks `PASS` |
| `scripts/ims_real.py start --mode 4g` | `DRY_RUN`, `executed=false`, `rf_started=false` |
| `scripts/ims_real.py start --mode 5g` | `DRY_RUN`, `executed=false`, `rf_started=false` |
| `scripts/ims_real.py images` | Six image commands planned, none executed |

Some scenario-specific `LAIN5G_DRY_RUN=true` scripts were not executed because
static inspection showed that they can create run artifacts, remove RF marker
files, start diagnostic containers, or inspect and print operational RF data.
In particular, the NSA RF start script does not honor `LAIN5G_DRY_RUN` at all.

## Documentation checks

All formal relative Markdown links in the 32 pre-audit tracked Markdown files
resolved. Thirty-five principal paths referenced by the root README existed.

The only formal external URL in the README, the official SoftwareX guide,
returned HTTP 403 to an automated request. This is recorded as a warning, not
proof that the browser-facing page is absent.

Static review found documentation drift despite link integrity:

- VoNR documents describe the scenario as future work although code exists.
- Configuration documentation says no generator exists although profiles can be applied.
- Third-party and architecture documents describe the implemented web app as future work.
- One UHD image README documents an older version than its Dockerfile.
- Backend/frontend guides omit significant current API and UI surface.

## Scientific evidence checks

Safe metadata-only parsers examined run status, scenario name, commit field,
validation status, and marker presence. They never printed subscriber values,
credentials, private addresses, hardware serials, or RF plans.

Observed run corpus:

| Scenario | Metadata records | Validations | All-pass validations | Records with commit |
| --- | ---: | ---: | ---: | ---: |
| `4g-lte-sim` | 6 | 6 | 3 | 0 |
| `4g-lte-x310` | 85 | 6 | 0 | 0 |
| `4g-volte-sim` | 8 | 8 | 2 | 0 |
| `5g-sa` | 20 | 20 | 8 | 10 |
| `5g-vonr-sim` | 10 | 10 | 3 | 4 |

NSA logs are not accompanied by normal run metadata or validation files. One
root-owned metadata file was not readable and is `NOT_TESTED`.

## Checks not executed

| Check | Status | Reason |
| --- | --- | --- |
| RF starts for LTE, 5G SA, and NSA | `SKIPPED` | Prohibited; would transmit |
| UHD hardware checks | `SKIPPED` | Hardware access was outside read-only scope |
| 5G X-Series preflight scripts | `SKIPPED` | Some start diagnostic containers or expose private RF data |
| Firmware/FPGA checks or updates | `SKIPPED` | Explicitly prohibited |
| Simulation deployment starts | `SKIPPED` | Would create/alter containers, networks, volumes, and run evidence |
| Subscriber integration test | `SKIPPED` | Would mutate Open5GS MongoDB |
| Real IMS provisioning with `--execute` | `SKIPPED` | Would mutate pyHSS/Open5GS state |
| Full Docker image builds | `SKIPPED` | Not required for source audit; network and build state mutation |
| Image vulnerability scan | `SKIPPED` | `trivy` unavailable |
| SBOM generation | `SKIPPED` | `syft` and `trivy` unavailable |
| Full external-link crawl | `SKIPPED` | No link-checker installed; only README URL checked |

## Test conclusion

At the audited commit, the available backend tests, frontend tests, frontend
build, syntax checks, and Compose model checks passed. This did not make the
project release ready because critical security, provenance, evidence,
versioning, CI, SBOM, and editorial gaps remained. This document is a
historical audit result only.
