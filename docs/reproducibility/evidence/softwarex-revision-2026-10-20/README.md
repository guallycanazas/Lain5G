# Revision-cycle software simulations — 2026-10-20

These are new local 4G and 5G SA software-simulation checks from the revision cycle. They are separate from the five-run historical v1.1.3 series in `results/public/summaries/v1.1.3-cloud-five-run-20260818.md`.

| Profile | Run | Result | Checks | Time evidence |
|---|---|---:|---:|---|
| 4G LTE ZMQ | `run-20261020-113613` | PASS | 14/14 | 83 s start-to-stop, local Docker run |
| 5G SA UERANSIM | `run-20261020-135526` | PASS | 15/15 | 30 s start-to-validation; stack still running at capture, so no completed duration |

Both runs used software-only radio emulation; no USRP, antenna, or RF transmission was involved. The validation JSON files are sanitized to remove UE and gateway addresses. The host was an Apple M4 with 10 logical CPUs and 16 GB RAM; Docker Desktop 29.1.3 ran Linux/aarch64 containers. The historical 5G run used an AMD64 UERANSIM container under emulation; consult its environment record for that separate run.

## Provenance boundary

These runs were performed from a working tree based on `583c350` that contained uncommitted changes. They are new measurements, but they are not an immutable reproduction of the final revision commit. Do not cite them as a versioned release result until a clean checkout of the committed revision is rerun. The 5G stack was still running at capture time; it was left running to preserve the user's live frontend state.

Raw logs remain in the ignored local `runs/` directory because they include subscriber and network identifiers. This package contains sanitized validator outputs only.
