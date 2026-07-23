from backend.app.models.deployment import CommandResult, DeploymentStatus


def test_list_deployments_includes_simulation_and_x310_scenarios(client):
    response = client.get("/api/deployments")

    assert response.status_code == 200
    payload = response.json()
    ids = {item["id"] for item in payload}
    assert ids == {"5g-sa", "4g-lte-sim", "4g-lte-x310", "5g-sa-x310"}
    assert all(item["status"] == "dry_run" for item in payload)


def test_get_deployment_detail(client):
    response = client.get("/api/deployments/5g-vonr-sim")

    assert response.status_code == 200
    assert response.json()["supported_actions"] == ["start", "stop", "restart", "status", "logs", "validate"]
    assert response.json()["rf_capable"] is False


def test_x310_is_rf_controlled(client):
    response = client.get("/api/deployments/4g-lte-x310")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "rf-controlled"
    assert payload["rf_capable"] is True
    assert "start" not in payload["supported_actions"]
    assert "start-rf" in payload["supported_actions"]
    assert "emergency-stop" in payload["supported_actions"]


def test_experimental_nsa_is_hidden_but_guarded(client):
    catalog = client.get("/api/deployments").json()
    assert "5g-nsa-x310" not in {item["id"] for item in catalog}
    response = client.get("/api/deployments/5g-nsa-x310")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rf_capable"] is True
    assert "start-rf" in payload["supported_actions"]
    assert "emergency-stop" in payload["supported_actions"]


def test_unknown_deployment_returns_404(client):
    response = client.get("/api/deployments/unknown")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DEPLOYMENT_NOT_FOUND"


def test_start_dry_run_does_not_execute_script(client):
    response = client.post("/api/deployments/5g-vonr-sim/start")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "dry_run"
    assert payload["command"]["dry_run"] is True
    assert payload["command"]["stdout"].startswith("DRY RUN:")


def test_stop_dry_run_does_not_execute_script(client):
    response = client.post("/api/deployments/4g-volte-sim/stop")

    assert response.status_code == 200
    assert response.json()["command"]["dry_run"] is True


def test_restart_dry_run_does_not_execute_script(client):
    response = client.post("/api/deployments/5g-sa/restart")

    assert response.status_code == 200
    assert response.json()["command"]["dry_run"] is True


def test_status_returns_model(client):
    response = client.get("/api/deployments/5g-sa/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "5g-sa"
    assert payload["status"] == "dry_run"
    assert payload["command"]["exit_code"] == 0


def test_logs_validates_tail_range(client):
    response = client.get("/api/deployments/5g-sa/logs?tail=0")

    assert response.status_code == 422


def test_logs_rejects_unknown_container(client):
    response = client.get("/api/deployments/5g-sa/logs?container=../../bad&tail=100")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "BAD_REQUEST"


def test_blocks_arbitrary_scenario_names(client):
    response = client.post("/api/deployments/../../deployments/5g-sa/start")

    assert response.status_code == 404


def test_x310_specific_endpoints_are_available(client):
    for action in ["hardware-check", "preflight", "start-epc", "emergency-stop"]:
        response = client.post(f"/api/deployments/4g-lte-x310/{action}")
        assert response.status_code == 200
        assert response.json()["command"]["dry_run"] is True


def test_guarded_rf_start_is_dry_run_by_default_for_x310_profiles(client):
    for scenario in ["4g-lte-x310", "5g-sa-x310", "5g-nsa-x310"]:
        response = client.post(f"/api/deployments/{scenario}/start-rf", json={})
        assert response.status_code == 200
        assert response.json()["status"] == "dry_run"
        assert response.json()["command"]["dry_run"] is True


def test_guarded_rf_dry_run_plan_omits_operator_and_rf_values(client):
    canary = "SYNTHETIC_PRIVATE_OPERATOR_NOTE"
    for scenario in ["4g-lte-x310", "5g-sa-x310", "5g-nsa-x310"]:
        response = client.post(
            f"/api/deployments/{scenario}/start-rf",
            json={"operator_note": canary, "requested_duration_seconds": 347},
        )

        assert response.status_code == 200
        command = response.json()["command"]
        rendered = " ".join(command["command"]) + command["stdout"] + command["stderr"]
        assert command["command"][1] == "LAIN5G_DRY_RUN=true"
        assert canary not in rendered
        assert "347" not in rendered
        assert "LAIN5G_RF_OPERATOR_NOTE" not in rendered
        assert "LAIN5G_RF_DURATION_SECONDS" not in rendered


def test_rf_execution_requires_all_acknowledgements(client):
    for scenario in ["4g-lte-x310", "5g-sa-x310", "5g-nsa-x310"]:
        response = client.post(f"/api/deployments/{scenario}/start-rf", json={"execute": True})
        assert response.status_code == 422


def test_x310_normal_start_is_blocked(client):
    response = client.post("/api/deployments/4g-lte-x310/start")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "BAD_REQUEST"


def test_start_conflict_reports_active_scenario(deployment_service, monkeypatch):
    command = CommandResult(
        command=["status"],
        cwd=".",
        exit_code=0,
        stdout="",
        stderr="",
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:00Z",
        duration_ms=0,
    )

    def fake_status(scenario: str):
        state = "running" if scenario == "5g-sa" else "stopped"
        return DeploymentStatus(id=scenario, status=state, containers=[], checked_at="2026-01-01T00:00:00Z", command=command, output="")

    deployment_service.settings.dry_run = False
    monkeypatch.setattr(deployment_service, "get_status", fake_status)

    try:
        deployment_service.start("5g-vonr-sim")
    except Exception as exc:
        assert getattr(exc, "active_scenario", None) == "5g-sa"
    else:
        raise AssertionError("Expected conflict")
