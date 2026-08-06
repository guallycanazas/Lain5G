from pathlib import Path

from backend.app.services.run_service import RunService
from backend.app.services.validation_service import ValidationService


def test_dry_run_validation_returns_not_tested(validation_service):
    report = validation_service.dry_run_report("5g-sa")

    assert report.status == "NOT_TESTED"
    assert set(report.validation.values()) == {"NOT_TESTED"}


def test_validation_report_identifies_pass(validation_service, run_service):
    run = run_service.get_run("run-valid")
    report = validation_service.report_from_run(run)

    assert report.status == "PASS"
    assert report.validation["ping"] == "PASS"


def test_validation_report_does_not_convert_fail_to_pass(validation_service, run_service):
    run = run_service.get_run("run-partial")
    report = validation_service.report_from_run(run)

    assert report.status == "FAIL"
    assert report.validation["nrf"] == "FAIL"


def test_corrupt_optional_validation_json_is_ignored(project_root: Path, dry_settings):
    run_dir = project_root / "runs" / "run-corrupt-validation"
    run_dir.mkdir()
    (run_dir / "metadata.json").write_text(
        '{"run_id":"run-corrupt-validation","scenario":"5g-sa","started_at":"2026-07-11T00:00:00Z"}',
        encoding="utf-8",
    )
    (run_dir / "validation.json").write_text("{", encoding="utf-8")

    service = RunService(dry_settings)
    validation = ValidationService(service)
    report = validation.report_from_run(service.get_run("run-corrupt-validation"))

    assert report.status == "NOT_TESTED"


def test_validation_endpoint_dry_run(client):
    response = client.post("/api/deployments/5g-sa/validate")

    assert response.status_code == 200
    assert response.json()["status"] == "NOT_TESTED"


def test_latest_validation_endpoint(client):
    response = client.get("/api/validation/latest")

    assert response.status_code == 200
    assert response.json()["status"] == "PASS"
