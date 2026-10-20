# 5G SA simulated run on macOS ARM64

This evidence package records one local software-only run of Lain5G 5G SA using Open5GS and UERANSIM. It used Docker Desktop on an ARM64 macOS host. Open5GS and MongoDB ran as ARM64 images; the pinned UERANSIM image is AMD64 and ran under Docker Desktop emulation. No USRP, antenna, or RF transmission was involved.

## Outcome

All 15 checks in `validation.json` passed: MongoDB, the 5G core services, gNB NG setup, UE registration, PDU session establishment, the UE tunnel and address assignment, and a ping to `8.8.8.8` from the UE tunnel (UE address redacted). The run started at `2026-10-20T10:27:19Z` and was stopped at `2026-10-20T10:27:46Z`. A redacted log copy is in `logs/docker-compose.log`; subscriber identifiers and private addresses were removed. The unredacted source log remains in the ignored local `runs/` directory.

## Provenance and limits

The run metadata records repository HEAD `583c350`. The working tree had local modifications during this run, so that short commit alone does not identify the exact source state. The package records the validation and container logs, but it is not a claim of physical-radio performance or a benchmark against a manual installation. The UE image ran through CPU emulation, which may affect timings.

The generated subscriber credentials were temporary and were not copied into this package. The run was stopped after validation. Its source tree had local modifications, as documented in `environment.json`; this is not an immutable release reproduction.
