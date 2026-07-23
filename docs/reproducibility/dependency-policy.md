# Dependency Policy

## Release Authority

The repository-root `VERSION` file is the authoritative Lain5G-Lab release
version. Backend API metadata reads that file at runtime. Frontend package,
lockfile, UI fallback, OCI labels, changelog, documentation, and derived image
tags are synchronized copies checked by:

```bash
make version-check
```

The check is offline and read-only. It fails on version contradictions, direct
Python requirements without exact versions, constraints mismatches, empty Git
commit arguments, unpinned Docker bases, unpinned third-party Compose images,
mutable `latest` image/URL policy references, and Real-IMS tag drift.

## Python

`backend/requirements.txt` and `backend/requirements-dev.txt` contain only
direct dependencies and use exact `==` versions. `backend/constraints.txt`
contains the exact runtime and development closure observed in the tested
Python 3.14.4 virtual environment, including pip 25.1.1. It intentionally does
not contain fabricated package hashes.

Create the release environment with:

```bash
make backend-install
.venv/bin/python -m pip check
make backend-test
```

The install command consumes both direct requirement files and the constraints
file. To refresh dependencies, use a clean temporary virtual environment,
install the reviewed direct versions, capture `python -m pip freeze --all`,
replace the constraints file, and run all backend tests. Do not call a new
closure tested until its exact output and interpreter version are recorded in
the version matrix.

The backend container uses the same runtime requirements and constraints, but
its pinned Python 3.12 base is a separate interpreter target. A local Python
3.12 container build was not executed for this candidate.

## JavaScript

`frontend/package-lock.json` is the transitive dependency lock and retains npm
registry integrity hashes. Release and developer install commands use:

```bash
make frontend-install
```

This runs `npm ci`; it must not rewrite the lock. Changes to `package.json`
require a separately reviewed lockfile refresh, followed by `npm ci`, frontend
tests, and a production build. The release version is changed in only the root
package records; transitive package metadata remains untouched.

For this candidate, `npm audit --omit=dev` reports zero findings. A full audit
reports five findings in the locked Vitest/Vite development path. The available
automatic fix is a semver-major Vitest update, so it is documented as a release
limitation rather than applied without a dedicated compatibility review.

## Git Sources

Human-readable upstream tags are retained for traceability, but every source
build checks out a full commit and verifies `git rev-parse HEAD`. Resolve an
updated tag using the authoritative repository, including the peeled `^{}` ref
for annotated tags:

```bash
git ls-remote --tags UPSTREAM_URL refs/tags/TAG refs/tags/TAG^{}
```

Never infer or shorten a commit. Record the command result and source URL in
`docs/reproducibility/version-matrix.md` before changing a Docker build arg.

## Containers

Dockerfile bases use registry manifest digests. Multi-platform index digests
are preferred so digest pinning does not silently force one CPU architecture.
When a registry publishes only one platform, the limitation must be explicit
in the version matrix. Compose uses digests for MongoDB and MariaDB. Local
`:local` names are deliberate aliases for first-party images; the downloadable
catalog source behind each alias is digest-pinned.

Verify a proposed digest from the registry manifest and its authoritative tag
API before changing it. A digest is not accepted solely because it resembles a
SHA-256 value.

## System Packages

Base filesystem digests do not lock packages later selected by `apt-get`.
Ubuntu, Debian, Docker, Redis, and RTPengine package repositories are not
snapshot-pinned in this candidate. Rebuilding at another time can therefore
select different OS packages. This is a known reproducibility boundary, not an
architecture-neutral lock.

RTPengine uses the verified `26.0` release channel instead of the mutable
`latest` path. The repository keyring is checked against SHA-256
`78fe26f0251138f4e3c749c88dc4df29666c8efe0823858d3a4ab49d2fa2e088`.
The channel itself can still publish newer `26.0` package revisions; complete
reproduction requires archiving the resolved package set or adopting a trusted
snapshot repository.

## Release Gate

The minimum non-operational release gate is:

```bash
make version-check
.venv/bin/python -m pip check
.venv/bin/pytest backend/tests/test_release_metadata.py backend/tests/test_health.py
cd frontend && npm ci && npm test && npm run build
```

Compose and Dockerfile static validation must also pass. Scenario, RF, hardware,
and database tests are separate evidence-producing activities and are never
implied by this dependency gate.
