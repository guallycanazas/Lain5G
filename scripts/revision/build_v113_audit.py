#!/usr/bin/env python3
"""Derive a publication-safe audit from downloaded original GitHub evidence.

Usage: python scripts/revision/build_v113_audit.py INPUT_DIRECTORY > audit.json
Inputs: jobs.json, workflow-history.json, artifacts-32087329776.json,
        original-artifacts/<artifact-name>/{environment.txt,runs/*/validation.json}
Only allowlisted fields are emitted; original files are never modified.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

SOURCE = "8da4d92e4aacec8660ddd3a5be5c4c0167671de5"
RUN = 32087329776


def main() -> None:
    root = Path(sys.argv[1])
    load = lambda name: json.loads((root / name).read_text())
    jobs = load("jobs.json")["jobs"]
    artifacts = load("artifacts-32087329776.json")["artifacts"]
    rows = []
    for job in jobs:
        repetition = int(re.search(r"\((\d)/5\)", job["name"])[1])
        artifact = next(a for a in artifacts if a["name"].endswith(f"-{repetition}"))
        folder = root / "original-artifacts" / artifact["name"]
        assert f"git_commit={SOURCE}" in (folder / "environment.txt").read_text()
        validations = [json.loads(p.read_text()) for p in folder.glob("runs/*/validation.json")]
        assert len(validations) == 2 and job["conclusion"] == "success"
        for scenario, label, expected in (("4g-lte-sim", "4G LTE", 14), ("5g-sa", "5G SA", 15)):
            step = next(s for s in job["steps"] if s["name"] == f"Reproduce {label} software profile")
            validation = next(v for v in validations if v["scenario"] == scenario)
            assert step["conclusion"] == "success"
            if "status" in validation:
                assert validation["status"] == "PASS"
            assert len(validation["checks"]) == expected
            assert all(c["status"] == "PASS" for c in validation["checks"])
            seconds = int((datetime.fromisoformat(step["completed_at"]) - datetime.fromisoformat(step["started_at"])).total_seconds())
            rows.append({"repetition": repetition, "scenario": scenario, "job_id": job["id"],
                         "step_started_at": step["started_at"], "step_completed_at": step["completed_at"],
                         "step_seconds": seconds, "checks_passed": expected, "checks_total": expected,
                         "checks": [{"id": c["id"], "status": c["status"]} for c in validation["checks"]],
                         "artifact_id": artifact["id"], "artifact_digest": artifact["digest"]})
    assert len(rows) == 10
    inputs = [root / n for n in ("jobs.json", "workflow-history.json", "artifacts-32087329776.json")]
    inputs += sorted((root / "original-artifacts").rglob("*"))
    payload = {"audit_date": "2026-10-14", "source_commit": SOURCE, "workflow_run": RUN,
               "workflow_commit": "8f535205a12c5a270b3382710647bef8c290af86",
               "run_attempt": 1, "classification": "SIMULATION_ONLY",
               "timing_boundary": "GitHub reproduction step, including setup, start, validation and EXIT-trap stop; excluding prior install and image pulls",
               "rows": sorted(rows, key=lambda r: (r["repetition"], r["scenario"])),
               "workflow_history": [{k: r[k] for k in ("id", "run_number", "run_attempt", "conclusion", "created_at")}
                                    for r in load("workflow-history.json")["workflow_runs"]],
               "input_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in inputs if p.is_file()},
               "limitations": ["CPU model, RAM and NIC inventory not captured in the original artifact environment files",
                               "No physical RF, voice media, latency benchmark or manual-deployment comparison",
                               "100% is conditional on the selected workflow run; earlier workflow attempts exist"]}
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
