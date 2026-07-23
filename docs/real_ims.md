# Real IMS Operations

Lain5G-Lab packages a real IMS core separately from its simulated and X310
scenarios. The package includes Open5GS packet core roles, MongoDB, MySQL,
Kamailio P/I/S-CSCF, pyHSS, DNS, and RTPengine. It does not include a RAN, RF
control, UERANSIM, or an Open5GS WebUI.

The [canonical capability table](../README.md#canonical-capability-status)
is the sole source of current scientific classifications. This guide defines
the operational and validation boundary; it does not promote historical or
private runtime markers to candidate-commit or public evidence.

The public
[`4g-ims-sim` result](../results/public/4g-ims-sim/run-20260723-055149.json)
records 22/22 passing checks with `SIMULATION_ONLY` classification for source
commit `12c4a38404bbaf240c698a056e3f47182081ab5c`. It uses laboratory Digest
registration and is not evidence for this real-IMS package, AKA, Cx, Rx, a
completed call, or media. The sanitized artifact was versioned by publication
commit `060e669d3f65e1844a702b1b5264be6933ef45c2`.

## Safety Boundary

The real IMS CLI never starts a gNB, eNB, UE simulator, or radio. The Compose
manifests do not publish host ports. pyHSS port 8080 and its Diameter port are
available only to services on the Compose network and backend operations use
`docker compose exec` rather than host access.

The imported services require privileged containers or `NET_ADMIN` for UPF,
P-CSCF, and RTPengine networking. Run this stack only on a dedicated, trusted
lab host. It is not a production or multi-tenant deployment. The imported
MySQL/Kamailio initialization also assumes an isolated Compose network and
permits passwordless MySQL root access from that internal network. No database
port is published to the host, but untrusted containers must not join it.

## Subscriber File

Start from `config/real-ims-subscriber.example.json`. Replace every redacted
placeholder in a local `config/real-ims-subscriber.json`; that path is ignored.
Restrict the file before use:

```bash
chmod 600 config/real-ims-subscriber.json
```

Do not pass Ki or OPc as command arguments, environment variables, chat text,
or issue content. Provisioning reads one JSON file and response reports exclude
the authentication keys.

## Commands

Image build is a dry-run plan unless explicitly executed:

```bash
make ims-real-images
make ims-real-images IMS_REAL_FLAGS="--execute"
```

Preflight and status are read-only. Select exactly one mode:

```bash
make ims-real-preflight IMS_REAL_FLAGS="--mode 5g"
make ims-real-status IMS_REAL_FLAGS="--mode 5g"
```

Start only the core and IMS services:

```bash
.venv/bin/python scripts/ims_real.py start --mode 5g
.venv/bin/python scripts/ims_real.py start --mode 5g --execute
```

Provision the same subscriber into Open5GS and pyHSS after startup:

```bash
.venv/bin/python scripts/ims_real.py provision \
  --mode 5g \
  --subscriber-file config/real-ims-subscriber.json \
  --execute
```

Use `--mcc` and `--mnc` only when the subscriber PLMN differs from the lab
default. The IMSI must begin with that MCC/MNC. The backend reconciles Open5GS
`internet` and `ims` sessions plus pyHSS APN, AuC, packet subscriber, and IMS
subscriber records.

Inspect an IMSI or wait for registration evidence:

```bash
.venv/bin/python scripts/ims_real.py status --mode 5g --imsi 001010000000001
.venv/bin/python scripts/ims_real.py wait-register --mode 5g --timeout 300
```

Stop without deleting Compose volumes:

```bash
make ims-real-stop IMS_REAL_FLAGS="--mode 5g --execute"
```

Use `--mode 4g` for the EPC/Rx topology. The backend gives each mode a distinct
Compose project and runtime subnet and refuses to run both modes concurrently.

## Generated Security

At execution time the backend creates a mode-specific directory under
`deployments/ims-real/.runtime/`, generates a pyHSS provisioning key, and writes
a hardened pyHSS configuration with provisioning locked, insecure AuC reads
disabled, and SQL echo disabled. The directory and files are restricted to the
local user. The source runtime files remain unchanged so their recorded
provenance hashes stay verifiable.

## Limitations

A passing preflight evaluates only its packaging, Docker, image, and publication
prerequisites. A passing service status evaluates only container and listener
readiness. Authenticated registration requires REGISTER, challenge,
authorization, final SIP 200, and Cx evidence in one correlated run. Audit-time
4G observations exist only as private, mutable markers without an anonymized
commit-linked package; the marker scan found `SUBSCRIBE`, `NOTIFY`, and
`INVITE`, but not `MESSAGE`.

Neither preflight, service status, nor registration proves a VoLTE/VoNR call.
The available evidence has no correlated final successful response to the
`INVITE`, no `ACK`, no `BYE`, and no bidirectional RTP. A complete result would
also require an IMS-capable UE and an integrated RAN path. No such UE or RAN is
supplied by this package, and the 5G mode has only non-executing evidence.
Accordingly, the canonical status for the 5G mode is `DRY_RUN_ONLY`; the private
4G observations remain `PARTIALLY_VALIDATED`.
