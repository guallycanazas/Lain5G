from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RESULTS_SCRIPTS = ROOT / "scripts" / "results"
if str(RESULTS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RESULTS_SCRIPTS))

from public_result import (  # noqa: E402
    PublicResultError,
    export_public_result,
    normalized_json,
    validate_public_result,
)


CONFIG_REFERENCE = "config/profiles/4g-lte-sim.yaml"
ENVIRONMENT_REFERENCE = "results/public/environment/verification-host-20260723.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_result() -> dict:
    environment = json.loads((ROOT / ENVIRONMENT_REFERENCE).read_text(encoding="utf-8"))
    return {
        "artifact_type": "public-scenario-result",
        "schema_version": "1.0",
        "run_id": "synthetic-positive",
        "started_at_utc": "2026-01-01T00:00:00Z",
        "ended_at_utc": "2026-01-01T00:00:05Z",
        "source_commit": environment["source_commit"],
        "release_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "scenario": "4g-lte-sim",
        "command_label": "Synthetic simulation validation",
        "public_configurations": [
            {
                "reference": CONFIG_REFERENCE,
                "sha256": _sha256(ROOT / CONFIG_REFERENCE),
            }
        ],
        "environment_reference": ENVIRONMENT_REFERENCE,
        "success_criteria": [
            {
                "id": "synthetic-criterion",
                "description": "Synthetic schema criterion",
                "outcome": "MET",
                "evidence_references": [],
            }
        ],
        "result_classification": "SIMULATION_ONLY",
        "execution_status": "PASS",
        "duration_seconds": 5,
        "limitations": ["Synthetic test fixture only; this is not a recorded scenario result."],
        "associated_files": [],
    }


def test_synthetic_safe_summary_exports_deterministic_json(tmp_path: Path):
    public_root = tmp_path / "results" / "public"
    scenario_dir = public_root / "4g-lte-sim"
    scenario_dir.mkdir(parents=True)
    value = _synthetic_result()

    first = export_public_result(value, root=ROOT, public_root=public_root)
    second = export_public_result(deepcopy(value), root=ROOT, public_root=public_root)

    assert first == scenario_dir / "synthetic-positive.json"
    assert second == first
    assert first.read_bytes() == normalized_json(value)
    assert json.loads(first.read_text(encoding="ascii")) == value


@pytest.mark.parametrize(
    "unsafe_value",
    [
        "password=synthetic-credential",
        "Bearer synthetic-credential-value",
        "IMSI: 001010000000001",
        "10.23.0.7",
        "127.0.0.1",
        "169.254.10.1",
        "fe80::1",
        "center_frequency=3500MHz",
        "EARFCN 123",
        "serial=ABC12345",
        "/home/synthetic/result.json",
        "../runs/synthetic-result.json",
        "SIP/2.0 200 synthetic-payload",
        "2026-01-01T00:00:00Z INFO synthetic raw log line",
    ],
)
def test_synthetic_unsafe_values_are_rejected_without_echo(unsafe_value: str):
    value = _synthetic_result()
    value["limitations"] = [unsafe_value]

    with pytest.raises(PublicResultError) as caught:
        validate_public_result(value, root=ROOT)

    assert unsafe_value not in str(caught.value)


@pytest.mark.parametrize(
    ("unsafe_field", "unsafe_value"),
    [
        ("password", "synthetic-credential"),
        ("subscriber_imsi", "synthetic-identifier"),
        ("subscriberImsi", "synthetic-identifier"),
        ("tx_gain", 1),
        ("txGain", 1),
        ("hardware_serial", "SYNTHETIC123"),
        ("serialNumber", "SYNTHETIC123"),
        ("stdout", "synthetic output"),
        ("protocol_payload", "synthetic payload"),
    ],
)
def test_synthetic_unsafe_field_names_are_rejected_without_echo(unsafe_field: str, unsafe_value: object):
    value = _synthetic_result()
    value[unsafe_field] = unsafe_value

    with pytest.raises(PublicResultError) as caught:
        validate_public_result(value, root=ROOT)

    assert unsafe_field not in str(caught.value)
    assert str(unsafe_value) not in str(caught.value)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("source_commit", "a" * 39),
        ("result_classification", "PASSED"),
        ("execution_status", "VALIDATED"),
        ("command_label", "validate; printenv"),
        ("command_label", "Synthetic label "),
    ],
)
def test_synthetic_contract_rejects_invalid_provenance_and_status_fields(field: str, invalid_value: str):
    value = _synthetic_result()
    value[field] = invalid_value

    with pytest.raises(PublicResultError) as caught:
        validate_public_result(value, root=ROOT)

    assert invalid_value not in str(caught.value)


def test_exporter_cli_does_not_echo_rejected_input(tmp_path: Path):
    unsafe_value = "token=synthetic-cli-credential"
    value = _synthetic_result()
    value["limitations"] = [unsafe_value]
    input_path = tmp_path / "unsafe-summary.json"
    input_path.write_text(json.dumps(value), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(RESULTS_SCRIPTS / "export-public-result.py"), str(input_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert unsafe_value not in result.stdout
    assert unsafe_value not in result.stderr


def test_repository_public_results_verifier_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify" / "public_results.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "4 scenario result(s)" in result.stdout
    assert "1 environment summary(s)" in result.stdout
    assert "4 support artifact(s)" in result.stdout
