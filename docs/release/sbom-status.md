# SBOM Status

## Result

A safe, partial application source-manifest SBOM was generated. A complete
release SBOM was not generated because no final application, telecom, IMS, or
database image filesystem was inspected, and the ignored local Python
environment was deliberately excluded.

Artifact:

- Path: `sbom/lain5g-lab-application.cdx.json`
- Format: CycloneDX JSON 1.7
- Subject: `OpenLain5G` version `1.1.1`
- Generated: `2026-08-03T14:37:28Z`
- Components: 340 libraries, comprising 331 npm package/version entries and 9
  direct PyPI package/version entries
- Dependency graph entries: 125
- SHA-256:
  `574251d1350325747f8d7f21b5a6229dc89f25fe1b70f31fb83c39efa0cefa21`

## Generator

- Tool: Anchore Syft `1.49.0`
- Syft commit: `29fd7d0dec81cf03e0a1194a1985c7c893bb2396`
- Container index:
  `anchore/syft:v1.49.0@sha256:13b53ebabe3d215268c90cf8fb9b875f0183908245f376fd4b3a2cb69d21d484`
- Executed platform: `linux/amd64`
- Platform manifest selected by the index:
  `sha256:9a9f85314017f1ea798fb012edfa7fe9259923910f82c8d4bc983ab5c765e60b`
- Syft schema version reported by the tool: `16.1.10`

The image was resolved by immutable index digest. Generation ran with
`--network none`, the update check disabled, the repository mounted read-only,
npm development dependencies enabled, and file metadata disabled.

## Included Scope

The artifact includes package identities and dependency relationships detected
from:

- `frontend/package-lock.json`, including production, development, optional,
  and platform-specific lock entries; and
- the nine exact direct entries in `backend/requirements.txt` and
  `backend/requirements-dev.txt`.

The SBOM intentionally contains no scanner-enriched license assertions because
generation was network-isolated and the source manifests do not carry complete
license fields. Verified direct-package licenses are documented separately in
`THIRD_PARTY_NOTICES.md`.

## Excluded Scope

The scan explicitly excluded version-control and CI internals, generated SBOMs,
ignored dependency environments, runtime directories, environment files,
private RF overlays, subscriber input, key/certificate/credential patterns,
databases, dumps, backups, run output, logs, and packet captures.

The artifact does not cover:

- the 29-entry Python tested closure in `backend/constraints.txt` beyond its
  nine direct requirements;
- packages installed in final Python, nginx, Ubuntu, Debian, Alpine, MongoDB,
  MariaDB, MySQL, CoreDNS, or GHCR image filesystems;
- source-built Open5GS, UERANSIM, srsRAN 4G, srsRAN Project, UHD, Kamailio, or
  their C/C++ dependencies;
- RTPengine APT packages;
- imported configuration as software components;
- firmware, FPGA images, hardware state, RF state, scenarios, database data,
  or runtime evidence.

The artifact is therefore a partial application dependency SBOM, not a complete
release, deployment, or container SBOM.

The generated BOM does not encode that partiality through a CycloneDX
`composition` declaration. Its dependency graph contains 125 entries and leaves
64 components disconnected, including all nine direct PyPI entries. The
sidecar status in this document is therefore required to interpret its scope;
the artifact must not be used as a complete dependency graph.

## Generation Command

The artifact was generated from the repository root with the following pinned
command. The repeated exclusions are deliberate and keep the command
self-contained rather than relying on local ignore-file interpretation.

```bash
docker run --rm --network none \
  --env SYFT_CHECK_FOR_APP_UPDATE=false \
  --env SYFT_JAVASCRIPT_INCLUDE_DEV_DEPENDENCIES=true \
  --env SYFT_FILE_METADATA_SELECTION=none \
  --env SYFT_RELATIONSHIPS_PACKAGE_FILE_OWNERSHIP=false \
  --mount type=bind,source="$PWD",target=/src,readonly \
  anchore/syft:v1.49.0@sha256:13b53ebabe3d215268c90cf8fb9b875f0183908245f376fd4b3a2cb69d21d484 \
  scan dir:/src --base-path /src \
  --source-name OpenLain5G --source-version 1.1.1 \
  --exclude './.git' --exclude './.git/**' \
  --exclude './.github' --exclude './.github/**' \
  --exclude './.venv' --exclude './.venv/**' \
  --exclude '**/.venv' --exclude '**/.venv/**' \
  --exclude './node_modules' --exclude './node_modules/**' \
  --exclude '**/node_modules' --exclude '**/node_modules/**' \
  --exclude './runs' --exclude './runs/**' \
  --exclude './.backups' --exclude './.backups/**' \
  --exclude './.direnv' --exclude './.direnv/**' \
  --exclude './sbom' --exclude './sbom/**' \
  --exclude '**/.runtime' --exclude '**/.runtime/**' \
  --exclude './.env' --exclude './.env.*' \
  --exclude '**/.env' --exclude '**/.env.*' \
  --exclude './config/real-ims-subscriber.json' \
  --exclude '**/rf/channel-plan.yaml' \
  --exclude '**/rf/safety-manifest.yaml' \
  --exclude '**/rf/*.local.yaml' --exclude '**/rf/*-local.yaml' \
  --exclude '**/.rf-active' \
  --exclude '**/*.key' --exclude '**/*.pem' \
  --exclude '**/*.p12' --exclude '**/*.pfx' \
  --exclude '**/*.jks' --exclude '**/*.keystore' \
  --exclude '**/*.kdbx' --exclude '**/*.crt' \
  --exclude '**/*.cer' --exclude '**/*.der' \
  --exclude '**/*.token' --exclude '**/*.secret' \
  --exclude '**/*.credentials' \
  --exclude '**/*.sqlite3' --exclude '**/*.sqlite' \
  --exclude '**/*.db' --exclude '**/*.db3' \
  --exclude '**/*.dump' --exclude '**/*.bson' \
  --exclude '**/*.sql.gz' --exclude '**/*.sql.zst' \
  --exclude '**/*.log' --exclude '**/*.pcap' \
  --exclude '**/*.pcapng' \
  --output cyclonedx-json \
  > sbom/lain5g-lab-application.cdx.json
```

## Validation

Validation performed after generation established that:

- `jq` parsed the artifact successfully;
- `bomFormat` is `CycloneDX`, `specVersion` is `1.7`, and `components` is an
  array;
- the component count and ecosystem counts agree with the declared scope;
- no string contains a host home path, `/src` scan path, file URI, or directory
  source URI; normalized repository-relative manifest locations remain;
- no string matches IPv4 loopback, link-local, or RFC 1918 private ranges,
  `localhost`, or `.local` host names;
- no string matches password, credential, private-key, API-key, access-token,
  or bearer-token indicators; and
- no string records run, backup, or environment-file paths.

The validation checks inspect generated strings, not the excluded source data.
No secret values or private paths are reproduced in this document.

## Pending Complete Scan

A local tag is mutable, and a read-only Docker-socket mount still grants broad
Docker API authority. A future complete scan should first export the reviewed
final image, record the archive hash and image ID or registry digest, and then
scan that immutable archive without mounting the Docker socket. Procedure
template:

```bash
test -f .env.app
REVIEW_DIR="${REVIEW_DIR:-$PWD/reviewed-images}"
mkdir -p "$REVIEW_DIR"

docker compose --env-file .env.app -f docker-compose.app.yml build backend
image_id="$(docker compose --env-file .env.app \
  -f docker-compose.app.yml images -q backend)"
test -n "$image_id"
docker save --output "$REVIEW_DIR/lain5g-lab-backend.tar" \
  "$image_id"
sha256sum "$REVIEW_DIR/lain5g-lab-backend.tar" \
  > "$REVIEW_DIR/lain5g-lab-backend.tar.sha256"
chmod 0444 "$REVIEW_DIR/lain5g-lab-backend.tar" \
  "$REVIEW_DIR/lain5g-lab-backend.tar.sha256"
sha256sum --check "$REVIEW_DIR/lain5g-lab-backend.tar.sha256"

docker run --rm --network none \
  --env SYFT_CHECK_FOR_APP_UPDATE=false \
  --mount type=bind,source="$REVIEW_DIR/lain5g-lab-backend.tar",target=/input/backend.tar,readonly \
  --mount type=bind,source="$PWD/sbom",target=/out \
  anchore/syft:v1.49.0@sha256:13b53ebabe3d215268c90cf8fb9b875f0183908245f376fd4b3a2cb69d21d484 \
  scan docker-archive:/input/backend.tar \
  --source-name lain5g-lab/backend --source-version 1.1.1 \
  --output cyclonedx-json=/out/lain5g-lab-backend-image.cdx.json
```

Verify the recorded checksum again immediately before any later scan. If a
registry artifact is the publication unit, scan by its immutable registry digest
instead and record that digest with the generated SBOM.

Equivalent archive- or registry-digest scans remain required for the frontend
and every published telecom or Real-IMS image. This SBOM covers source manifests
only; final-image scans remain outstanding.
