#!/usr/bin/env python3
"""Require a profile validation to pass and emit a sanitized summary line."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario")
    parser.add_argument("iteration", type=int)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    matching = []
    for metadata_path in (ROOT / "runs").glob("run-*/metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if metadata.get("scenario") == args.scenario:
            matching.append((str(metadata.get("started_at", "")), metadata_path))
    if not matching:
        raise SystemExit(f"No run record found for {args.scenario}")

    _, metadata_path = max(matching)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    try:
        validation = json.loads((metadata_path.parent / "validation.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Validation evidence is unavailable for {args.scenario}") from exc

    checks = validation.get("checks", [])
    if not checks or any(check.get("status") != "PASS" for check in checks):
        failed = [check.get("id", "unknown") for check in checks if check.get("status") != "PASS"]
        raise SystemExit(f"{args.scenario} validation did not pass all checks: {', '.join(failed) or 'no checks'}")

    started_at = metadata.get("started_at")
    finished_at = metadata.get("finished_at")
    if not started_at or not finished_at:
        raise SystemExit(f"Start/stop timestamps are missing for {args.scenario}")
    elapsed_seconds = (
        datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
        - datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    ).total_seconds()
    if elapsed_seconds < 0:
        raise SystemExit(f"Invalid start/stop timestamps for {args.scenario}")
    source_commit = metadata.get("git_commit") or subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()

    record = {
        "scenario": args.scenario,
        "iteration": args.iteration,
        "release_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "source_commit": source_commit,
        "run_id": metadata.get("run_id"),
        "started_at": started_at,
        "finished_at": finished_at,
        "elapsed_seconds": elapsed_seconds,
        "result": "PASS",
        "passed_checks": len(checks),
        "total_checks": len(checks),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
