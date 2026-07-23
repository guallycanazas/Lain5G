# Version Matrix

## Release

| Item | Exact value | Authority |
| --- | --- | --- |
| Lain5G-Lab | `1.0.0-rc.1` | Root `VERSION` |
| Status | Unreleased release candidate | `CHANGELOG.md` |
| Evidence captured | `2026-07-23T04:30:11Z` | Local UTC clock during verification |
| Verification host | Linux `x86_64` | `uname -m` |
| Python test environment | CPython `3.14.4`, pip `25.1.1` | `.venv/bin/python --version`, `.venv/bin/pip --version` |
| Node/npm environment | Node `v22.22.1`, npm `9.2.0` | `node --version`, `npm --version` |
| Docker tooling | Docker client `29.1.3`, Compose `2.40.3+ds1-0ubuntu1` | Local CLI version output |
| Dockerfile linter | Hadolint `v2.14.0`, linux/amd64 manifest `sha256:e9dbf5113239ef2bf696d20c8f28d3019a47c26a38c98b89344d3e2846c4d5f8` | Official `hadolint/hadolint` registry artifact |

## Source Builds

The following values were resolved with authoritative `git ls-remote --tags`
queries on 2026-07-23 UTC. Annotated tags use the peeled commit, not the tag
object.

| Component | Tag/ref | Exact checkout commit | Authoritative source |
| --- | --- | --- | --- |
| Open5GS | `v2.7.5` | `7dfd9a39649700c24c22f1978ed7a35541a72cca` | [open5gs/open5gs](https://github.com/open5gs/open5gs.git), tag object `b729f1050eaf73f5478e2c240109958a41060604` |
| UERANSIM | `v3.2.6` | `384636f4fcf46b8c86109790ff3e2cd242b53556` | [aligungr/UERANSIM](https://github.com/aligungr/UERANSIM.git) |
| srsRAN 4G | `release_23_11` | `eea87b1d893ae58e0b08bc381730c502024ae71f` | [srsran/srsRAN_4G](https://github.com/srsran/srsRAN_4G.git) |
| UHD | `v4.10.0.0` | `2af4ddb96219a99d2300804830e0971f79557b23` | [EttusResearch/uhd](https://github.com/EttusResearch/uhd.git), tag object `d800f9b031bd058dd2403a5da66354d9d3e5576c` |
| Kamailio | `5.8.8` | `053181eb9c3136836cb272584b582484a9a11b48` | [kamailio/kamailio](https://github.com/kamailio/kamailio.git), tag object `920c380101652ce2772d9e999c69a2cf83592f6e` |
| srsRAN Project | `release_24_10_1` | `ef4b0749a12a3b1a8347ae01c937a621603b4069` | [srsran/srsRAN_Project](https://github.com/srsran/srsRAN_Project.git) |
| Real-IMS configuration source | commit | `3685b58aa0c7c28b2fecc6b9533f128285bf8dda` | [GitHub commit API](https://api.github.com/repos/herlesupreeth/docker_open5gs/commits/3685b58aa0c7c28b2fecc6b9533f128285bf8dda), verified GitHub signature |

## Dockerfile Bases

Docker Hub tag evidence came from the linked tag APIs; each selected digest was
also accepted by `docker manifest inspect IMAGE@sha256:...`. Platform lists
exclude `unknown/unknown` attestations.

| Input | Locked digest | Verified manifest platforms | Evidence |
| --- | --- | --- | --- |
| `python:3.12-slim` | `sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de` | linux/amd64, arm/v5, arm/v7, arm64/v8, 386, ppc64le, riscv64, s390x | [Docker Hub tag API](https://hub.docker.com/v2/repositories/library/python/tags/3.12-slim) |
| `node:22-alpine` | `sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2` | linux/amd64, arm/v6, arm/v7, arm64/v8, s390x | [Docker Hub tag API](https://hub.docker.com/v2/repositories/library/node/tags/22-alpine) |
| `nginx:1.27-alpine` | `sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10` | linux/amd64, arm/v6, arm/v7, arm64/v8, 386, ppc64le, riscv64, s390x | [Docker Hub tag API](https://hub.docker.com/v2/repositories/library/nginx/tags/1.27-alpine) |
| `ubuntu:22.04` / `ubuntu:jammy` | `sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982` | linux/amd64, arm/v7, arm64/v8, ppc64le, riscv64, s390x | [Docker Hub tag API](https://hub.docker.com/v2/repositories/library/ubuntu/tags/22.04) |
| `ubuntu:24.04` | `sha256:4fbb8e6a8395de5a7550b33509421a2bafbc0aab6c06ba2cef9ebffbc7092d90` | linux/amd64, arm/v7, arm64/v8, ppc64le, riscv64, s390x | [Docker Hub tag API](https://hub.docker.com/v2/repositories/library/ubuntu/tags/24.04) |
| `debian:bookworm-slim` | `sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818` | linux/amd64, arm/v5, arm/v7, arm64/v8, 386, mips64le, ppc64le, s390x | [Docker Hub tag API](https://hub.docker.com/v2/repositories/library/debian/tags/bookworm-slim) |
| `debian:bookworm` (vendored reference) | `sha256:9344f8b8992482f80cba753f323adeaf17690076c095ccff6cc9536be98185dc` | linux/amd64, arm/v5, arm/v7, arm64/v8, 386, mips64le, ppc64le, s390x | [Docker Hub tag API](https://hub.docker.com/v2/repositories/library/debian/tags/bookworm) |
| `coredns/coredns:1.11.3` | `sha256:9caabbf6238b189a65d0d6e6ac138de60d6a1c419e5a341fbbb7c78382559c6e` | linux/amd64, arm/v7, arm64, ppc64le, riscv64, s390x | [Docker Hub tag API](https://hub.docker.com/v2/repositories/coredns/coredns/tags/1.11.3) |
| Real-IMS RTPengine Debian base | `sha256:60eac759739651111db372c07be67863818726f754804b8707c90979bda511df` | Multi-platform Linux index, directly inspected | `deployments/ims-real/images.lock.yaml` and registry manifest |
| Real-IMS Open5GS base | `sha256:441d40e16f76ae79fc25eaaa92245850ed833bdd3d0d0dc78acbffd958cdc2c6` | linux/amd64 only | GHCR manifest inspection |
| Real-IMS Kamailio base | `sha256:67dc92b423ca5ef0b827a049d0cabeff741f3eafd9222608036494f4d7611821` | linux/amd64 only | GHCR manifest inspection |
| Real-IMS pyHSS base | `sha256:90206eb3cbe862bfa71e0bfaf038fe3ddbefba1df531eb2157c9642ac732e6fb` | linux/amd64 only | GHCR manifest inspection |
| Real-IMS MySQL base | `sha256:324d3d4c5089feea787684f0dbf1a646dde8d356170085ac0b6538aee6910057` | linux/amd64 only | GHCR manifest inspection |

## Compose Images

| Image role | Locked digest | Platforms observed | Evidence |
| --- | --- | --- | --- |
| MongoDB | `sha256:8b6d8f5bbedb25cb73517b65cf99f13aeb75ad5b157a56c479287a840bbad3ac` | linux/amd64, linux/arm64/v8; Windows manifests also present | Existing Real-IMS lock plus direct registry manifest inspection |
| MariaDB `11` capture | `sha256:efb4959ef2c835cd735dbc388eb9ad6aab0c78dd64febcd51bc17481111890c4` | linux/amd64, arm64/v8, ppc64le, s390x | [Docker Hub tag API](https://hub.docker.com/v2/repositories/library/mariadb/tags/11) |

## Registry Catalog Artifacts

These registry artifacts were verified by Docker Hub tag API and direct digest
manifest inspection. This proves registry availability, not that the bytes were
built from the source commits and current Dockerfiles in this matrix; no build
attestation was available. Every listed artifact is Linux/amd64-only. The local
`:local` tag is an alias created after pulling the exact registry digest.

| Local alias | Published tag and exact digest | Evidence |
| --- | --- | --- |
| `lain5g-lab/open5gs:local` | `gually/lain5g-open5gs:2.7.5-lain1@sha256:d25affe90c39adb35bfef312e725b27d2ef6b139ec1d8b2fe9f5d0da6d82753c` | [tag API](https://hub.docker.com/v2/repositories/gually/lain5g-open5gs/tags/2.7.5-lain1) |
| `lain5g-lab/ueransim:local` | `gually/lain5g-ueransim:3.2.6-lain1@sha256:1451cb0327f97fb276b30b78ec1c3ad54bbb480ec044004e580e62a20b60a8a2` | [tag API](https://hub.docker.com/v2/repositories/gually/lain5g-ueransim/tags/3.2.6-lain1) |
| `lain5g-lab/srsran4g-sim:local` | `gually/lain5g-srsran4g-sim:23.11-lain1@sha256:7ec771cf70e77f699283017b02bbe6311fd377047109dc952c2c18ebae1e2ced` | [tag API](https://hub.docker.com/v2/repositories/gually/lain5g-srsran4g-sim/tags/23.11-lain1) |
| `lain5g-lab/srsran4g-uhd:local` | `gually/lain5g-srsran4g-uhd:23.11-uhd4.10-lain1@sha256:8d8ed84133008b542e0db510d57a458049c1b6391e7fd557a81d03dde794cb2e` | [tag API](https://hub.docker.com/v2/repositories/gually/lain5g-srsran4g-uhd/tags/23.11-uhd4.10-lain1) |
| `lain5g-lab/srsranproject-uhd:local` | `gually/lain5g-srsranproject-uhd:24.10.1-uhd4.10-lain1@sha256:a7f08617cfdd5611c7988f58cd8463836e61610048aa29218c657730018f0711` | [tag API](https://hub.docker.com/v2/repositories/gually/lain5g-srsranproject-uhd/tags/24.10.1-uhd4.10-lain1) |
| `lain5g-lab/kamailio:local` | `gually/lain5g-kamailio:5.8.8-lain1@sha256:a59ac70c28c9635944b4bbebbfd292e611b08b2b454bcb0f020afc3d4544ca0e` | [tag API](https://hub.docker.com/v2/repositories/gually/lain5g-kamailio/tags/5.8.8-lain1) |
| `lain5g-lab/ims-dns:local` | `gually/lain5g-ims-dns:1.11.3-lain1@sha256:54663afe89d68dab67d5b0d98a70d6e2d2f7910ea9267622d8844a2ce9fdaed7` | [tag API](https://hub.docker.com/v2/repositories/gually/lain5g-ims-dns/tags/1.11.3-lain1) |
| `lain5g-lab/ims-sip:local` | `gually/lain5g-ims-sip:1.0-lain1@sha256:fa164401efcab1738c8b8e56ade75949ae50e25e2745a37053d7d3c8ebf295cf` | [tag API](https://hub.docker.com/v2/repositories/gually/lain5g-ims-sip/tags/1.0-lain1) |

## Python Direct Set

| Scope | Exact tested direct dependencies |
| --- | --- |
| Runtime | `fastapi==0.139.0`, `uvicorn==0.51.0`, `pydantic==2.13.4`, `pydantic-settings==2.14.2`, `pymongo==4.17.0`, `PyYAML==6.0.3` |
| Development | `pytest==9.1.1`, `pytest-cov==7.1.0`, `httpx==0.28.1` |
| Full closure | Every package and version is listed in `backend/constraints.txt`; source was `.venv/bin/pip freeze --all` before release tests |

The npm transitive closure and registry integrity values remain authoritative in
`frontend/package-lock.json`; the root package version is `1.0.0-rc.1`.
`npm audit --omit=dev` reports zero findings. The full locked tree reports five
development findings (three moderate, one high, and one critical) in the
Vitest/Vite test path. npm's available remediation is the semver-major update to
Vitest `4.1.10`; it was not applied as an unreviewed release metadata change.

## RTPengine Evidence

- Release channel: `https://rtpengine.dfx.at/26.0`.
- Bookworm Release file captured from
  `https://rtpengine.dfx.at/26.0/dists/bookworm/Release`.
- Supported repository architectures observed: `i386`, `amd64`, `armhf`,
  `arm64`.
- Keyring SHA-256 published by dfx.at and independently recalculated:
  `78fe26f0251138f4e3c749c88dc4df29666c8efe0823858d3a4ab49d2fa2e088`.
- Package revision observed for Bookworm amd64: `26.0.1.19-1~bpo12+1`.
- Package revision observed for Bookworm arm64: `26.0.1.17-1~bpo12+1`.

## Unresolved Risks

- No trusted snapshot date locks APT repositories. Exact source commits and
  base filesystem digests do not make OS package installation bit-reproducible.
- RTPengine's `26.0` channel can move and currently differs by architecture.
- The current Python closure was executed on CPython 3.14.4; the pinned backend
  image targets CPython 3.12 and was statically checked but not built here.
- The published catalog and GHCR Real-IMS application bases are Linux/amd64
  only. No non-amd64 runtime claim is made.
- Local first-party image tags are aliases and do not identify build output by
  digest. Archive final image digests with experiment evidence.
- Catalogued registry digests are not linked to the current source commits by a
  verifiable build record and are blocked for release-candidate republication.
- The locked Vitest/Vite development tree has five npm audit findings. The
  production dependency audit is clean, and the vulnerable Vitest UI mode is
  not used by the release test command, but the test toolchain still requires a
  separately reviewed major upgrade.
- No scenario, RF, hardware, or database validation was run as part of this
  release metadata work.

## Static Validation

- All 11 Compose configurations resolved with `docker compose config --quiet`
  using checked-in non-secret example/default environment files.
- All 19 tracked Dockerfiles parsed with the pinned Hadolint artifact and had
  no error-severity findings. Advisory findings remain for unsnapshotted APT
  package versions and inherited shell/style practices.
