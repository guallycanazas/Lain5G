# Isolated Real IMS Runtime

OpenLain5G exposes an isolated real IMS runtime at `/ims`, separately from its
simulated and X310 scenarios. It follows the herlesupreeth pattern: Open5GS
provides packet-core subscriber data; Kamailio provides P-/I-/S-CSCF; and pyHSS
provides IMS subscriber data over Diameter Cx, backed by MySQL. The runtime has
separate 4G and 5G Compose projects, networks, subnets, and volumes; both modes
can run side by side. It does not include a RAN, RF control,
UERANSIM, or a public pyHSS endpoint.

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

## Operating Boundary

The local IMS console and `/api/ims-real` endpoints operate this package. The
manifests publish no host ports, and no action starts RF. Prepare missing
first-party images from the Preparation page; runtime start only checks that
they are present and starts services. Image building, runtime start/stop, and
subscriber provisioning require an explicit in-page confirmation and the
backend mutation gate. This runtime remains separate from the integrated IMS
services included in the VoLTE/VoNR deployment scenarios.

The Subscribers page can synchronize one existing IMS identity between the
4G and 5G real-IMS runtimes. The source and target runtimes must be running.
The backend reads the source Open5GS record locally and reconciles the target
Open5GS, pyHSS/AuC, and `internet`/`ims` APN records without returning Ki or
OPc in the API response.

## Generated Security

At execution time the backend creates a mode-specific directory under
`deployments/ims-real/.runtime/`, generates a pyHSS provisioning key, and writes
a hardened pyHSS configuration with provisioning locked, insecure AuC reads
disabled, and SQL echo disabled. The directory and files are restricted to the
local user. The source runtime files remain unchanged so their recorded
provenance hashes stay verifiable.

## Validation Scope

A passing preflight evaluates only its packaging, Docker, image, and publication
prerequisites. A passing service status evaluates only container and listener
readiness. Mutable marker scans are not validation. Authenticated registration
requires commit-linked, run-correlated evidence covering the applicable SIP and
Cx sequence. Call and media validation use a correlated evidence scope covering
dialog completion, teardown, and bidirectional RTP from the same run.

The package's core-service checks, registration flow, and call/media flow are
reported as distinct validation layers. A passing readiness report is not
evidence of VoLTE/VoNR registration or a completed call. IMS-capable UE and
integrated RAN evidence must be correlated with the package under the same run
identifier before making those claims.
