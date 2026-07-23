# Third-Party Notices

Lain5G-Lab does not implement a mobile core, radio access network, SIP core,
media relay, DNS server, or database server. It provides an independently
licensed deployment, configuration, administration, validation, and
visualisation layer around the third-party works identified below.

This inventory was checked on 2026-07-23 against the upstream materials linked
in each entry. Versions and commits are taken from
`docs/reproducibility/version-matrix.md`, the checked-in build recipes, and the
package lock files. An SPDX identifier is stated only where exact-version
upstream evidence supports it. A container image is an aggregate: the license
of its principal program does not license every package in that image.

The following status terms are used:

- **Build download** means that the repository stores a recipe and downloads
  the third-party work while building; the upstream source is not vendored.
- **Deployment pull** means that a deployment refers to an external image by
  digest and does not copy that image into this source repository.
- **Catalogued registry artifact** means that the release matrix records a
  project image currently available by digest from a public registry. Registry
  availability does not prove which source commit or build recipe produced the
  bytes.
- **Vendored** means that third-party source or configuration is present in
  this repository.

This notice is informational and is not a substitute for the complete license
terms supplied by each project.

No signed attestation or archived build record currently binds the catalogued
project image digests to the source commits and Dockerfiles below. Those images
therefore remain blocked for release-candidate binary publication even where the
principal program's source revision and license are known.

## Mobile Core and Radio Access Components

### Open5GS

- **Component and exact revision:** Open5GS `v2.7.5`, commit
  `7dfd9a39649700c24c22f1978ed7a35541a72cca`.
- **Authoritative project:** [open5gs/open5gs](https://github.com/open5gs/open5gs/tree/7dfd9a39649700c24c22f1978ed7a35541a72cca).
- **Verified license:** GNU Affero General Public License v3.0 or later
  (`AGPL-3.0-or-later`). The [license text](https://github.com/open5gs/open5gs/blob/7dfd9a39649700c24c22f1978ed7a35541a72cca/LICENSE)
  and exact-revision source headers both state version 3 or, at the recipient's
  option, a later version.
- **Use:** 4G EPC and 5G Core network functions. A separate Real-IMS path
  derives from an upstream Open5GS application image.
- **Download and redistribution status:** build download for the first-party
  image; catalogued registry artifact
  `gually/lain5g-open5gs:2.7.5-lain1@sha256:d25affe90c39adb35bfef312e725b27d2ef6b139ec1d8b2fe9f5d0da6d82753c`;
  Real-IMS deployment pull from the GHCR digest listed under Base Images.
- **Restrictions and open questions:** conveyance of object code requires the
  notices and Corresponding Source arrangements in AGPL section 6. Modified
  network-facing versions are also subject to AGPL section 13. Before any
  release-candidate republication, the publisher must provide durable,
  equivalent access to the exact source and build modifications. Existing
  public artifacts require the same provenance and source-material remediation.

### srsRAN 4G

- **Component and exact revision:** srsRAN 4G `release_23_11`, commit
  `eea87b1d893ae58e0b08bc381730c502024ae71f`.
- **Authoritative project:** [srsran/srsRAN_4G](https://github.com/srsran/srsRAN_4G/tree/eea87b1d893ae58e0b08bc381730c502024ae71f).
- **Verified license:** GNU Affero General Public License v3.0 or later
  (`AGPL-3.0-or-later`), verified from the exact-revision
  [license](https://github.com/srsran/srsRAN_4G/blob/eea87b1d893ae58e0b08bc381730c502024ae71f/LICENSE)
  and source headers.
- **Use:** software LTE eNB/UE simulation and the UHD-enabled LTE path.
- **Download and redistribution status:** build download; catalogued registry artifacts
  `gually/lain5g-srsran4g-sim:23.11-lain1@sha256:7ec771cf70e77f699283017b02bbe6311fd377047109dc952c2c18ebae1e2ced`
  and
  `gually/lain5g-srsran4g-uhd:23.11-uhd4.10-lain1@sha256:8d8ed84133008b542e0db510d57a458049c1b6391e7fd557a81d03dde794cb2e`.
- **Restrictions and open questions:** AGPL Corresponding Source and network
  interaction obligations apply. The UHD-enabled recipe changes the selected
  upstream `CMakeLists.txt` from C++14 to C++17 before compiling. That
  modification, its build recipe, and the separately licensed UHD and
  operating-system packages must be included in Corresponding Source and notice
  material.

### srsRAN Project

- **Component and exact revision:** srsRAN Project `release_24_10_1`, commit
  `ef4b0749a12a3b1a8347ae01c937a621603b4069`.
- **Authoritative project:** [srsran/srsRAN_Project](https://github.com/srsran/srsRAN_Project/tree/ef4b0749a12a3b1a8347ae01c937a621603b4069).
- **Verified license:** GNU Affero General Public License v3.0 or later
  (`AGPL-3.0-or-later`), verified from the exact-revision
  [license](https://github.com/srsran/srsRAN_Project/blob/ef4b0749a12a3b1a8347ae01c937a621603b4069/LICENSE)
  and application source headers.
- **Use:** UHD-enabled 5G gNB for the X310 preparation path. The build applies
  the checked-in `uhd-4.10-event-code-ok.patch` before compiling the gNB.
- **Download and redistribution status:** build download; catalogued registry artifact
  `gually/lain5g-srsranproject-uhd:24.10.1-uhd4.10-lain1@sha256:a7f08617cfdd5611c7988f58cd8463836e61610048aa29218c657730018f0711`.
- **Restrictions and open questions:** the exact upstream source and the
  project patch must remain available with any conveyed object code; AGPL
  section 13 also applies to modified network-facing use.

### UERANSIM

- **Component and exact revision:** UERANSIM `v3.2.6`, commit
  `384636f4fcf46b8c86109790ff3e2cd242b53556`.
- **Authoritative project:** [aligungr/UERANSIM](https://github.com/aligungr/UERANSIM/tree/384636f4fcf46b8c86109790ff3e2cd242b53556).
- **Verified license:** GNU General Public License v3.0. The exact-revision
  [root license](https://github.com/aligungr/UERANSIM/blob/384636f4fcf46b8c86109790ff3e2cd242b53556/LICENSE)
  and upstream repository metadata identify GPL v3. Upstream evidence reviewed
  here does not resolve the SPDX `-only` versus `-or-later` suffix, so neither
  suffix is asserted.
- **Use:** software 5G SA gNB and UE simulation.
- **Download and redistribution status:** build download; catalogued registry artifact
  `gually/lain5g-ueransim:3.2.6-lain1@sha256:1451cb0327f97fb276b30b78ec1c3ad54bbb480ec044004e580e62a20b60a8a2`.
- **Restrictions and open questions:** GPL object-code redistribution requires
  preservation of notices and provision of Corresponding Source. The precise
  SPDX suffix remains an upstream clarification item.

### UHD

- **Component and exact revision:** USRP Hardware Driver (UHD) `v4.10.0.0`,
  commit `2af4ddb96219a99d2300804830e0971f79557b23`.
- **Authoritative project:** [EttusResearch/uhd](https://github.com/EttusResearch/uhd/tree/2af4ddb96219a99d2300804830e0971f79557b23).
- **Verified license:** the exact-revision [license statement](https://github.com/EttusResearch/uhd/blob/2af4ddb96219a99d2300804830e0971f79557b23/LICENSE.md)
  states that UHD and MPM are GPLv3 by default. It also states that individual
  files, bundled dependencies, and FPGA directories can have different terms.
  No single SPDX expression is therefore assigned to the repository as a
  whole.
- **Use:** host-side communication with USRP hardware in the srsRAN 4G and
  srsRAN Project images. The image recipes do not download or update device
  firmware or FPGA images.
- **Download and redistribution status:** build download; redistributed inside
  the two published UHD-enabled srsRAN images identified above.
- **Restrictions and open questions:** GPLv3 obligations apply to the default
  UHD/MPM code. A file-level review of the built host subset and bundled
  dependencies is still required before declaring either composite image
  redistribution-complete.

## IMS, SIP, Media, and DNS Components

### Kamailio

- **Component and exact revision:** Kamailio `5.8.8`, commit
  `053181eb9c3136836cb272584b582484a9a11b48`.
- **Authoritative project:** [kamailio/kamailio](https://github.com/kamailio/kamailio/tree/053181eb9c3136836cb272584b582484a9a11b48).
- **Verified license:** GNU General Public License v2.0 or later
  (`GPL-2.0-or-later`) for the core and selected modules, verified from the
  exact-revision [COPYING](https://github.com/kamailio/kamailio/blob/053181eb9c3136836cb272584b582484a9a11b48/COPYING)
  and core source headers. Upstream warns that external modules linked as
  plug-ins must be GPL or GPL-compatible.
- **Use:** SIP routing and IMS P-CSCF, I-CSCF, and S-CSCF functions.
- **Download and redistribution status:** build download for the minimal image;
  catalogued registry artifact
  `gually/lain5g-kamailio:5.8.8-lain1@sha256:a59ac70c28c9635944b4bbebbfd292e611b08b2b454bcb0f020afc3d4544ca0e`;
  the Real-IMS path uses the GHCR base digest listed below.
- **Restrictions and open questions:** GPLv2 Corresponding Source and notice
  requirements apply. The current Real-IMS image label says
  `GPL-2.0-only`; that is narrower than the verified upstream grant and must
  be reconciled before binary publication.

### pyHSS

- **Component and exact revision:** pyHSS tag `1.0.2`, commit
  `71a91f6d9e6b910a74750e266edb7642ca8f9971`.
- **Authoritative project:** [nickvsnetworking/pyhss](https://github.com/nickvsnetworking/pyhss/tree/71a91f6d9e6b910a74750e266edb7642ca8f9971).
- **Verified license:** GNU Affero General Public License v3.0. The exact-tag
  [root license](https://github.com/nickvsnetworking/pyhss/blob/71a91f6d9e6b910a74750e266edb7642ca8f9971/LICENSE)
  and GitHub license metadata identify AGPL v3, but the reviewed upstream
  material does not resolve the SPDX `-only` versus `-or-later` suffix.
- **Use:** HSS/IMS subscriber functions and internal provisioning in the
  Real-IMS deployment. The project wrapper removes one upstream log statement
  that prints provisioning payloads.
- **Download and redistribution status:** deployment pull of
  `ghcr.io/herlesupreeth/docker_pyhss@sha256:90206eb3cbe862bfa71e0bfaf038fe3ddbefba1df531eb2157c9642ac732e6fb`;
  a modified local derivative is defined but no public project digest is
  recorded for that derivative.
- **Restrictions and open questions:** the source modification and network use
  engage AGPL source-availability requirements. The upstream image's complete
  package inventory has not been inspected, and the precise AGPL SPDX suffix
  remains unresolved.

### RTPengine

- **Component and exact revision:** Sipwise RTPengine release channel `26.0`.
  The observed Bookworm packages are `26.0.1.19-1~bpo12+1` for amd64 and
  `26.0.1.17-1~bpo12+1` for arm64. No source commit is locked.
- **Authoritative project:** [sipwise/rtpengine](https://github.com/sipwise/rtpengine)
  and the [official 26.0 package repository](https://rtpengine.dfx.at/26.0/).
- **Verified license:** GNU General Public License v3.0, verified from the
  upstream [LICENSE](https://github.com/sipwise/rtpengine/blob/master/LICENSE).
  The reviewed root text does not establish `-only` versus `-or-later`.
- **Use:** IMS media relay.
- **Download and redistribution status:** the local image downloads a signed
  APT package at build time from channel `26.0`; no public project derivative
  digest is recorded.
- **Restrictions and open questions:** GPL source and notice obligations apply.
  The moving APT channel, architecture-dependent revisions, absent source
  commit, and unresolved SPDX suffix prevent a reproducible redistribution
  claim.

### CoreDNS

- **Component and exact revision:** CoreDNS `1.11.3`; base index digest
  `sha256:9caabbf6238b189a65d0d6e6ac138de60d6a1c419e5a341fbbb7c78382559c6e`.
- **Authoritative project:** [coredns/coredns v1.11.3](https://github.com/coredns/coredns/tree/v1.11.3).
- **Verified license:** Apache License 2.0 (`Apache-2.0`), verified from the
  exact-tag [LICENSE](https://github.com/coredns/coredns/blob/v1.11.3/LICENSE).
- **Use:** DNS service for the compact IMS laboratory path.
- **Download and redistribution status:** deployment/base-image pull;
  catalogued registry artifact
  `gually/lain5g-ims-dns:1.11.3-lain1@sha256:54663afe89d68dab67d5b0d98a70d6e2d2f7910ea9267622d8844a2ce9fdaed7`.
- **Restrictions and open questions:** Apache 2.0 license, attribution, change
  notice, and any upstream NOTICE obligations must be retained. Packages in
  the container, if any beyond CoreDNS, retain their own terms.

## Additional Runtime Components Pending Inspection

The checked-in recipes also install or invoke the following principal runtime
components. Their exact final-image versions and complete applicable license
sets were not established by this source-only review:

| Component | Repository evidence | Current disposition |
| --- | --- | --- |
| BIND 9 tools/server | Installed by `images/ims-real-dns/Dockerfile` | Version and final-image license/notice inventory pending; binary publication of the wrapper remains blocked. |
| Redis | Installed by `images/pyhss-secure/runtime/Dockerfile` | Version and final-image license expression pending; binary publication of the wrapper remains blocked. |
| Docker CLI and Compose plug-in | Installed by `backend/Dockerfile` for opt-in local operations | Exact package versions and notices pending final backend-image inspection. |

This table records known omissions rather than assigning unverified SPDX
identifiers. Transitive operating-system packages remain outside the source
manifest SBOM.

## Database Components

### MongoDB

- **Component and exact revision:** Docker Official Image index
  `mongo@sha256:8b6d8f5bbedb25cb73517b65cf99f13aeb75ad5b157a56c479287a840bbad3ac`.
  The release records do not associate this digest with an exact MongoDB
  server version tag.
- **Authoritative project:** [MongoDB Server](https://github.com/mongodb/mongo)
  and the [Docker Official Image](https://hub.docker.com/_/mongo).
- **Verified license:** MongoDB Community Server versions after 2018-10-16 use
  the Server Side Public License v1 (`SSPL-1.0`), verified from MongoDB's
  [official license text](https://www.mongodb.com/legal/licensing/server-side-public-license)
  and the Official Image notice. The image also contains Apache-licensed and
  distribution packages; it has no single image-wide license.
- **Use:** subscriber and core state required by Open5GS.
- **Download and redistribution status:** deployment pull only; the source
  repository does not vendor or publish the MongoDB image.
- **Restrictions and open questions:** SSPL section 13 imposes broad Service
  Source Code requirements when the program is offered as a service. SSPL is
  not an OSI-approved open-source license. The server version and complete
  package/license inventory represented by the locked digest remain to be
  established before republishing that image.

### MariaDB

- **Component and exact revision:** Docker Official Image major tag `11`
  captured as
  `mariadb@sha256:efb4959ef2c835cd735dbc388eb9ad6aab0c78dd64febcd51bc17481111890c4`.
  No exact patch version is recorded.
- **Authoritative project:** [MariaDB Server](https://github.com/MariaDB/server)
  and the [Docker Official Image](https://hub.docker.com/_/mariadb).
- **Verified license:** MariaDB Server is principally distributed under GNU
  GPL version 2; individual client libraries, connectors, image scripts, and
  base packages can use other licenses. The Official Image explicitly states
  that it is a multi-license aggregate, so no single SPDX expression is
  assigned to the image.
- **Use:** compact IMS subscriber and SIP data.
- **Download and redistribution status:** deployment pull only; the source
  repository does not vendor or publish the MariaDB image.
- **Restrictions and open questions:** GPL source and notice duties apply to
  covered server binaries if the image is conveyed. Exact patch version and a
  digest-specific package/license inventory are pending.

## Python Direct Packages

All Python versions below are exact pins from `backend/requirements.txt` and
`backend/requirements-dev.txt`. License values were verified from the
maintainer-supplied metadata for each exact PyPI release. Runtime packages are
downloaded during the backend image build; development packages are downloaded
only into a developer/test environment. No wheel or source archive is vendored
in this repository.

| Component | Exact version | Authoritative project and exact metadata | Verified license | Use | Download/redistribution status and restrictions |
| --- | --- | --- | --- | --- | --- |
| FastAPI | `0.139.0` | [fastapi/fastapi](https://github.com/fastapi/fastapi); [PyPI metadata](https://pypi.org/pypi/fastapi/0.139.0/json) | `MIT` | Backend API framework | Runtime build download; installed code may enter a locally built image. Retain the MIT notice on redistribution. |
| Uvicorn | `0.51.0` | [Kludex/uvicorn](https://github.com/Kludex/uvicorn); [PyPI metadata](https://pypi.org/pypi/uvicorn/0.51.0/json) | `BSD-3-Clause` | ASGI server | Runtime build download; retain copyright, conditions, and disclaimer. |
| Pydantic | `2.13.4` | [pydantic/pydantic](https://github.com/pydantic/pydantic); [PyPI metadata](https://pypi.org/pypi/pydantic/2.13.4/json) | `MIT` | Data validation and API models | Runtime build download; retain the MIT notice. |
| pydantic-settings | `2.14.2` | [pydantic/pydantic-settings](https://github.com/pydantic/pydantic-settings); [PyPI metadata](https://pypi.org/pypi/pydantic-settings/2.14.2/json) | `MIT` | Typed application settings | Runtime build download; retain the MIT notice. |
| PyMongo | `4.17.0` | [mongodb/mongo-python-driver](https://github.com/mongodb/mongo-python-driver); [PyPI metadata](https://pypi.org/pypi/pymongo/4.17.0/json) | `Apache-2.0` | MongoDB access | Runtime build download; retain Apache 2.0 and applicable NOTICE material. |
| PyYAML | `6.0.3` | [PyYAML](https://pyyaml.org/); [PyPI metadata](https://pypi.org/pypi/PyYAML/6.0.3/json) | `MIT` | YAML configuration parsing | Runtime build download; retain the MIT notice. |
| pytest | `9.1.1` | [pytest-dev/pytest](https://github.com/pytest-dev/pytest); [PyPI metadata](https://pypi.org/pypi/pytest/9.1.1/json) | `MIT` | Test runner | Development download only; retain the MIT notice if conveyed. |
| pytest-cov | `7.1.0` | [pytest-dev/pytest-cov](https://github.com/pytest-dev/pytest-cov); [PyPI metadata](https://pypi.org/pypi/pytest-cov/7.1.0/json) | `MIT` | Test coverage integration | Development download only; retain the MIT notice if conveyed. |
| HTTPX | `0.28.1` | [encode/httpx](https://github.com/encode/httpx); [PyPI metadata](https://pypi.org/pypi/httpx/0.28.1/json) | `BSD-3-Clause` | Backend API test client | Development download only; retain copyright, conditions, and disclaimer if conveyed. |

The Python transitive closure is pinned in `backend/constraints.txt`, but it
has not received the same component-by-component legal review as the direct
set. The partial SBOM records only the nine direct Python package manifests.

## npm Direct Packages

Exact resolved versions come from `frontend/package-lock.json`, not the
semver ranges in `frontend/package.json`. License values and authoritative
repositories were verified from the exact npm registry records linked below.
No npm tarball or `node_modules` directory is vendored.

| Component | Exact version | Authoritative project and exact metadata | Verified license | Use | Download/redistribution status and restrictions |
| --- | --- | --- | --- | --- | --- |
| `@tanstack/react-query` | `5.101.2` | [TanStack/query](https://github.com/TanStack/query); [npm metadata](https://registry.npmjs.org/@tanstack%2freact-query/5.101.2) | `MIT` | Client data fetching and cache | Build download; application bundle. Retain the MIT notice. |
| `@vitejs/plugin-react` | `4.7.0` | [vitejs/vite-plugin-react](https://github.com/vitejs/vite-plugin-react); [npm metadata](https://registry.npmjs.org/@vitejs%2fplugin-react/4.7.0) | `MIT` | React build transform | Build-stage download; not intended for the final runtime layer. Retain notice if conveyed. |
| `lucide-react` | `0.468.0` | [lucide-icons/lucide](https://github.com/lucide-icons/lucide); [npm metadata](https://registry.npmjs.org/lucide-react/0.468.0) | `ISC` | User-interface icons | Build download; application bundle. Retain the ISC copyright and permission notice. |
| `react` | `19.2.7` | [facebook/react](https://github.com/facebook/react); [npm metadata](https://registry.npmjs.org/react/19.2.7) | `MIT` | User-interface runtime | Build download; application bundle. Retain the MIT notice. |
| `react-dom` | `19.2.7` | [facebook/react](https://github.com/facebook/react); [npm metadata](https://registry.npmjs.org/react-dom/19.2.7) | `MIT` | DOM renderer | Build download; application bundle. Retain the MIT notice. |
| `react-router-dom` | `7.18.1` | [remix-run/react-router](https://github.com/remix-run/react-router); [npm metadata](https://registry.npmjs.org/react-router-dom/7.18.1) | `MIT` | Browser routing | Build download; application bundle. Retain the MIT notice. |
| `vite` | `6.4.3` | [vitejs/vite](https://github.com/vitejs/vite); [npm metadata](https://registry.npmjs.org/vite/6.4.3) | `MIT` | Frontend build tool | Build-stage download; not intended for the final runtime layer. Retain notice if conveyed. |
| `@testing-library/jest-dom` | `6.9.1` | [testing-library/jest-dom](https://github.com/testing-library/jest-dom); [npm metadata](https://registry.npmjs.org/@testing-library%2fjest-dom/6.9.1) | `MIT` | DOM test assertions | Development download only; retain notice if conveyed. |
| `@testing-library/react` | `16.3.2` | [testing-library/react-testing-library](https://github.com/testing-library/react-testing-library); [npm metadata](https://registry.npmjs.org/@testing-library%2freact/16.3.2) | `MIT` | React test utilities | Development download only; retain notice if conveyed. |
| `@testing-library/user-event` | `14.6.1` | [testing-library/user-event](https://github.com/testing-library/user-event); [npm metadata](https://registry.npmjs.org/@testing-library%2fuser-event/14.6.1) | `MIT` | User interaction tests | Development download only; retain notice if conveyed. |
| `@types/react` | `19.2.17` | [DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/react); [npm metadata](https://registry.npmjs.org/@types%2freact/19.2.17) | `MIT` | React type declarations | Development/build download; retain notice if conveyed. |
| `@types/react-dom` | `19.2.3` | [DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/react-dom); [npm metadata](https://registry.npmjs.org/@types%2freact-dom/19.2.3) | `MIT` | React DOM type declarations | Development/build download; retain notice if conveyed. |
| `jsdom` | `25.0.1` | [jsdom/jsdom](https://github.com/jsdom/jsdom); [npm metadata](https://registry.npmjs.org/jsdom/25.0.1) | `MIT` | Browser-like test environment | Development download only; retain notice if conveyed. |
| `typescript` | `5.9.3` | [microsoft/TypeScript](https://github.com/microsoft/TypeScript); [npm metadata](https://registry.npmjs.org/typescript/5.9.3) | `Apache-2.0` | Type checking and compilation | Development/build download; retain Apache 2.0 and applicable NOTICE material if conveyed. |
| `vitest` | `2.1.9` | [vitest-dev/vitest](https://github.com/vitest-dev/vitest); [npm metadata](https://registry.npmjs.org/vitest/2.1.9) | `MIT` | Frontend test runner | Development download only; retain notice if conveyed. |

The npm lock contains the transitive production and development trees and
registry integrity values. A generated license bundle is not currently copied
into the final static frontend image; that is an unresolved binary
redistribution item even though the source lock is complete.

## Base Images

Docker Official Image build repositories commonly license their Dockerfiles
under MIT or Apache-2.0, but that license does not relicense the runtime,
distribution packages, or application placed in an image. The verified and
honest license conclusion for each image below is therefore an aggregate,
except for the principal application identified separately.

| Base input | Exact locked digest | Authoritative project and verified license position | Use and download/redistribution status | Restrictions or open questions |
| --- | --- | --- | --- | --- |
| `python:3.12-slim` | `sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de` | [Docker Official Python image](https://github.com/docker-library/python) recipes are MIT; CPython uses the [PSF License](https://docs.python.org/3/license.html); Debian packages retain individual licenses. | Backend and compact SIP bases; deployment/build pull and possible derivative image content. | No digest-specific OS package license inventory has been archived. |
| `node:22-alpine` | `sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2` | [Docker Official Node image](https://github.com/nodejs/docker-node) recipes and [Node.js](https://github.com/nodejs/node) are MIT; Alpine packages retain individual licenses. | Frontend build stage only; build pull. | Build-stage packages are not expected in the nginx runtime, but the final bundle requires its own notice inventory. |
| `nginx:1.27-alpine` | `sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10` | [Docker Official nginx image](https://hub.docker.com/_/nginx); nginx uses its [2-clause BSD license](https://nginx.org/LICENSE), while Alpine packages vary. | Final frontend runtime base; build pull and derivative content. | No digest-specific package/license inventory has been archived. |
| `ubuntu:22.04` / `ubuntu:jammy` | `sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982` | [Ubuntu base image](https://hub.docker.com/_/ubuntu); aggregate of packages under their source-package licenses, with no single image-wide license. | Principal base for Open5GS, UERANSIM, srsRAN 4G, DNS, pyHSS reference, and MySQL reference images. | A final-image package and notice inventory is pending. |
| `ubuntu:24.04` | `sha256:4fbb8e6a8395de5a7550b33509421a2bafbc0aab6c06ba2cef9ebffbc7092d90` | [Ubuntu base image](https://hub.docker.com/_/ubuntu); multi-license package aggregate. | srsRAN Project build/runtime base. | A final-image package and notice inventory is pending. |
| `debian:bookworm-slim` | `sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818` | [Debian Official Image](https://hub.docker.com/_/debian); packages retain their individual Debian copyright terms. | Minimal Kamailio base. | A final-image package and notice inventory is pending. |
| `debian:bookworm` reference | `sha256:9344f8b8992482f80cba753f323adeaf17690076c095ccff6cc9536be98185dc` | [Debian Official Image](https://hub.docker.com/_/debian); multi-license aggregate. | Vendored RTPengine reference Dockerfile. | Reference input only; the active wrapper uses the separately locked Debian digest below. |
| CoreDNS `1.11.3` | `sha256:9caabbf6238b189a65d0d6e6ac138de60d6a1c419e5a341fbbb7c78382559c6e` | CoreDNS is `Apache-2.0`; see the component entry above. | Compact IMS DNS base and catalogued registry artifact. | Preserve Apache notices and inspect any additional image contents. |
| Real-IMS RTPengine Debian base | `sha256:60eac759739651111db372c07be67863818726f754804b8707c90979bda511df` | [Debian Official Image](https://hub.docker.com/_/debian); multi-license aggregate. | Active RTPengine wrapper base. | The tag/date corresponding to this digest and its package inventory are not recorded. |
| Real-IMS Open5GS GHCR base | `sha256:441d40e16f76ae79fc25eaaa92245850ed833bdd3d0d0dc78acbffd958cdc2c6` | [herlesupreeth/docker_open5gs](https://github.com/herlesupreeth/docker_open5gs) packages Open5GS under its AGPL terms; the packaging/configuration repository is BSD-2-Clause; OS packages vary. | Deployment pull and local wrapper base. | Exact embedded Open5GS version and complete image licenses are not established by the lock. BSD-2-Clause does not relicense Open5GS. |
| Real-IMS Kamailio GHCR base | `sha256:67dc92b423ca5ef0b827a049d0cabeff741f3eafd9222608036494f4d7611821` | [herlesupreeth/docker_open5gs](https://github.com/herlesupreeth/docker_open5gs) packaging is BSD-2-Clause; Kamailio remains GPL-2.0-or-later; OS packages vary. | Deployment pull and local wrapper base. | Exact embedded Kamailio version and complete image licenses are pending. |
| Real-IMS pyHSS GHCR base | `sha256:90206eb3cbe862bfa71e0bfaf038fe3ddbefba1df531eb2157c9642ac732e6fb` | Packaging/configuration is BSD-2-Clause; pyHSS is verified as AGPL v3 with suffix unresolved; OS and Python packages vary. | Deployment pull and modified local wrapper base. | Exact package inventory and AGPL suffix are pending; the local modification requires source disclosure controls. |
| Real-IMS MySQL GHCR base | `sha256:324d3d4c5089feea787684f0dbf1a646dde8d356170085ac0b6538aee6910057` | Packaging/configuration is BSD-2-Clause; [MySQL Community Server](https://www.mysql.com/about/legal/licensing/oem/) is principally GPLv2 with component-specific terms; OS packages vary. | Deployment pull and local wrapper base. | Exact server version, applicable exceptions, and complete image licenses are not established by the lock. |

The MongoDB base digest is documented in the MongoDB entry. MariaDB is a
deployment image rather than a Dockerfile base and is documented separately.

## Imported BSD Configuration

- **Component and exact revision:** selected configurations and startup scripts
  from `herlesupreeth/docker_open5gs`, commit
  `3685b58aa0c7c28b2fecc6b9533f128285bf8dda`.
- **Authoritative project:** [exact upstream commit](https://github.com/herlesupreeth/docker_open5gs/tree/3685b58aa0c7c28b2fecc6b9533f128285bf8dda).
- **Verified license:** BSD 2-Clause (`BSD-2-Clause`), verified from the
  exact-commit [LICENSE](https://github.com/herlesupreeth/docker_open5gs/blob/3685b58aa0c7c28b2fecc6b9533f128285bf8dda/LICENSE).
- **Use:** Real-IMS Open5GS roles, Kamailio roles, DNS zones, RTPengine startup,
  MySQL startup, and pyHSS runtime configuration.
- **Download and redistribution status:** vendored and redistributed in this
  source repository. File hashes and documented transformations are recorded
  in `deployments/ims-real/config-provenance.json`. Private key material was
  deliberately excluded and is generated only at runtime.
- **Restrictions and open questions:** source redistributions must retain the
  following copyright notice, conditions, and disclaimer. Binary
  redistributions must reproduce them in accompanying documentation or other
  materials. This BSD grant applies only to the imported packaging and
  configuration, not to third-party applications named by those files.

The required upstream notice follows:

```text
BSD 2-Clause License

Copyright (c) 2020-2025, Supreeth Herle
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Completeness and Trademarks

The partial application SBOM and its limitations are documented in
`docs/release/sbom-status.md`. Operating-system packages, compiler outputs,
firmware, FPGA images, final image filesystems, and Python transitive packages
are not fully represented there. The legal review and redistribution gates are
recorded in `docs/legal/redistribution-status.md`.

Project and product names may be trademarks of their respective owners. No
trademark license is granted by this notice.
