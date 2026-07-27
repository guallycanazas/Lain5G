# Lain5G-Lab Real IMS Package

This directory contains the target-owned Compose and provenance layer for a
real Open5GS, Kamailio, and pyHSS IMS core. The images are built from
`images/ims-real-*` and `images/pyhss-secure`; immutable base references are in
`images.lock.yaml` and imported configuration hashes are in
`config-provenance.json`.

This package is retained for source review and historical traceability. It has
no public web, API, Make, or standalone CLI entry point. Runtime secrets and
generated pyHSS configuration remain excluded under the ignored
`deployments/ims-real/.runtime/` directory.

The manifests publish no host ports. In particular, the pyHSS API and Diameter
listeners are reachable only inside the Compose project. Named volumes and the
default network remain Compose-scoped, and 4G and 5G use distinct
`lain5g-lab-ims-real-*` projects and backend-supplied subnet overrides.

This package starts no RF service and contains no RAN, UERANSIM, or WebUI.
UERANSIM is not an IMS voice user agent. A healthy core does not prove UE
registration or a voice call; see `docs/real_ims.md` for the archived validation
boundary.
