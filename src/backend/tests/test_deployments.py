import os
import subprocess
from pathlib import Path

import pytest
import yaml

from backend.app.models.deployment import CommandResult, ContainerStatus, DeploymentStatus
from backend.app.services.deployment_registry import get_deployment_definition
from backend.app.services.deployment_service import DeploymentConflictError


def test_public_catalog_contains_simulation_and_guarded_rf_scenarios(client):
    response = client.get("/api/deployments")

    assert response.status_code == 200
    payload = response.json()
    ids = {item["id"] for item in payload}
    assert ids == {"5g-sa", "4g-lte-sim", "4g-volte-sim", "5g-vonr-sim", "4g-lte-x310", "5g-sa-x310", "5g-nsa-x310"}
    assert all(item["status"] == "dry_run" for item in payload)


def test_get_deployment_detail(client):
    response = client.get("/api/deployments/5g-sa")

    assert response.status_code == 200
    assert response.json()["supported_actions"] == ["start", "stop", "restart", "status", "logs", "validate"]
    assert response.json()["rf_capable"] is False


def test_voice_signaling_simulations_are_available_in_the_catalog(client):
    catalog = {item["id"] for item in client.get("/api/deployments").json()}

    assert {"4g-volte-sim", "5g-vonr-sim"}.issubset(catalog)
    assert client.get("/api/deployments/4g-volte-sim").status_code == 200
    assert client.get("/api/deployments/5g-vonr-sim").status_code == 200
    assert "virtual_call" in client.get("/api/deployments/5g-vonr-sim").json()["validation_checks"]


def test_logs_fall_back_to_example_env_when_local_secrets_file_is_absent(deployment_service, project_root):
    vonr_path = project_root / "deployments/5g-vonr"
    vonr_path.mkdir(parents=True)
    (vonr_path / ".env.example").write_text("IMS_DOMAIN=example.invalid\n", encoding="utf-8")

    volte_common = project_root / "deployments/4g-volte/common"
    volte_common.mkdir(parents=True)
    (volte_common / ".env.example").write_text("IMS_DOMAIN=example.invalid\n", encoding="utf-8")

    assert deployment_service._available_env_file("deployments/5g-vonr", ".env") == ".env.example"
    assert deployment_service._available_env_file("deployments/4g-volte/sim", "../common/.env") == "../common/.env.example"

    (vonr_path / ".env").write_text("IMS_DOMAIN=private.invalid\n", encoding="utf-8")
    assert deployment_service._available_env_file("deployments/5g-vonr", ".env") == ".env"


def test_5g_sa_ue_renders_private_credentials_at_runtime():
    compose = (Path(__file__).resolve().parents[3] / "deployments/5g-sa/docker-compose.runtime.yml").read_text(encoding="utf-8")
    ue = (Path(__file__).resolve().parents[3] / "deployments/5g-sa/ueransim/ue.yaml").read_text(encoding="utf-8")
    start = (Path(__file__).resolve().parents[3] / "deployments/5g-sa/scripts/start.sh").read_text(encoding="utf-8")

    assert "env_file:\n      - .env" in compose
    assert "umask 077" in compose
    assert 'value="$${!name:-}"' in compose
    for variable in ("SUBSCRIBER_IMSI", "SUBSCRIBER_KEY", "SUBSCRIBER_OPC", "SUBSCRIBER_AMF", "SUBSCRIBER_SQN"):
        assert f"__{variable}__" in ue
        assert variable in compose
    assert "00000000000000000000000000000000" not in ue
    assert 'deployments/5g-sa-x310/scripts/ensure-core-network.sh' in start
    assert "docker compose --env-file .env -f docker-compose.yml rm -f" in start
    assert start.index('if [ "${LAIN5G_DRY_RUN:-false}" != "true" ]') < start.index("ensure-core-network.sh")


def test_5g_sa_runtime_renderer_matches_provisioned_credentials(tmp_path: Path):
    root = Path(__file__).resolve().parents[3]
    runtime = yaml.safe_load((root / "deployments/5g-sa/docker-compose.runtime.yml").read_text(encoding="utf-8"))
    command = runtime["services"]["ue"]["command"][2].replace("$$", "$")
    runtime_dir = tmp_path / "ueransim"
    rendered_path = runtime_dir / "ue.yaml"
    command = command.replace("/tmp/ueransim", str(runtime_dir))
    command = command.replace("/etc/ueransim/ue.yaml", str(root / "deployments/5g-sa/ueransim/ue.yaml"))
    command = command.replace(f"exec nr-ue -c {rendered_path}", "true")
    credentials = {
        "SUBSCRIBER_IMSI": "001010000000001",
        "SUBSCRIBER_KEY": "00112233445566778899AABBCCDDEEFF",
        "SUBSCRIBER_OPC": "FFEEDDCCBBAA99887766554433221100",
        "SUBSCRIBER_AMF": "8000",
        "SUBSCRIBER_SQN": "000000000001",
    }

    result = subprocess.run(["bash", "-c", command], env={**os.environ, **credentials}, text=True, capture_output=True, check=False)

    assert result.returncode == 0, result.stderr
    rendered = yaml.safe_load(rendered_path.read_text(encoding="utf-8"))
    assert rendered["supi"] == f"imsi-{credentials['SUBSCRIBER_IMSI']}"
    assert rendered["key"] == credentials["SUBSCRIBER_KEY"]
    assert rendered["op"] == credentials["SUBSCRIBER_OPC"]
    assert rendered["amf"] == credentials["SUBSCRIBER_AMF"]
    assert rendered["sqn"] == credentials["SUBSCRIBER_SQN"]
    assert rendered_path.stat().st_mode & 0o777 == 0o600


def test_x310_is_rf_controlled(client):
    response = client.get("/api/deployments/4g-lte-x310")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "rf-controlled"
    assert payload["rf_capable"] is True
    assert "start" not in payload["supported_actions"]
    assert "start-rf" in payload["supported_actions"]
    assert "emergency-stop" in payload["supported_actions"]


def test_public_x310_profiles_require_compact_ims_services(client):
    for scenario in ("4g-lte-x310", "5g-sa-x310", "5g-nsa-x310"):
        payload = client.get(f"/api/deployments/{scenario}").json()
        assert {"ims-database", "pcscf", "icscf", "scscf", "dns"}.issubset(payload["components"])
        assert "ims_services" in payload["validation_checks"]
        assert "virtual_call" in payload["validation_checks"]


def test_rf_core_start_prepares_private_ims_environment(deployment_service, monkeypatch):
    events = []

    class Preparation:
        def ensure_ready(self, profile: str, core_only: bool = False):
            events.append(("components", profile, core_only))

        def prepare_environment(self, profile: str):
            events.append(("environment", profile))

    deployment_service.settings.dry_run = False
    deployment_service.preparation_service = Preparation()
    monkeypatch.setattr(deployment_service, "_ensure_no_conflict", lambda definition: events.append(("conflicts", definition.id)))
    monkeypatch.setattr(deployment_service, "_script_action", lambda definition, *args, **kwargs: events.append(("start", definition.id)))

    deployment_service.start_core("5g-sa-x310")

    assert events == [
        ("components", "5g-sa-x310", True),
        ("environment", "5g-sa-x310"),
        ("conflicts", "5g-sa-x310"),
        ("start", "5g-sa-x310"),
    ]


def test_lab_validated_nsa_is_public_but_stays_rf_guarded(client):
    catalog = client.get("/api/deployments").json()
    assert "5g-nsa-x310" in {item["id"] for item in catalog}
    response = client.get("/api/deployments/5g-nsa-x310")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rf_capable"] is True
    assert "start-rf" in payload["supported_actions"]
    assert "validate" in payload["supported_actions"]
    assert "start" not in payload["supported_actions"]
    assert "enb-nsa-x310" in payload["conditional_components"]


def test_unknown_deployment_returns_404(client):
    response = client.get("/api/deployments/unknown")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DEPLOYMENT_NOT_FOUND"


def test_start_dry_run_does_not_execute_script(client):
    response = client.post("/api/deployments/5g-sa/start")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "dry_run"
    assert payload["command"]["dry_run"] is True
    assert payload["command"]["stdout"].startswith("DRY RUN:")


def test_stop_dry_run_does_not_execute_script(client):
    response = client.post("/api/deployments/4g-lte-sim/stop")

    assert response.status_code == 200
    assert response.json()["command"]["dry_run"] is True


def test_restart_dry_run_does_not_execute_script(client):
    response = client.post("/api/deployments/5g-sa/restart")

    assert response.status_code == 200
    assert response.json()["command"]["dry_run"] is True


def test_software_start_prepares_selected_environment(deployment_service, monkeypatch):
    events = []

    class Preparation:
        def ensure_ready(self, profile: str, core_only: bool = False):
            events.append(("components", profile, core_only))

        def prepare_environment(self, profile: str):
            events.append(("environment", profile))

    deployment_service.settings.dry_run = False
    deployment_service.preparation_service = Preparation()
    monkeypatch.setattr(deployment_service, "_ensure_no_conflict", lambda definition: events.append(("conflicts", definition.id)))
    monkeypatch.setattr(deployment_service, "_script_action", lambda definition, *args: events.append(("start", definition.id)))

    deployment_service.start("4g-volte-sim")

    assert events == [
        ("components", "4g-volte-sim", False),
        ("environment", "4g-volte-sim"),
        ("conflicts", "4g-volte-sim"),
        ("start", "4g-volte-sim"),
    ]


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
    for scenario in ["4g-lte-x310", "5g-sa-x310"]:
        response = client.post(f"/api/deployments/{scenario}/start-rf", json={})
        assert response.status_code == 200
        assert response.json()["status"] == "dry_run"
        assert response.json()["command"]["dry_run"] is True


def test_guarded_rf_dry_run_plan_omits_operator_and_rf_values(client):
    canary = "SYNTHETIC_PRIVATE_OPERATOR_NOTE"
    for scenario in ["4g-lte-x310", "5g-sa-x310"]:
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
    for scenario in ["4g-lte-x310", "5g-sa-x310"]:
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


def test_shared_lte_core_does_not_make_nsa_x310_a_conflict(deployment_service, monkeypatch):
    command = CommandResult(
        command=["status"], cwd=".", exit_code=0, stdout="", stderr="",
        started_at="2026-01-01T00:00:00Z", finished_at="2026-01-01T00:00:00Z", duration_ms=0,
    )

    def fake_status(scenario: str):
        containers = []
        if scenario == "5g-nsa-x310":
            containers = [ContainerStatus(name=f"shared-{service}", service=service, status="running", running=True)
                          for service in ("mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "pcrf")]
        state = "partial" if containers else "stopped"
        return DeploymentStatus(id=scenario, status=state, containers=containers, checked_at="2026-01-01T00:00:00Z", command=command, output="")

    deployment_service.settings.dry_run = False
    monkeypatch.setattr(deployment_service, "get_status", fake_status)

    deployment_service._ensure_no_conflict(get_deployment_definition("4g-lte-x310"))


def test_nsa_status_is_partial_when_shared_core_runs_but_guarded_ran_is_standby(deployment_service, monkeypatch):
    command = CommandResult(
        command=["status"], cwd=".", exit_code=0, stdout="", stderr="",
        started_at="2026-01-01T00:00:00Z", finished_at="2026-01-01T00:00:00Z", duration_ms=0,
    )
    services = ("mongo", "mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "ims-database", "pcscf", "icscf", "scscf", "dns")
    output = "\n".join(f"lain5g-lab-4g-lte-x310-{service} Up 1 minute" for service in services)
    command = command.model_copy(update={"stdout": output})
    monkeypatch.setattr(deployment_service, "_execute_script", lambda *args: command)

    status = deployment_service.get_status("5g-nsa-x310")

    assert status.status == "partial"
    assert all(container.running for container in status.containers)
    assert not any(container.service == "enb-nsa-x310" for container in status.containers)


def test_4g_core_does_not_block_5g_sa_x310_core_start(deployment_service, monkeypatch):
    command = CommandResult(
        command=["status"], cwd=".", exit_code=0, stdout="", stderr="",
        started_at="2026-01-01T00:00:00Z", finished_at="2026-01-01T00:00:00Z", duration_ms=0,
    )

    def fake_status(scenario: str):
        containers = []
        if scenario == "4g-lte-x310":
            containers = [ContainerStatus(name=f"4g-{service}", service=service, status="running", running=True)
                          for service in ("mme", "hss", "ims-database")]
        state = "partial" if containers else "stopped"
        return DeploymentStatus(id=scenario, status=state, containers=containers, checked_at="2026-01-01T00:00:00Z", command=command, output="")

    deployment_service.settings.dry_run = False
    monkeypatch.setattr(deployment_service, "get_status", fake_status)

    deployment_service._ensure_no_conflict(get_deployment_definition("5g-sa-x310"))


def test_nsa_view_of_shared_4g_core_does_not_block_5g_sa_x310(deployment_service, monkeypatch):
    command = CommandResult(
        command=["status"], cwd=".", exit_code=0, stdout="", stderr="",
        started_at="2026-01-01T00:00:00Z", finished_at="2026-01-01T00:00:00Z", duration_ms=0,
    )

    def fake_status(scenario: str):
        containers = []
        if scenario == "5g-nsa-x310":
            containers = [ContainerStatus(name=f"shared-{service}", service=service, status="running", running=True)
                          for service in ("mme", "hss", "sgwc", "sgwu", "pgwc", "pgwu", "pcrf")]
        state = "partial" if containers else "stopped"
        return DeploymentStatus(id=scenario, status=state, containers=containers, checked_at="2026-01-01T00:00:00Z", command=command, output="")

    deployment_service.settings.dry_run = False
    monkeypatch.setattr(deployment_service, "get_status", fake_status)

    deployment_service._ensure_no_conflict(get_deployment_definition("5g-sa-x310"))


def test_5g_sa_gnb_blocks_simultaneous_4g_x310_rf(deployment_service, monkeypatch):
    command = CommandResult(
        command=["status"], cwd=".", exit_code=0, stdout="", stderr="",
        started_at="2026-01-01T00:00:00Z", finished_at="2026-01-01T00:00:00Z", duration_ms=0,
    )

    def fake_status(scenario: str):
        containers = []
        if scenario == "5g-sa-x310":
            containers = [ContainerStatus(name="5g-amf", service="amf", status="running", running=True),
                          ContainerStatus(name="5g-gnb", service="gnb-x310", status="running", running=True)]
        state = "partial" if containers else "stopped"
        return DeploymentStatus(id=scenario, status=state, containers=containers, checked_at="2026-01-01T00:00:00Z", command=command, output="")

    deployment_service.settings.dry_run = False
    monkeypatch.setattr(deployment_service, "get_status", fake_status)

    with pytest.raises(DeploymentConflictError) as exc_info:
        deployment_service._ensure_no_conflict(get_deployment_definition("4g-lte-x310"))

    assert exc_info.value.active_scenario == "5g-sa-x310"


def test_shared_core_still_blocks_when_other_x310_ran_is_active(deployment_service, monkeypatch):
    command = CommandResult(
        command=["status"], cwd=".", exit_code=0, stdout="", stderr="",
        started_at="2026-01-01T00:00:00Z", finished_at="2026-01-01T00:00:00Z", duration_ms=0,
    )

    def fake_status(scenario: str):
        containers = []
        if scenario == "5g-nsa-x310":
            containers = [ContainerStatus(name="shared-mme", service="mme", status="running", running=True),
                          ContainerStatus(name="nsa-enb", service="enb-nsa-x310", status="running", running=True)]
        state = "partial" if containers else "stopped"
        return DeploymentStatus(id=scenario, status=state, containers=containers, checked_at="2026-01-01T00:00:00Z", command=command, output="")

    deployment_service.settings.dry_run = False
    monkeypatch.setattr(deployment_service, "get_status", fake_status)

    with pytest.raises(DeploymentConflictError) as exc_info:
        deployment_service._ensure_no_conflict(get_deployment_definition("4g-lte-x310"))

    assert exc_info.value.active_scenario == "5g-nsa-x310"


def test_failed_validation_returns_new_failure_evidence(deployment_service, run_service, monkeypatch):
    result = CommandResult(
        command=["validate"], cwd=".", exit_code=1, stdout="status=FAIL", stderr="",
        started_at="2026-01-01T00:00:00Z", finished_at="2026-01-01T00:00:01Z", duration_ms=1000,
    )
    failed_run = run_service.get_run("run-partial")
    runs = iter([None, failed_run])
    deployment_service.settings.dry_run = False
    monkeypatch.setattr(deployment_service, "_execute_script", lambda *args: result)
    monkeypatch.setattr(run_service, "latest_run", lambda **kwargs: next(runs))

    report = deployment_service.validate("5g-sa")

    assert report.status == "FAIL"
    assert report.validation["nrf"] == "FAIL"
