# Lain5G-Lab Real IMS Package

This directory contains the target-owned Compose and provenance layer for a
real Open5GS, Kamailio, and pyHSS IMS core. The images are built from
`images/ims-real-*` and `images/pyhss-secure`; immutable base references are in
`images.lock.yaml` and imported configuration hashes are in
`config-provenance.json`.

Use the target-native CLI from the repository root:

```bash
.venv/bin/python scripts/ims_real.py images
.venv/bin/python scripts/ims_real.py images --execute
.venv/bin/python scripts/ims_real.py preflight --mode 5g
.venv/bin/python scripts/ims_real.py start --mode 5g --execute
.venv/bin/python scripts/ims_real.py provision --mode 5g \
  --subscriber-file config/real-ims-subscriber.json --execute
.venv/bin/python scripts/ims_real.py status --mode 5g
.venv/bin/python scripts/ims_real.py wait-register --mode 5g --timeout 300
.venv/bin/python scripts/ims_real.py stop --mode 5g --execute
```

Commands that can mutate Docker state or subscriber databases return a plan
unless `--execute` is present. Provisioning accepts subscriber credentials only
from a JSON file; never place Ki or OPc on a command line or commit a populated
file. Runtime secrets and generated pyHSS configuration are written under the
ignored `deployments/ims-real/.runtime/` directory.

The manifests publish no host ports. In particular, the pyHSS API and Diameter
listeners are reachable only inside the Compose project. Named volumes and the
default network remain Compose-scoped, and 4G and 5G use distinct
`lain5g-lab-ims-real-*` projects and backend-supplied subnet overrides.

This package starts no RF service and contains no RAN, UERANSIM, or WebUI.
UERANSIM is not an IMS voice user agent. A healthy core does not prove UE
registration or a voice call; see `docs/real_ims.md` for the validation boundary
and operational limitations.
