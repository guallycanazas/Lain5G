import json

import pytest

from backend.app.services.run_service import RunSecurityError


def test_list_runs_orders_descending(run_service):
    runs = run_service.list_runs()

    assert [run.run_id for run in runs] == ["run-valid", "run-partial"]


def test_list_runs_uses_timestamp_in_id_when_started_at_is_missing(run_service, project_root):
    run_dir = project_root / "runs/run-20261024-184854"
    run_dir.mkdir()
    (run_dir / "metadata.json").write_text(
        json.dumps({"run_id": run_dir.name, "scenario": "4g-lte-sim", "status": "stopped"}),
        encoding="utf-8",
    )
    (run_dir / "validation.json").write_text(
        json.dumps({"checks": [{"id": "ue_registration", "status": "PASS"}]}),
        encoding="utf-8",
    )

    runs = run_service.list_runs()

    assert runs[0].run_id == "run-20261024-184854"


def test_list_runs_filters(run_service):
    runs = run_service.list_runs(limit=1, scenario="5g-sa", status="PASS")

    assert len(runs) == 1
    assert runs[0].run_id == "run-valid"
    assert runs[0].status == "PASS"


def test_get_run_reads_metadata_validation_metrics_and_logs(run_service):
    run = run_service.get_run("run-valid")

    assert run is not None
    assert run.metadata["run_id"] == "run-valid"
    assert run.validation["checks"][0]["status"] == "PASS"
    assert run.metrics["metrics"] == []
    assert run.logs == ["docker-compose.log"]


def test_get_run_reads_preflight_evidence(run_service, project_root):
    preflight = {
        "scenario": "4g-lte-x310",
        "status": "FAIL",
        "checked_at": "2026-10-22T22:46:46Z",
        "checks": [{"id": "authorization", "status": "FAIL", "detail": "authorization not confirmed"}],
    }
    (project_root / "runs/run-valid/preflight.json").write_text(json.dumps(preflight), encoding="utf-8")

    run = run_service.get_run("run-valid")

    assert run is not None
    assert run.preflight == preflight


def test_get_run_tolerates_missing_metrics(run_service):
    run = run_service.get_run("run-partial")

    assert run is not None
    assert run.metrics is None
    assert run.logs == ["partial.log"]


def test_run_status_is_derived_from_checks(run_service, project_root):
    validation_path = project_root / "runs/run-valid/validation.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    validation["status"] = "PASS"
    validation["checks"][0]["status"] = "WARNING"
    validation_path.write_text(json.dumps(validation), encoding="utf-8")

    listed = run_service.list_runs(scenario="5g-sa")
    detail = run_service.get_run("run-valid")

    assert listed[0].status == "WARNING"
    assert detail is not None
    assert detail.validation["status"] == "WARNING"

    validation["checks"][0]["status"] = "NOT_TESTED"
    validation["checks"].append({"id": "ue_registration", "status": "NOT_TESTED"})
    validation_path.write_text(json.dumps(validation), encoding="utf-8")

    listed = run_service.list_runs(scenario="5g-sa")
    detail = run_service.get_run("run-valid")

    assert listed[0].status == "PARTIAL"
    assert detail is not None
    assert detail.validation["status"] == "PARTIAL"


def test_list_runs_ignores_corrupt_directories(run_service):
    run_ids = {run.run_id for run in run_service.list_runs()}

    assert "run-invalid" not in run_ids


def test_get_run_rejects_path_traversal(run_service):
    with pytest.raises(RunSecurityError):
        run_service.get_run("../outside")


def test_get_run_returns_none_for_missing(run_service):
    assert run_service.get_run("run-missing") is None


def test_runs_api_latest(client):
    response = client.get("/api/runs/latest")


    assert response.status_code == 200
    assert response.json()["run_id"] == "run-valid"


def test_runs_api_get_404(client):
    response = client.get("/api/runs/run-missing")

    assert response.status_code == 404


def test_runs_api_rejects_traversal(client):
    response = client.get("/api/runs/..%2Foutside")
    assert response.status_code in {400, 404}


def test_runs_api_hides_internal_scenario_evidence(client, project_root):
    metadata_path = project_root / "runs/run-valid/metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["scenario"] = "5g-vonr-sim"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    listed = client.get("/api/runs")
    hidden = client.get("/api/runs/run-valid")
    filtered = client.get("/api/runs", params={"scenario": "5g-vonr-sim"})

    assert listed.status_code == 200
    assert "run-valid" not in {run["run_id"] for run in listed.json()}
    assert hidden.status_code == 404
    assert filtered.json() == []
