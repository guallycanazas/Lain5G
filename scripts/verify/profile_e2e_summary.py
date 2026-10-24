#!/usr/bin/env python3
"""Require a profile validation to pass and emit a sanitized summary line."""

from __future__ import annotations

import argparse
import json
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
    try:
        validation = json.loads((metadata_path.parent / "validation.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Validation evidence is unavailable for {args.scenario}") from exc

    checks = validation.get("checks", [])
    if not checks or any(check.get("status") != "PASS" for check in checks):
        failed = [check.get("id", "unknown") for check in checks if check.get("status") != "PASS"]
        raise SystemExit(f"{args.scenario} validation did not pass all checks: {', '.join(failed) or 'no checks'}")

    record = {
        "scenario": args.scenario,
        "iteration": args.iteration,
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
