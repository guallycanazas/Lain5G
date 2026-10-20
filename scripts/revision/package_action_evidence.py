#!/usr/bin/env python3
"""Write a sanitized, commit-bound summary for a GitHub Actions simulation run."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--scenario", choices=("4g-lte-sim", "5g-sa"), required=True)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--finished-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = Path("runs") / args.run_id / "validation.json"
    validation = json.loads(source.read_text(encoding="utf-8"))
    metadata = json.loads(source.with_name("metadata.json").read_text(encoding="utf-8"))
    checks = validation.get("checks", [])
    passed = sum(check.get("status") == "PASS" for check in checks)
    status = validation.get("status")
    if status is None and checks and passed == len(checks):
        status = "PASS"
    if status is None and any(check.get("status") == "FAIL" for check in checks):
        status = "FAIL"
    if metadata.get("scenario") != args.scenario or not checks:
        raise SystemExit(f"Unexpected or empty validation record: {source}")
    if status != "PASS" or passed != len(checks):
        raise SystemExit(f"Validation did not pass: {args.scenario} {passed}/{len(checks)}")

    started = datetime.fromisoformat(args.started_at.replace("Z", "+00:00"))
    finished = datetime.fromisoformat(args.finished_at.replace("Z", "+00:00"))
    if finished < started:
        raise SystemExit("Run finish time precedes its start time")
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {
        "scenario": args.scenario,
        "run_id": args.run_id,
        "status": status,
        "checks_passed": passed,
        "checks_total": len(checks),
        "checks": [{"id": check["id"], "status": check["status"]} for check in checks],
    }
    metadata = {
        "run_id": args.run_id,
        "scenario": args.scenario,
        "attempt": args.attempt,
        "source_commit": args.source_sha,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "duration_seconds": int((finished - started).total_seconds()),
        "execution_status": status,
        "evidence_scope": "software-only simulation; no RF hardware",
        "details_redacted": True,
    }
    for name, value in (("validation.json", summary), ("metadata.json", metadata)):
        (args.output / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    files = sorted(path for path in args.output.iterdir() if path.is_file())
    checksum = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in files
    )
    (args.output / "SHA256SUMS.txt").write_text(checksum, encoding="utf-8")
    print(f"PASS: packaged {args.scenario} {args.run_id} ({passed}/{len(checks)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
