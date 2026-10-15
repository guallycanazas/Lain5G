from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
AUDIT_SCRIPT = ROOT / "scripts" / "revision" / "build_v113_audit.py"
SOURCE = "8da4d92e4aacec8660ddd3a5be5c4c0167671de5"


def _write_audit_inputs(root: Path, invalid_case: str) -> None:
    artifact_name = "reproduction-artifact-1"
    artifact_dir = root / "original-artifacts" / artifact_name
    run_dir = artifact_dir / "runs" / "run-1"
    run_dir.mkdir(parents=True)

    validations = []
    for scenario, count in (("4g-lte-sim", 14), ("5g-sa", 15)):
        validations.append(
            {
                "scenario": scenario,
                "status": "FAIL" if invalid_case == "validation-status" and scenario == "4g-lte-sim" else "PASS",
                "checks": [
                    {
                        "id": f"{scenario}-{index}",
                        "status": (
                            "FAIL"
                            if invalid_case == "check-status" and scenario == "4g-lte-sim" and index == 0
                            else "PASS"
                        ),
                    }
                    for index in range(count - (1 if invalid_case == "check-count" and scenario == "4g-lte-sim" else 0))
                ],
            }
        )
    (run_dir / "validation.json").write_text(json.dumps(validations[0]), encoding="utf-8")
    (artifact_dir / "runs" / "run-2").mkdir()
    (artifact_dir / "runs" / "run-2" / "validation.json").write_text(json.dumps(validations[1]), encoding="utf-8")
    (artifact_dir / "environment.txt").write_text(
        f"git_commit={'bad-source' if invalid_case == 'source-commit' else SOURCE}\n",
        encoding="utf-8",
    )

    steps = []
    for label in ("4G LTE", "5G SA"):
        steps.append(
            {
                "name": f"Reproduce {label} software profile",
                "conclusion": "failure" if invalid_case == "step-failure" and label == "4G LTE" else "success",
                "started_at": "2026-08-18T01:00:00+00:00",
                "completed_at": "2026-08-18T01:00:10+00:00",
            }
        )
    job = {
        "id": 95562466135,
        "name": "Clean Ubuntu 24.04 reproduction (1/5)",
        "conclusion": "failure" if invalid_case == "job-failure" else "success",
        "steps": steps,
    }

    (root / "jobs.json").write_text(json.dumps({"jobs": [job]}), encoding="utf-8")
    (root / "artifacts-32087329776.json").write_text(
        json.dumps({"artifacts": [{"name": artifact_name, "id": 1, "digest": "sha256:example"}]}),
        encoding="utf-8",
    )
    (root / "workflow-history.json").write_text(json.dumps({"workflow_runs": []}), encoding="utf-8")


@pytest.mark.parametrize(
    ("invalid_case", "expected_error"),
    [
        ("source-commit", "does not use the expected source commit"),
        ("job-failure", "did not complete successfully"),
        ("step-failure", "4G LTE step did not succeed"),
        ("validation-status", "4G LTE validation did not pass"),
        ("check-status", "4G LTE contains a failing check"),
        ("check-count", "4G LTE validation has an unexpected check count"),
        ("incomplete-run", "must contain ten scenario outcomes"),
    ],
)
def test_audit_rejects_invalid_evidence_even_with_python_optimization(
    tmp_path: Path, invalid_case: str, expected_error: str
) -> None:
    _write_audit_inputs(tmp_path, invalid_case)

    result = subprocess.run(
        [sys.executable, "-O", str(AUDIT_SCRIPT), str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert expected_error in result.stderr
    assert result.stdout == ""
