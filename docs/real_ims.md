# Archived Real IMS Design

OpenLain5G packages a real IMS core separately from its simulated and X310
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

## Archived Boundary

The manifests, service implementation, provenance, and tests remain available
for source review and historical traceability. Real IMS has no public web, API,
Make, or standalone CLI entry point and is not one of the supported launchable
profiles.

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
readiness. Mutable marker scans are not validation. Authenticated registration
requires commit-linked, run-correlated evidence covering the applicable SIP and
Cx sequence. A call claim additionally requires final dialog completion and
bidirectional RTP evidence from the same run.

Neither preflight, service status, nor registration proves a VoLTE/VoNR call. A
complete result requires a correlated successful SIP dialog, teardown, and
bidirectional RTP, plus an IMS-capable UE and integrated RAN path. This package
does not supply that UE or RAN, and no public result establishes the complete
call path. Accordingly, the canonical status for the 5G mode is `DRY_RUN_ONLY`;
private 4G observations remain `PARTIALLY_VALIDATED`.
