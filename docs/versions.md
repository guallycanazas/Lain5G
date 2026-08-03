# Versions and traceability

The authoritative OpenLain5G version is stored in `VERSION`. The current stable
release is `1.1.1`. The API, frontend, OCI tags, derived images, and changelog
are checked against that source with:

```bash
make version-check
```

The complete matrix, evidence sources, platforms for each manifest, and
unresolved risks are documented in `docs/reproducibility/version-matrix.md`.
The update policy is documented in
`docs/reproducibility/dependency-policy.md`.

## Software components

| Component | Human-readable ref | Immutable commit |
| --- | --- | --- |
| Open5GS | `v2.7.5` | `7dfd9a39649700c24c22f1978ed7a35541a72cca` |
| UERANSIM | `v3.2.6` | `384636f4fcf46b8c86109790ff3e2cd242b53556` |
| srsRAN 4G | `release_23_11` | `eea87b1d893ae58e0b08bc381730c502024ae71f` |
| srsRAN Project | `release_24_10_1` | `ef4b0749a12a3b1a8347ae01c937a621603b4069` |
| UHD | `v4.10.0.0` | `2af4ddb96219a99d2300804830e0971f79557b23` |
| Kamailio | `5.8.8` | `053181eb9c3136836cb272584b582484a9a11b48` |

Tags are retained for human readability, but each Dockerfile downloads, checks
out, and verifies the full commit. CoreDNS `1.11.3`, MongoDB, MariaDB, and all
Dockerfile base images are pinned by manifest digest.

Published images in the `gually/lain5g-*` catalog are pinned by digest and
currently provide Linux/amd64 only. Multi-platform index digests are retained
for official base images when provided by the registry; this does not claim that
the project's own software has been tested on all those architectures.

## Application dependencies

- Python: exact direct requirements in `backend/requirements*.txt` and exact
  runtime/development resolution in `backend/constraints.txt`.
- Frontend: dependency resolution and integrity hashes in
  `frontend/package-lock.json`; install with `npm ci` through
  `make frontend-install`.
- Real IMS: base images and derived tags in
  `deployments/ims-real/images.lock.yaml`.

## Reproducibility limitations

The APT repositories used during builds are not snapshots. Therefore, system
packages may change even when the base image and source code are pinned.
RTPengine uses the verified `26.0` channel and validates the keyring checksum,
but that channel may still receive architecture-specific revisions.

The local `lain5g-lab/open5gs:local` image contains the EPC binaries
`open5gs-mmed`, `open5gs-hssd`, `open5gs-sgwcd`, `open5gs-sgwud`,
`open5gs-pcrfd`, `open5gs-smfd`, and `open5gs-upfd`. Open5GS `v2.7.5` does not
install `open5gs-pgwcd` or `open5gs-pgwud`; the 4G `pgwc` and `pgwu` services run
`open5gs-smfd` and `open5gs-upfd`.

Before publishing results, archive the OpenLain5G commit, the output of
`make version-check`, the build arguments, and `docker image inspect` for each
final image. A `:local` tag does not replace the image digest or an artifact
archived with the release.
