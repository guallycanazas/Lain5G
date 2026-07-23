import pytest

from backend.app.services.run_service import RunSecurityError


def test_list_runs_orders_descending(run_service):
    runs = run_service.list_runs()

    assert [run.run_id for run in runs] == ["run-valid", "run-partial"]


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


def test_get_run_tolerates_missing_metrics(run_service):
    run = run_service.get_run("run-partial")

    assert run is not None
    assert run.metrics is None
    assert run.logs == ["partial.log"]


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
